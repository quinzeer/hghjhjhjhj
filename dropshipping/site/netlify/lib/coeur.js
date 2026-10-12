/* Logique serveur commune (Netlify Functions et Cloudflare Pages Functions).
   Aucune dépendance npm : appels HTTP directs aux API Stripe et Brevo via fetch.

   Sécurité :
   - les prix sont TOUJOURS recalculés ici à partir de /data/products.json ;
     le navigateur n'envoie que des identifiants et des quantités ;
   - les clés (STRIPE_SECRET_KEY, BREVO_API_KEY) viennent des variables
     d'environnement de l'hébergeur, jamais du code. */
"use strict";

const STRIPE_SESSIONS = "https://api.stripe.com/v1/checkout/sessions";
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
  if (!enSaison(it)) return false;
  if (it.type === "kit") return it.composition.every((c) => idx[c.id] && enSaison(idx[c.id]));
  return true;
}

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
  let sous = 0, offerteKit = false;
  for (const [id, q] of fusion) {
    const it = idx[id];
    if (!disponible(it, idx)) throw new ErreurClient(`« ${it.nom} » n'est pas disponible actuellement.`);
    const pu = Math.round(Number(it.prix_ttc) * 100);
    if (!Number.isInteger(pu) || pu <= 0) throw new Error("Prix invalide pour " + id);
    sous += pu * q;
    if (it.livraison_offerte) offerteKit = true;
    items.push({ it, q, pu });
  }
  const offerte = offerteKit || sous >= Math.round(cat.livraison.seuil_gratuite_ttc * 100);
  const livraison = offerte ? 0 : Math.round(cat.livraison.frais_ttc * 100);
  return { items, sous, livraison, offerte, total: sous + livraison, idx };
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

