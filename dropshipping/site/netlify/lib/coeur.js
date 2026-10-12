/* Logique serveur commune (Netlify Functions et Cloudflare Pages Functions).
   Aucune dépendance npm : appels HTTP directs aux API Stripe et Brevo via fetch.

   Sécurité :
   - les prix, la phase de vente (liste d'attente, précommande, vente), l'état et le stock de
     chaque article sont TOUJOURS relus ici dans /data/products.json (généré depuis brand.json) ;
     le navigateur n'envoie que des identifiants et des quantités ;
   - toutes les fonctions sauf le webhook exigent un en-tête Origin égal à SITE_URL
     (ou à une origine de ORIGINES_AUTORISEES) ;
   - inscription et rétractation : jeton Cloudflare Turnstile (si TURNSTILE_SECRET_KEY est défini),
     3 requêtes par heure et par adresse IP, champs filtrés (aucune URL) ; l'accusé de rétractation
     n'est envoyé au déclarant que si la commande correspond à une session Stripe payée avec le
     même e-mail, sinon il part au seul service client ;
   - les compteurs (limite de débit, webhooks déjà traités) utilisent le stockage KV lié sous le nom
     CANAPOIL_KV (Cloudflare) ; sans lui, un compteur en mémoire par instance sert de repli ;
   - les clés (STRIPE_SECRET_KEY, BREVO_API_KEY, TURNSTILE_SECRET_KEY) viennent des variables
     d'environnement de l'hébergeur, jamais du code. */
"use strict";

const STRIPE_SESSIONS = "https://api.stripe.com/v1/checkout/sessions";
const TURNSTILE = "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const LIMITES = { retractation: 3, inscription: 3, checkout: 20 }; // requêtes par heure et par adresse IP
const URL_RE = /(https?:|www\.|:\/\/|@|[a-z0-9-]+\.(?:com|net|org|fr|io|co|ru|xyz|info|biz|link|top|site|online|app|me|ly|gl|cc|tk|cn|de|uk|eu|shop|store)\b)/i;
const BREVO = "https://api.brevo.com/v3";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const JOUR = 864e5;

class ErreurClient extends Error {
  constructor(message, statut) { super(message); this.statut = statut || 400; }
}

const rep = (statut, corps) => ({ statut, corps });

/* ------------------------------------------------------------ catalogue */
let cache = { cat: null, date: 0 };
async function chargerCatalogue(ctx) {
  if (cache.cat && Date.now() - cache.date < 60000) return cache.cat;
  let cat;
  if (ctx.chargeur) cat = await ctx.chargeur();
  else {
    const base = siteUrl(ctx);
    const r = await fetch(base + "/data/products.json", { headers: { Accept: "application/json" } });
    if (!r.ok) throw new Error("Catalogue indisponible (" + r.status + ")");
    cat = await r.json();
  }
  if (!cat || !Array.isArray(cat.produits) || !Array.isArray(cat.kits)) throw new Error("Catalogue invalide");
  cache = { cat, date: Date.now() };
  return cat;
}

function siteUrl(ctx) {
  return String(ctx.env.SITE_URL || ctx.env.URL || ctx.hote || "").replace(/\/+$/, "");
}

/* ------------------------------------------------------------ disponibilité (identique au navigateur) */
function dateIso(s) { const [a, m, j] = String(s).split("-").map(Number); return new Date(Date.UTC(a, m - 1, j)); }
function enSaison(it, d) {
  d = d || new Date();
  if (it.disponible_jusqu_au && d.getTime() > dateIso(it.disponible_jusqu_au).getTime() + JOUR) return false;
  if (!it.saison) return true;
  const m = d.getUTCMonth() + 1, s = it.saison;
  return s.debut_mois <= s.fin_mois ? m >= s.debut_mois && m <= s.fin_mois : m >= s.debut_mois || m <= s.fin_mois;
}
function disponible(it, idx) {
  if (it.etat !== "disponible" && it.etat !== "precommande") return false;
  if (!enSaison(it)) return false;
  if (it.type === "kit") return it.composition.every((c) => idx[c.id] && enSaison(idx[c.id]));
  return true;
}
function dateFr(iso) { const [a, m, j] = String(iso || "").split("-"); return j && m && a ? `${j}/${m}/${a}` : ""; }