function verifierOrigine(ctx) {
  const o = ctx.origine;
  if (!o) return true; // requêtes sans en-tête Origin (outils serveur) : laissées passer, aucun secret n'est renvoyé
  const permis = [siteUrl(ctx)].concat(String(ctx.env.ORIGINES_AUTORISEES || "").split(",")).map((x) => x.trim().replace(/\/+$/, "")).filter(Boolean);
  return permis.includes(o.replace(/\/+$/, ""));
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
  const corps = lireJSON(ctx.corpsTexte);
  if (corps.cgv_acceptees !== true) throw new ErreurClient("Vous devez accepter les conditions générales de vente.");
  const cat = await chargerCatalogue(ctx);
  const p = calculerPanier(cat, corps.lignes);
  const site = siteUrl(ctx);
  const L = cat.livraison;
  const resume = p.items.map(({ it, q }) => `${it.sku} x${q}`).join(", ");
  const meta = {
    panier: resume.slice(0, 500),
    point_relais: nettoyer(corps.point_relais, 80) || "plus proche de l'adresse",
    cgv_acceptees_le: new Date().toISOString(),
    cgv_version: nettoyer(corps.cgv_version, 20),
    phase: nettoyer(corps.phase, 20),
    total_calcule_centimes: String(p.total),
  };
  const precommande = meta.phase === "precommande";
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
      const product_data = { name: it.nom, description: nettoyer(description, 300), metadata: { id: it.id, sku: it.sku } };
      if (/^https:\/\//.test(site) && it.image_produit_png) product_data.images = [site + it.image_produit_png];
      return { quantity: q, price_data: { currency: "eur", unit_amount: pu, product_data } };
    }),
    shipping_address_collection: { allowed_countries: L.pays_autorises || ["FR"] },
    shipping_options: [{
      shipping_rate_data: {
        type: "fixed_amount",
        display_name: p.offerte ? "Point relais Mondial Relay (livraison offerte)" : "Point relais Mondial Relay",
        fixed_amount: { amount: p.livraison, currency: "eur" },
        delivery_estimate: precommande ? undefined : {
          minimum: { unit: "business_day", value: L.delai_min_jours_ouvres },
          maximum: { unit: "business_day", value: L.delai_max_jours_ouvres },
        },
      },
    }],
    phone_number_collection: { enabled: true },
    billing_address_collection: "auto",
    custom_text: {
      shipping_address: { message: "Livraison en point relais Mondial Relay : sauf numéro de point relais indiqué à l'étape précédente, nous retenons le plus proche de cette adresse et vous l'indiquons par e-mail avant l'expédition." },
      submit: { message: (precommande ? "Précommande : la date d'expédition figure sur la fiche produit et dans l'e-mail de confirmation. " : "Expédié depuis la France sous 1 jour ouvré. ") + "En cliquant sur « Payer », vous passez une commande avec obligation de paiement. 30 jours pour changer d'avis après réception." },
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

async function retractation(ctx) {
  const env = ctx.env;
  if (!env.BREVO_API_KEY || !env.EMAIL_EXPEDITEUR || !env.EMAIL_SERVICE_CLIENT) {
    return rep(503, { erreur: "L'envoi automatique n'est pas configuré. Envoyez votre déclaration par e-mail à notre service client (adresse en bas de page)." });
  }
  const c = lireJSON(ctx.corpsTexte);
  const v = {
    nom: nettoyer(c.nom, 100), prenom: nettoyer(c.prenom, 100), commande: nettoyer(c.commande, 60),
    email: nettoyer(c.email, 200), produits: nettoyer(c.produits, 500),
  };
  if (!v.nom || !v.prenom || !v.commande) throw new ErreurClient("Nom, prénom et numéro de commande sont obligatoires.");
  if (!EMAIL_RE.test(v.email)) throw new ErreurClient("Adresse e-mail invalide.");
  const maintenant = new Date();
  const horodatage = maintenant.toISOString();
  const reference = "RET-" + maintenant.getTime().toString(36).toUpperCase();
  const quand = new Intl.DateTimeFormat("fr-FR", { dateStyle: "full", timeStyle: "medium", timeZone: "Europe/Paris" }).format(maintenant);
  const lignes = [
    ["Référence", reference], ["Envoyée le", quand + " (heure de Paris)"], ["Nom", v.nom], ["Prénom", v.prenom],
    ["Commande", v.commande], ["E-mail", v.email], ["Produits concernés", v.produits || "Toute la commande"],
  ];
  const nomMarque = env.NOM_EXPEDITEUR || "Canapoil";
  const html = `<p>Bonjour ${htmlEsc(v.prenom)},</p><p>Nous accusons réception de votre déclaration de rétractation, dont voici le contenu :</p>`
    + `<table cellpadding="6" style="border-collapse:collapse">${lignes.map(([k, x]) => `<tr><th align="left">${htmlEsc(k)}</th><td>${htmlEsc(x)}</td></tr>`).join("")}</table>`
    + `<p>Déclaration : « Je notifie par la présente ma rétractation du contrat portant sur la vente des biens ci-dessus. »</p>`
    + `<p>Renvoyez le ou les produits au plus tard 14 jours après cette déclaration, à l'adresse indiquée sur la page Retours de notre site. Nous vous remboursons au plus tard 14 jours après cette déclaration, frais de livraison initiaux inclus ; nous pouvons attendre la réception du produit ou votre preuve d'envoi.</p>`
    + `<p>${htmlEsc(nomMarque)}</p>`;
  const texte = "Accusé de réception de votre rétractation\n\n" + lignes.map(([k, x]) => `${k} : ${x}`).join("\n")
    + "\n\nDéclaration : « Je notifie par la présente ma rétractation du contrat portant sur la vente des biens ci-dessus. »\n";
  await envoyerEmail(env, {
    sender: { email: env.EMAIL_EXPEDITEUR, name: nomMarque },
    to: [{ email: v.email, name: `${v.prenom} ${v.nom}`.slice(0, 70) }],
    bcc: [{ email: env.EMAIL_SERVICE_CLIENT }],
    replyTo: { email: env.EMAIL_SERVICE_CLIENT, name: nomMarque },
    subject: `Accusé de réception de votre rétractation (commande ${v.commande})`,
    htmlContent: html,
    textContent: texte,
  });
  return rep(200, { horodatage, reference });
}

/* ------------------------------------------------------------ 3. liste d'attente et e-mails (double opt-in) */
async function inscription(ctx) {
  const env = ctx.env;
  if (!env.BREVO_API_KEY || !env.BREVO_LISTE_ID || !env.BREVO_TEMPLATE_DOI) return rep(503, { erreur: "Les inscriptions ne sont pas encore ouvertes." });
  const c = lireJSON(ctx.corpsTexte);
  const email = nettoyer(c.email, 200);
  if (!EMAIL_RE.test(email)) throw new ErreurClient("Adresse e-mail invalide.");
  const r = await fetch(BREVO + "/contacts/doubleOptinConfirmation", {
    method: "POST",
    headers: { "api-key": env.BREVO_API_KEY, "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      email,
      includeListIds: [Number(env.BREVO_LISTE_ID)],
      templateId: Number(env.BREVO_TEMPLATE_DOI),
      redirectionUrl: siteUrl(ctx) + "/?inscription=confirmee",
    }),
  });
  if (!r.ok && r.status !== 400) { console.error("Brevo DOI", r.status); return rep(502, { erreur: "Inscription impossible pour le moment. Réessayez plus tard." }); }
  // 400 = contact déjà inscrit le plus souvent : même réponse, pour ne pas révéler qui est inscrit.
  return rep(200, { ok: true });
}