/* ------------------------------------------------------------ calcul du panier */
function calculerPanier(cat, lignes) {
  const qmax = cat.quantite_max_par_ligne || 10;
  if (!Array.isArray(lignes) || lignes.length === 0) throw new ErreurClient("Votre panier est vide.");
  if (lignes.length > 20) throw new ErreurClient("Panier trop long.");
  const idx = {};
  cat.produits.concat(cat.kits).forEach((x) => { idx[x.id] = x; });
  const fusion = new Map();
  for (const l of lignes) {
    if (!l || typeof l.id !== "string" || !Object.prototype.hasOwnProperty.call(idx, l.id)) throw new ErreurClient("Un article du panier n'existe plus. Videz le panier et recommencez.");
    const q = l.qte;
    if (typeof q !== "number" || !Number.isInteger(q) || q < 1 || q > qmax) throw new ErreurClient("Quantité invalide.");
    fusion.set(l.id, Math.min(qmax, (fusion.get(l.id) || 0) + q));
  }
  const items = [];
  const conso = {};
  let sous = 0, offerteKit = false, precommande = null;
  for (const [id, q] of fusion) {
    const it = idx[id];
    if (!disponible(it, idx)) throw new ErreurClient(`« ${it.nom} » n'est pas disponible actuellement.`, 409);
    if (it.type === "kit") it.composition.forEach((c) => { conso[c.id] = (conso[c.id] || 0) + c.quantite * q; });
    else conso[id] = (conso[id] || 0) + q;
    if (it.etat === "precommande" && it.precommande && (!precommande || it.precommande.livraison_au_plus_tard_le > precommande.livraison_au_plus_tard_le)) precommande = it.precommande;
    const pu = Math.round(Number(it.prix_ttc) * 100);
    if (!Number.isInteger(pu) || pu <= 0) throw new Error("Prix invalide pour " + id);
    sous += pu * q;
    if (it.livraison_offerte) offerteKit = true;
    items.push({ it, q, pu });
  }
  for (const [pid, n] of Object.entries(conso)) {
    const max = Number(idx[pid] && idx[pid].stock_max_commande);
    if (!Number.isInteger(max) || n > max) throw new ErreurClient(`Stock insuffisant pour « ${idx[pid] ? idx[pid].nom : pid} » : ${Number.isInteger(max) ? max : 0} disponible(s) pour cette commande.`, 409);
  }
  const offerte = offerteKit || sous >= Math.round(cat.livraison.seuil_gratuite_ttc * 100);
  const livraison = offerte ? 0 : Math.round(cat.livraison.frais_ttc * 100);
  return { items, sous, livraison, offerte, total: sous + livraison, idx, precommande };
}

/* ------------------------------------------------------------ encodage Stripe */
function encoder(obj, prefixe, out) {
  out = out || [];
  Object.keys(obj).forEach((k) => {
    const v = obj[k];
    if (v === undefined || v === null) return;
    const cle = prefixe ? `${prefixe}[${k}]` : k;
    if (typeof v === "object") encoder(v, cle, out);
    else out.push(encodeURIComponent(cle) + "=" + encodeURIComponent(String(v)));
  });
  return out.join("&");
}