/* ------------------------------------------------------------ 4. webhook Stripe : confirmation de commande
   Sur « checkout.session.completed », envoie au client la confirmation sur support durable
   (récapitulatif, délai, CGV en PDF jointe, formulaire type, lien « renoncer au contrat ici »),
   avec copie cachée au service client (article L221-13 du Code de la consommation).
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

async function webhook(ctx) {
  const env = ctx.env;
  if (!env.STRIPE_WEBHOOK_SECRET) return rep(503, { erreur: "Webhook non configuré." });
  if (!(await verifierSignatureStripe(ctx.corpsTexte, ctx.signature, env.STRIPE_WEBHOOK_SECRET))) return rep(400, { erreur: "Signature invalide." });
  const evt = lireJSON(ctx.corpsTexte);
  if (evt.type !== "checkout.session.completed") return rep(200, { ignore: evt.type });
  const s = evt.data && evt.data.object;
  if (!s || s.payment_status !== "paid") return rep(200, { ignore: "non payée" });
  if (!env.BREVO_API_KEY || !env.EMAIL_EXPEDITEUR || !env.EMAIL_SERVICE_CLIENT) return rep(503, { erreur: "Envoi d'e-mail non configuré." });
  const cat = await chargerCatalogue(ctx);
  const parSku = {};
  cat.produits.concat(cat.kits).forEach((x) => { parSku[x.sku] = x; });
  const lignes = String((s.metadata || {}).panier || "").split(",").map((x) => x.trim()).filter(Boolean).map((x) => {
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
  const html = `<p>Bonjour ${htmlEsc(client.name || "")},</p><p>Merci pour votre commande <strong>${htmlEsc(numero)}</strong>. Votre paiement est confirmé.</p>`
    + `<table cellpadding="6" style="border-collapse:collapse">${tableau}<tr><td>Livraison point relais</td><td></td><td align="right">${port ? euros(port) : "Offerte"}</td></tr><tr><th align="left">Total TTC</th><td></td><th align="right">${euros(s.amount_total || 0)}</th></tr></table>`
    + `<p>Livraison : ${htmlEsc([livr.name, adr.line1, adr.line2, adr.postal_code, adr.city].filter(Boolean).join(", "))}. Point relais demandé : ${htmlEsc((s.metadata || {}).point_relais || "le plus proche de cette adresse")}.</p>`
    + `<p>Expédition depuis la France sous 1 jour ouvré, livraison en point relais Mondial Relay en 3 à 6 jours ouvrés. Vous recevrez le numéro de suivi par e-mail.</p>`
    + `<p><strong>30 jours pour changer d'avis</strong> après réception (14 jours légaux + 16 jours offerts) : <a href="${site}/retractation/">renoncer au contrat ici</a>. Formulaire type de rétractation et conditions : <a href="${site}/retours-retractation/">${site}/retours-retractation/</a>.</p>`
    + `<p>Nos conditions générales de vente acceptées lors de la commande (version ${htmlEsc((s.metadata || {}).cgv_version || "")}) sont jointes en PDF et consultables sur <a href="${site}/cgv/">${site}/cgv/</a>.</p><p>${htmlEsc(nomMarque)}</p>`;
  const message = {
    sender: { email: env.EMAIL_EXPEDITEUR, name: nomMarque },
    to: [{ email: client.email || env.EMAIL_SERVICE_CLIENT }],
    bcc: [{ email: env.EMAIL_SERVICE_CLIENT }],
    replyTo: { email: env.EMAIL_SERVICE_CLIENT, name: nomMarque },
    subject: `Confirmation de votre commande ${numero}`,
    htmlContent: html,
  };
  if (/^https:\/\//.test(site)) message.attachment = [{ url: site + "/documents/cgv-canapoil.pdf", name: "CGV-Canapoil.pdf" }];
  await envoyerEmail(env, message);
  return rep(200, { envoye: true });
}

/* ------------------------------------------------------------ point d'entrée commun */
const ACTIONS = { checkout, retractation, inscription, webhook };

/* CORS : utile seulement si une autre origine autorisée (par exemple la boutique Shopify,
   déclarée dans ORIGINES_AUTORISEES) appelle la fonction de rétractation. */
function entetesCors(ctx) {
  if (!ctx.origine || !verifierOrigine(ctx)) return {};
  return { "Access-Control-Allow-Origin": ctx.origine, Vary: "Origin", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400" };
}

async function traiter(action, ctx) {
  const cors = entetesCors(ctx);
  const avec = (r) => Object.assign(r, { entetes: cors });
  try {
    if (ctx.methode === "OPTIONS") return avec({ statut: 204, corps: null });
    if (ctx.methode && ctx.methode !== "POST") return avec(rep(405, { erreur: "Méthode non autorisée." }));
    if (!verifierOrigine(ctx)) return rep(403, { erreur: "Origine non autorisée." });
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
      chargeur: env.ASSETS ? async () => (await env.ASSETS.fetch(new URL("/data/products.json", url))).json() : null,
    });
    return new Response(res.statut === 204 ? null : corpsReponse(res), { status: res.statut, headers: Object.assign({}, ENTETES, res.entetes) });
  };
}

module.exports = { traiter, netlify, cloudflare, calculerPanier, encoder, disponible, verifierSignatureStripe, _ErreurClient: ErreurClient };