function nettoyer(s, max) {
  return String(s == null ? "" : s).replace(/[\u0000-\u001f\u007f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}

function verifierOrigine(ctx, action) {
  if (action === "webhook") return true; // Stripe n'envoie pas d'en-tête Origin : la signature HMAC fait foi
  const o = ctx.origine;
  if (!o) return false; // curl, script : refusé (correction C5)
  const permis = [siteUrl(ctx)].concat(String(ctx.env.ORIGINES_AUTORISEES || "").split(",")).map((x) => x.trim().replace(/\/+$/, "")).filter(Boolean);
  return permis.includes(o.replace(/\/+$/, ""));
}

function ipClient(ctx) { return String(ctx.ip || "").split(",")[0].trim().slice(0, 64) || "inconnue"; }

const memoire = new Map();
function kv(ctx) { const k = ctx.env && ctx.env.CANAPOIL_KV; return k && typeof k.get === "function" && typeof k.put === "function" ? k : null; }

/* 3 requêtes par heure et par adresse IP (retractation, inscription). La règle de limitation de
   débit de l'offre gratuite de Cloudflare ne compte que sur 10 secondes : le compteur horaire est
   donc tenu ici, dans KV si le stockage est lié, sinon en mémoire (repli moins fiable). */
async function limiter(ctx, action) {
  const max = LIMITES[action];
  if (!max) return true;
  const heure = Math.floor(Date.now() / 36e5);
  const cle = `lim:${action}:${ipClient(ctx)}:${heure}`;
  const stock = kv(ctx);
  if (stock) {
    const n = Number(await stock.get(cle)) || 0;
    if (n >= max) return false;
    await stock.put(cle, String(n + 1), { expirationTtl: 3700 });
    return true;
  }
  if (memoire.size > 5000) for (const k of memoire.keys()) if (!k.endsWith(":" + heure)) memoire.delete(k);
  const n = memoire.get(cle) || 0;
  if (n >= max) return false;
  memoire.set(cle, n + 1);
  return true;
}

let avertiTurnstile = false;
async function verifierTurnstile(ctx, jeton) {
  const secret = ctx.env.TURNSTILE_SECRET_KEY;
  if (!secret) {
    if (!avertiTurnstile) { console.warn("TURNSTILE_SECRET_KEY absente : formulaires protégés seulement par l'origine et la limite de débit"); avertiTurnstile = true; }
    return true;
  }
  if (typeof jeton !== "string" || !jeton || jeton.length > 2048) return false;
  const corps = new URLSearchParams({ secret, response: jeton, remoteip: ipClient(ctx) });
  const r = await fetch(TURNSTILE, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: corps.toString() });
  let d = {};
  try { d = await r.json(); } catch (e) { /* réponse vide */ }
  return d.success === true;
}

async function controlesFormulaire(ctx, action, jeton) {
  if (!(await limiter(ctx, action))) throw new ErreurClient("Trop de demandes depuis cette connexion. Réessayez dans une heure, ou écrivez-nous à l'adresse du service client indiquée en bas de page.", 429);
  if (!(await verifierTurnstile(ctx, jeton))) throw new ErreurClient("La vérification anti-robot a échoué. Rechargez la page et réessayez.", 403);
}

const filtreNom = (s) => nettoyer(s, 120).replace(/[^\p{L}\p{M}' .’-]/gu, "").replace(/\s+/g, " ").trim().slice(0, 60);
const filtreCommande = (s) => nettoyer(s, 80).replace(/[^A-Za-z0-9-]/g, "").slice(0, 40);
function filtreUtm(u) {
  const out = {};
  if (!u || typeof u !== "object") return out;
  ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"].forEach((k) => {
    const v = String(u[k] || "").toLowerCase().replace(/[^a-z0-9_.-]/g, "").slice(0, 50);
    if (v) out[k] = v;
  });
  return out;
}

function lireJSON(texte) {
  if (!texte || texte.length > 20000) throw new ErreurClient("Requête invalide.", texte ? 413 : 400);
  try { return JSON.parse(texte); } catch (e) { throw new ErreurClient("Requête invalide."); }
}

/* ------------------------------------------------------------ 1. session de paiement */
async function checkout(ctx) {
  const env = ctx.env;
  const cle = String(env.STRIPE_SECRET_KEY || "");
  if (!/^(sk|rk)_(test|live)_/.test(cle)) return rep(503, { erreur: "Le paiement en ligne n'est pas encore configuré. Écrivez-nous pour commander." });
  const cat = await chargerCatalogue(ctx);
  const L = cat.livraison;
  // Phase lue dans products.json, jamais dans la requête (corrections M2 et C1).
  if (L.phase === "liste_attente") return rep(503, { erreur: "Les ventes ne sont pas encore ouvertes. Inscrivez-vous sur une fiche produit pour être prévenu." });
  if (!(await limiter(ctx, "checkout"))) throw new ErreurClient("Trop de tentatives de paiement depuis cette connexion. Réessayez dans une heure.", 429);
  const corps = lireJSON(ctx.corpsTexte);
  if (corps.cgv_acceptees !== true) throw new ErreurClient("Vous devez accepter les conditions générales de vente.");
  const p = calculerPanier(cat, corps.lignes);
  const site = siteUrl(ctx);
  const pc = p.precommande;
  const resume = p.items.map(({ it, q }) => `${it.sku} x${q}`).join(", ");
  const meta = Object.assign({
    panier: resume.slice(0, 500),
    point_relais: nettoyer(corps.point_relais, 80) || "plus proche de l'adresse",
    cgv_acceptees_le: new Date().toISOString(),
    cgv_version: nettoyer(cat.cgv_version || corps.cgv_version, 40),
    phase: L.phase,
    precommande: pc ? "oui" : "non",
    precommande_expedition: pc ? pc.expedition_a_partir_du : undefined,
    precommande_livraison_max: pc ? pc.livraison_au_plus_tard_le : undefined,
    total_calcule_centimes: String(p.total),
  }, filtreUtm(corps.utm));
  const phraseDelai = pc
    ? `Précommande : expédition à partir du ${dateFr(pc.expedition_a_partir_du)}, livraison au plus tard le ${dateFr(pc.livraison_au_plus_tard_le)}. `
    : "Expédié depuis la France sous 1 jour ouvré. ";
  const params = {
    mode: "payment",
    locale: "fr",
    success_url: site + "/merci.html?session_id={CHECKOUT_SESSION_ID}",
    cancel_url: site + "/commande/",
    client_reference_id: "web-" + Date.now().toString(36),
    line_items: p.items.map(({ it, q, pu }) => {
      const description = it.type === "kit"
        ? it.composition.map((c) => (c.quantite > 1 ? c.quantite + " × " : "") + p.idx[c.id].nom).join(" + ")
        : it.description_courte;
      const product_data = { name: it.nom + (it.etat === "precommande" ? " (précommande)" : ""), description: nettoyer(description, 300), metadata: { id: it.id, sku: it.sku } };
      if (/^https:\/\//.test(site) && it.image_produit_png) product_data.images = [site + it.image_produit_png];
      return { quantity: q, price_data: { currency: "eur", unit_amount: pu, product_data } };
    }),
    shipping_address_collection: { allowed_countries: L.pays_autorises || ["FR"] },
    shipping_options: [{
      shipping_rate_data: {
        type: "fixed_amount",
        display_name: (p.offerte ? "Point relais Mondial Relay (livraison offerte)" : "Point relais Mondial Relay")
          + (pc ? ` : livraison au plus tard le ${dateFr(pc.livraison_au_plus_tard_le)}` : ""),
        fixed_amount: { amount: p.livraison, currency: "eur" },
        delivery_estimate: pc ? undefined : {
          minimum: { unit: "business_day", value: L.delai_min_jours_ouvres },
          maximum: { unit: "business_day", value: L.delai_max_jours_ouvres },
        },
      },
    }],
    phone_number_collection: { enabled: true },
    billing_address_collection: "auto",
    custom_text: {
      shipping_address: { message: "Livraison en point relais Mondial Relay : sauf numéro de point relais indiqué à l'étape précédente, nous retenons le plus proche de cette adresse et vous l'indiquons par e-mail avant l'expédition." },
      submit: { message: phraseDelai + "En cliquant sur « Payer », vous passez une commande avec obligation de paiement. 30 jours pour changer d'avis après réception." },
    },
    metadata: meta,
    payment_intent_data: { description: "Commande Canapoil : " + resume.slice(0, 400), metadata: meta },
  };
  if (String(env.STRIPE_CASE_CGV || "") === "oui") params.consent_collection = { terms_of_service: "required" };

  const r = await fetch(STRIPE_SESSIONS, {
    method: "POST",
    headers: { Authorization: "Bearer " + cle, "Content-Type": "application/x-www-form-urlencoded" },
    body: encoder(params),
  });
  let data = {};
  try { data = await r.json(); } catch (e) { /* réponse vide */ }
  if (!r.ok || !data.url) {
    console.error("Stripe", r.status, data && data.error ? data.error.message : "");
    return rep(502, { erreur: "Le paiement n'a pas pu être initialisé. Réessayez dans quelques minutes ou écrivez-nous." });
  }
  return rep(200, { url: data.url, id: data.id, total: p.total });
}

/* ------------------------------------------------------------ 2. rétractation en ligne */
function htmlEsc(s) { return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]); }

async function envoyerEmail(env, message) {
  const r = await fetch(BREVO + "/smtp/email", {
    method: "POST",
    headers: { "api-key": env.BREVO_API_KEY, "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(message),
  });
  if (!r.ok) { const t = await r.text().catch(() => ""); throw new Error("Brevo " + r.status + " " + t.slice(0, 200)); }
}

/* La commande existe-t-elle ? Session Stripe payée, même e-mail, numéro = 10 derniers caractères
   de l'identifiant de session (numéro affiché sur merci.html et dans l'e-mail de confirmation). */
async function commandeVerifiee(env, numero, email) {
  const cle = String(env.STRIPE_SECRET_KEY || "");
  if (!/^(sk|rk)_(test|live)_/.test(cle) || numero.length < 6) return false;
  const essais = Array.from(new Set([email, email.toLowerCase()]));
  for (const adresse of essais) {
    const r = await fetch(STRIPE_SESSIONS + "?" + encoder({ limit: 100, status: "complete", customer_details: { email: adresse } }), { headers: { Authorization: "Bearer " + cle } });
    if (!r.ok) { console.error("Stripe liste", r.status); return false; }
    let d = {};
    try { d = await r.json(); } catch (e) { return false; }
    if ((d.data || []).some((s) => s.payment_status === "paid" && String(s.id || "").slice(-10).toUpperCase() === numero)) return true;
  }
  return false;
}

async function retractation(ctx) {
  const env = ctx.env;
  if (!env.BREVO_API_KEY || !env.EMAIL_EXPEDITEUR || !env.EMAIL_SERVICE_CLIENT) {
    return rep(503, { erreur: "L'envoi automatique n'est pas configuré. Envoyez votre déclaration par e-mail à notre service client (adresse en bas de page)." });
  }
  const c = lireJSON(ctx.corpsTexte);
  await controlesFormulaire(ctx, "retractation", c.turnstile);
  if ([c.nom, c.prenom, c.commande].some((x) => URL_RE.test(String(x || "")))) throw new ErreurClient("Les liens et adresses ne sont pas acceptés dans ces champs.");
  if (URL_RE.test(String(c.produits || ""))) throw new ErreurClient("Les liens et adresses ne sont pas acceptés dans le champ « Produits concernés ».");
  const v = {
    nom: filtreNom(c.nom), prenom: filtreNom(c.prenom), commande: filtreCommande(c.commande),
    email: nettoyer(c.email, 200), produits: nettoyer(c.produits, 300).replace(/[<>{}\[\]\\|^~`]/g, ""),
  };
  if (!v.nom || !v.prenom || !v.commande) throw new ErreurClient("Nom, prénom et numéro de commande sont obligatoires (lettres, chiffres et tirets).");
  if (!EMAIL_RE.test(v.email)) throw new ErreurClient("Adresse e-mail invalide.");
  const numero = v.commande.replace(/-/g, "").toUpperCase().slice(-10);
  const verifiee = await commandeVerifiee(env, numero, v.email);
  const maintenant = new Date();
  const horodatage = maintenant.toISOString();
  const reference = "RET-" + maintenant.getTime().toString(36).toUpperCase();
  const quand = new Intl.DateTimeFormat("fr-FR", { dateStyle: "full", timeStyle: "medium", timeZone: "Europe/Paris" }).format(maintenant);
  const lignes = [
    ["Référence", reference], ["Envoyée le", quand + " (heure de Paris)"], ["Nom", v.nom], ["Prénom", v.prenom],
    ["Commande", numero], ["E-mail", v.email], ["Produits concernés", v.produits || "Toute la commande"],
  ];
  const nomMarque = env.NOM_EXPEDITEUR || "Canapoil";
  const tableau = `<table cellpadding="6" style="border-collapse:collapse">${lignes.map(([k, x]) => `<tr><th align="left">${htmlEsc(k)}</th><td>${htmlEsc(x)}</td></tr>`).join("")}</table>`;
  const declaration = "Déclaration : « Je notifie par la présente ma rétractation du contrat portant sur la vente des biens ci-dessus. »";
  const texte = "Accusé de réception de votre rétractation\n\n" + lignes.map(([k, x]) => `${k} : ${x}`).join("\n") + "\n\n" + declaration + "\n";
  if (verifiee) {
    const html = `<p>Bonjour ${htmlEsc(v.prenom)},</p><p>Nous accusons réception de votre déclaration de rétractation, dont voici le contenu :</p>${tableau}`
      + `<p>${htmlEsc(declaration)}</p>`
      + `<p>Renvoyez le ou les produits au plus tard 14 jours après cette déclaration, à l'adresse indiquée sur la page Retours de notre site. Nous vous remboursons au plus tard 14 jours après cette déclaration, frais de livraison initiaux inclus ; nous pouvons attendre la réception du produit ou votre preuve d'envoi.</p>`
      + `<p>${htmlEsc(nomMarque)}</p>`;
    await envoyerEmail(env, {
      sender: { email: env.EMAIL_EXPEDITEUR, name: nomMarque },
      to: [{ email: v.email, name: `${v.prenom} ${v.nom}`.slice(0, 70) }],
      bcc: [{ email: env.EMAIL_SERVICE_CLIENT }],
      replyTo: { email: env.EMAIL_SERVICE_CLIENT, name: nomMarque },
      subject: `Accusé de réception de votre rétractation (commande ${numero})`,
      htmlContent: html,
      textContent: texte,
    });
  } else {
    // Commande non retrouvée : aucun e-mail vers l'adresse saisie (pas de relais d'hameçonnage),
    // copie au service client, qui vérifie et répond sous 48 heures ouvrées.
    await envoyerEmail(env, {
      sender: { email: env.EMAIL_EXPEDITEUR, name: nomMarque },
      to: [{ email: env.EMAIL_SERVICE_CLIENT }],
      subject: `Rétractation à vérifier : commande non retrouvée (${numero})`,
      htmlContent: `<p>Déclaration reçue par la fonctionnalité « renoncer au contrat ici ». La commande n'a pas été retrouvée automatiquement (numéro ou e-mail différent, commande TikTok Shop ou Shopify, clé Stripe absente). Vérifiez puis envoyez l'accusé au client sous 48 heures ouvrées.</p>${tableau}<p>${htmlEsc(declaration)}</p><p>Adresse IP : ${htmlEsc(ipClient(ctx))}</p>`,
      textContent: texte,
    });
  }
  return rep(200, { horodatage, reference, commande_verifiee: verifiee });
}

/* ------------------------------------------------------------ 3. liste d'attente et e-mails (double opt-in) */
async function inscription(ctx) {
  const env = ctx.env;
  if (!env.BREVO_API_KEY || !env.BREVO_LISTE_ID || !env.BREVO_TEMPLATE_DOI) return rep(503, { erreur: "Les inscriptions ne sont pas encore ouvertes." });
  const c = lireJSON(ctx.corpsTexte);
  await controlesFormulaire(ctx, "inscription", c.turnstile);
  const email = nettoyer(c.email, 200);
  if (!EMAIL_RE.test(email)) throw new ErreurClient("Adresse e-mail invalide.");
  if (c.consentement !== true) throw new ErreurClient("Cochez la case de consentement pour vous inscrire.");
  const cat = await chargerCatalogue(ctx);
  const permis = new Set(cat.produits.concat(cat.kits).map((x) => x.id).concat(cat.produits_liste_attente || ["lettre"]));
  const produit = String(c.produit || "lettre");
  if (!permis.has(produit)) throw new ErreurClient("Produit inconnu.");
  const utm = filtreUtm(c.utm);
  const attributs = {
    PRODUIT: produit,
    SOURCE: nettoyer(c.source, 30).replace(/[^a-z0-9-]/gi, "") || "site",
    CONSENTEMENT_DATE: new Date().toISOString(),
    CONSENTEMENT_TEXTE: "liste-attente-2026-10-12 : lancement, tests et nouveautés, 2 e-mails par semaine au plus",
  };
  if (utm.utm_source) attributs.UTM_SOURCE = utm.utm_source;
  if (utm.utm_campaign) attributs.UTM_CAMPAIGN = utm.utm_campaign;
  if (utm.utm_content) attributs.UTM_CONTENT = utm.utm_content;
  const r = await fetch(BREVO + "/contacts/doubleOptinConfirmation", {
    method: "POST",
    headers: { "api-key": env.BREVO_API_KEY, "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      email,
      attributes: attributs,
      includeListIds: [Number(env.BREVO_LISTE_ID)],
      templateId: Number(env.BREVO_TEMPLATE_DOI),
      redirectionUrl: siteUrl(ctx) + "/?inscription=confirmee",
    }),
  });
  if (!r.ok && r.status !== 400) { console.error("Brevo DOI", r.status); return rep(502, { erreur: "Inscription impossible pour le moment. Réessayez plus tard." }); }
  // 400 = contact déjà inscrit le plus souvent (ou attribut absent du compte Brevo, journalisé) :
  // même réponse, pour ne pas révéler qui est inscrit.
  if (r.status === 400) { const t = await (r.text ? r.text() : Promise.resolve("")).catch(() => ""); console.warn("Brevo DOI 400", String(t).slice(0, 200)); }
  return rep(200, { ok: true });
}

/* ------------------------------------------------------------ 4. webhook Stripe : confirmation de commande
   Sur « checkout.session.completed », envoie au client la confirmation sur support durable
   (récapitulatif, délai ou dates de précommande, CGV en PDF jointe, formulaire type, lien
   « renoncer au contrat ici »), avec copie cachée au service client (article L221-13 du Code de la consommation).
   Variables : STRIPE_WEBHOOK_SECRET (whsec_…), BREVO_API_KEY, EMAIL_EXPEDITEUR, EMAIL_SERVICE_CLIENT, SITE_URL. */
function hex(buf) { return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join(""); }
function egaliteConstante(a, b) {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
async function verifierSignatureStripe(brut, entete, secret, tolerance) {
  const parties = String(entete || "").split(",").map((x) => x.split("="));
  const t = (parties.find((p) => p[0] === "t") || [])[1];
  const sigs = parties.filter((p) => p[0] === "v1").map((p) => p[1]);
  if (!t || !sigs.length) return false;
  if (Math.abs(Date.now() / 1000 - Number(t)) > (tolerance || 300)) return false;
  const c = globalThis.crypto; // Web Crypto : Node 20+ (Netlify) et Cloudflare Workers
  if (!c || !c.subtle) throw new Error("Web Crypto indisponible");
  const cle = await c.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const attendu = hex(await c.subtle.sign("HMAC", cle, new TextEncoder().encode(`${t}.${brut}`)));
  return sigs.some((s) => egaliteConstante(s, attendu));
}

function euros(c) { return (c / 100).toFixed(2).replace(".", ",") + " €"; }

/* Phrase de délai de l'e-mail de confirmation : dates de précommande enregistrées dans les
   métadonnées au moment du paiement (correction C1), sinon délai standard du stock en France. */
function phraseLivraison(meta) {
  if (meta.precommande === "oui" && meta.precommande_expedition && meta.precommande_livraison_max) {
    return `<strong>Précommande</strong> : expédition depuis la France à partir du ${htmlEsc(dateFr(meta.precommande_expedition))}, livraison en point relais Mondial Relay au plus tard le ${htmlEsc(dateFr(meta.precommande_livraison_max))}. Si ces dates ne peuvent pas être tenues, nous vous prévenons et vous pouvez annuler votre commande avec un remboursement intégral sous 14 jours. Vous recevrez le numéro de suivi par e-mail.`;
  }
  return "Expédition depuis la France sous 1 jour ouvré, livraison en point relais Mondial Relay 3 à 6 jours ouvrés après la commande. Vous recevrez le numéro de suivi par e-mail.";
}

async function webhook(ctx) {
  const env = ctx.env;
  if (!env.STRIPE_WEBHOOK_SECRET) return rep(503, { erreur: "Webhook non configuré." });
  if (!(await verifierSignatureStripe(ctx.corpsTexte, ctx.signature, env.STRIPE_WEBHOOK_SECRET))) return rep(400, { erreur: "Signature invalide." });
  const evt = lireJSON(ctx.corpsTexte);
  if (evt.type !== "checkout.session.completed") return rep(200, { ignore: evt.type });
  const s = evt.data && evt.data.object;
  if (!s || s.payment_status !== "paid") return rep(200, { ignore: "non payée" });
  if (!env.BREVO_API_KEY || !env.EMAIL_EXPEDITEUR || !env.EMAIL_SERVICE_CLIENT) return rep(503, { erreur: "Envoi d'e-mail non configuré." });
  const stock = kv(ctx);
  if (stock && evt.id && (await stock.get("evt:" + evt.id))) return rep(200, { ignore: "déjà traité" });
  const cat = await chargerCatalogue(ctx);
  const parSku = {};
  cat.produits.concat(cat.kits).forEach((x) => { parSku[x.sku] = x; });
  const meta = s.metadata || {};
  const lignes = String(meta.panier || "").split(",").map((x) => x.trim()).filter(Boolean).map((x) => {
    const [sku, q] = x.split(" x");
    const it = parSku[sku];
    return it ? { nom: it.nom, q: Number(q), pu: Math.round(it.prix_ttc * 100) } : null;
  }).filter(Boolean);
  const client = s.customer_details || {};
  const livr = (s.collected_information && s.collected_information.shipping_details) || s.shipping_details || {};
  const adr = livr.address || {};
  const site = siteUrl(ctx);
  const numero = String(s.id || "").slice(-10).toUpperCase();
  const nomMarque = env.NOM_EXPEDITEUR || "Canapoil";
  const port = (s.total_details && s.total_details.amount_shipping) || 0;
  const tableau = lignes.map((l) => `<tr><td>${htmlEsc(l.nom)}</td><td align="right">${l.q}</td><td align="right">${euros(l.pu * l.q)}</td></tr>`).join("");
  const precommande = meta.precommande === "oui";
  const html = `<p>Bonjour ${htmlEsc(client.name || "")},</p><p>Merci pour votre ${precommande ? "précommande" : "commande"} <strong>${htmlEsc(numero)}</strong>. Votre paiement est confirmé.</p>`
    + `<table cellpadding="6" style="border-collapse:collapse">${tableau}<tr><td>Livraison point relais</td><td></td><td align="right">${port ? euros(port) : "Offerte"}</td></tr><tr><th align="left">Total TTC</th><td></td><th align="right">${euros(s.amount_total || 0)}</th></tr></table>`
    + `<p>Livraison : ${htmlEsc([livr.name, adr.line1, adr.line2, adr.postal_code, adr.city].filter(Boolean).join(", "))}. Point relais demandé : ${htmlEsc(meta.point_relais || "le plus proche de cette adresse")}.</p>`
    + `<p>${phraseLivraison(meta)}</p>`
    + `<p><strong>30 jours pour changer d'avis</strong> après réception (14 jours légaux + 16 jours offerts) : <a href="${site}/retractation/">renoncer au contrat ici</a> (numéro de commande à indiquer : ${htmlEsc(numero)}). Formulaire type de rétractation et conditions : <a href="${site}/retours-retractation/">${site}/retours-retractation/</a>.</p>`
    + `<p>Nos conditions générales de vente acceptées lors de la commande (version ${htmlEsc(meta.cgv_version || "")}) sont jointes en PDF et consultables sur <a href="${site}/cgv/">${site}/cgv/</a>.</p><p>${htmlEsc(nomMarque)}</p>`;
  const message = {
    sender: { email: env.EMAIL_EXPEDITEUR, name: nomMarque },
    to: [{ email: client.email || env.EMAIL_SERVICE_CLIENT }],
    bcc: [{ email: env.EMAIL_SERVICE_CLIENT }],
    replyTo: { email: env.EMAIL_SERVICE_CLIENT, name: nomMarque },
    subject: `Confirmation de votre ${precommande ? "précommande" : "commande"} ${numero}`,
    htmlContent: html,
  };
  if (/^https:\/\//.test(site)) message.attachment = [{ url: site + "/documents/cgv-canapoil.pdf", name: "CGV-Canapoil.pdf" }];
  await envoyerEmail(env, message);
  if (stock && evt.id) await stock.put("evt:" + evt.id, "1", { expirationTtl: 30 * 86400 });
  return rep(200, { envoye: true });
}

/* ------------------------------------------------------------ point d'entrée commun */
const ACTIONS = { checkout, retractation, inscription, webhook };

/* CORS : utile seulement si une autre origine autorisée (par exemple la boutique Shopify,
   déclarée dans ORIGINES_AUTORISEES) appelle la fonction de rétractation. */
function entetesCors(ctx, action) {
  if (!ctx.origine || action === "webhook" || !verifierOrigine(ctx, action)) return {};
  return { "Access-Control-Allow-Origin": ctx.origine, Vary: "Origin", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400" };
}

async function traiter(action, ctx) {
  const cors = entetesCors(ctx, action);
  const avec = (r) => Object.assign(r, { entetes: cors });
  try {
    if (ctx.methode === "OPTIONS") return avec({ statut: 204, corps: null });
    if (ctx.methode && ctx.methode !== "POST") return avec(rep(405, { erreur: "Méthode non autorisée." }));
    if (!verifierOrigine(ctx, action)) return rep(403, { erreur: "Origine non autorisée." });
    return avec(await ACTIONS[action](ctx));
  } catch (e) {
    if (e instanceof ErreurClient) return avec(rep(e.statut, { erreur: e.message }));
    console.error(action, e && e.message);
    return avec(rep(500, { erreur: "Erreur interne. Réessayez ou écrivez-nous." }));
  }
}

const ENTETES = { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const corpsReponse = (res) => (res.corps === null ? "" : JSON.stringify(res.corps));

/* Adaptateur Netlify Functions (format « Lambda », compatible fichiers .js CommonJS). */
function netlify(action) {
  return async (event) => {
    const h = event.headers || {};
    const corpsTexte = event.isBase64Encoded ? Buffer.from(event.body || "", "base64").toString("utf8") : event.body || "";
    const res = await traiter(action, {
      methode: event.httpMethod, origine: h.origin || h.Origin || "", corpsTexte, env: process.env,
      signature: h["stripe-signature"] || h["Stripe-Signature"] || "",
      hote: h.host ? "https://" + h.host : "",
      ip: h["x-nf-client-connection-ip"] || h["x-forwarded-for"] || "",
    });
    return { statusCode: res.statut, headers: Object.assign({}, ENTETES, res.entetes), body: corpsReponse(res) };
  };
}

/* Adaptateur Cloudflare Pages Functions (onRequest). */
function cloudflare(action) {
  return async ({ request, env }) => {
    const url = new URL(request.url);
    const res = await traiter(action, {
      methode: request.method, origine: request.headers.get("Origin") || "", corpsTexte: await request.text(), env,
      signature: request.headers.get("Stripe-Signature") || "",
      hote: url.origin,
      ip: request.headers.get("CF-Connecting-IP") || "",
      chargeur: env.ASSETS ? async () => (await env.ASSETS.fetch(new URL("/data/products.json", url))).json() : null,
    });
    return new Response(res.statut === 204 ? null : corpsReponse(res), { status: res.statut, headers: Object.assign({}, ENTETES, res.entetes) });
  };
}

module.exports = { traiter, netlify, cloudflare, calculerPanier, encoder, disponible, verifierSignatureStripe, phraseLivraison, _ErreurClient: ErreurClient, _memoire: memoire, _viderCache: () => { cache = { cat: null, date: 0 }; } };
