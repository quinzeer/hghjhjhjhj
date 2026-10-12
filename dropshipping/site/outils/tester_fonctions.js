/* Tests de la logique serveur (netlify/lib/coeur.js) sans réseau : fetch est simulé.
   Usage : node site/outils/tester_fonctions.js   (Node 18 ou plus)
   Vérifie : recalcul des prix côté serveur, phase et stock lus dans products.json (jamais dans la
   requête), dates de précommande sur la page Stripe et dans l'e-mail de confirmation, refus des
   requêtes sans Origin, limite de 3 requêtes par heure, Turnstile, vérification de la commande avant
   l'accusé de rétractation, consentement et produit de la liste d'attente, UTM, idempotence du webhook. */
"use strict";
const path = require("path");
const fs = require("fs");
const assert = require("assert");

const SITE = path.resolve(__dirname, "..");
const base = JSON.parse(fs.readFileSync(path.join(SITE, "data/products.json"), "utf8"));
const coeur = require(path.join(SITE, "netlify/lib/coeur.js"));
const createCheckout = require(path.join(SITE, "netlify/functions/create-checkout.js"));
const retractation = require(path.join(SITE, "netlify/functions/retractation.js"));
const inscription = require(path.join(SITE, "netlify/functions/inscription.js"));
const webhook = require(path.join(SITE, "netlify/functions/stripe-webhook.js"));
const crypto = require("crypto");

/* Catalogues de test dérivés du products.json livré (phase de brand.json, en principe liste_attente). */
function catalogue(phase, opts) {
  const o = opts || {};
  const c = JSON.parse(JSON.stringify(base));
  c.livraison.phase = phase;
  const pc = phase === "precommande" ? { expedition_a_partir_du: "2026-12-02", livraison_au_plus_tard_le: "2026-12-10" } : null;
  c.livraison.precommande = pc;
  const etat = phase === "liste_attente" ? "attente" : phase === "precommande" ? "precommande" : "disponible";
  c.produits.forEach((p) => { p.etat = etat; p.stock_disponible = o.stock == null ? 20 : o.stock; p.stock_max_commande = etat === "attente" ? 0 : p.stock_disponible; if (pc) p.precommande = pc; else delete p.precommande; });
  c.kits.forEach((k) => { k.etat = etat; k.stock_max_commande = etat === "attente" ? 0 : 10; if (pc) k.precommande = pc; else delete k.precommande; });
  return c;
}
let CAT = catalogue("vente");
let sessionsStripe = [];
let turnstileOk = true;

let appels = [];
global.fetch = async (url, opts) => {
  const u = String(url);
  appels.push({ url: u, opts: opts || {} });
  if (u.endsWith("/data/products.json")) return { ok: true, status: 200, json: async () => CAT };
  if (u.startsWith("https://api.stripe.com/v1/checkout/sessions?")) return { ok: true, status: 200, json: async () => ({ data: sessionsStripe }) };
  if (u.startsWith("https://api.stripe.com/")) return { ok: true, status: 200, json: async () => ({ id: "cs_test_123", url: "https://checkout.stripe.com/c/pay/cs_test_123" }) };
  if (u.startsWith("https://api.brevo.com/")) return { ok: true, status: 201, json: async () => ({}), text: async () => "" };
  if (u.startsWith("https://challenges.cloudflare.com/")) return { ok: true, status: 200, json: async () => ({ success: turnstileOk }) };
  throw new Error("URL inattendue " + u);
};

const ENV = { STRIPE_SECRET_KEY: "sk_test_x", SITE_URL: "https://canapoil.fr", BREVO_API_KEY: "xkeysib-x", EMAIL_EXPEDITEUR: "bonjour@canapoil.fr", EMAIL_SERVICE_CLIENT: "sav@canapoil.fr", BREVO_LISTE_ID: "3", BREVO_TEMPLATE_DOI: "7" };
let ip = 1;
const evenement = (corps, extra) => Object.assign({ httpMethod: "POST", headers: { origin: "https://canapoil.fr", host: "canapoil.fr", "x-nf-client-connection-ip": "10.0.0." + ip }, body: JSON.stringify(corps) }, extra || {});
const decoder = (body) => Object.fromEntries(new URLSearchParams(body));
const stripeAppel = () => appels.find((a) => a.url === "https://api.stripe.com/v1/checkout/sessions");
const mails = () => appels.filter((a) => a.url.endsWith("/smtp/email")).map((a) => JSON.parse(a.opts.body));
function signer(evt, secret) {
  const t = Math.floor(Date.now() / 1000);
  return `t=${t},v1=${crypto.createHmac("sha256", secret).update(`${t}.${evt}`).digest("hex")}`;
}

let n = 0;
async function test(nom, fn) {
  appels = []; ip++; coeur._viderCache(); coeur._memoire.clear(); CAT = catalogue("vente"); sessionsStripe = []; turnstileOk = true;
  await fn(); n++; console.log("ok -", nom);
}

(async () => {
  Object.assign(process.env, ENV);

  await test("rouleau seul : 24,90 € + 3,90 € de port, prix venant du serveur, UTM en métadonnées", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1, prix_ttc: 0.01 }], cgv_acceptees: true, point_relais: "Relais 123", phase: "precommande", utm: { utm_source: "tiktok", utm_content: "R02", utm_campaign: "<script>" } }));
    assert.strictEqual(r.statusCode, 200, r.body);
    const p = decoder(stripeAppel().opts.body);
    assert.strictEqual(p["line_items[0][price_data][unit_amount]"], "2490");
    assert.strictEqual(p["shipping_options[0][shipping_rate_data][fixed_amount][amount]"], "390");
    assert.strictEqual(p["metadata[point_relais]"], "Relais 123");
    assert.strictEqual(p["metadata[phase]"], "vente", "la phase vient du catalogue, pas de la requête");
    assert.strictEqual(p["metadata[utm_source]"], "tiktok");
    assert.strictEqual(p["metadata[utm_content]"], "r02");
    assert.strictEqual(p["metadata[utm_campaign]"], "script");
    assert.ok(p["custom_text[submit][message]"].includes("sous 1 jour ouvré"));
    assert.ok(p["shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]"]);
    assert.strictEqual(JSON.parse(r.body).total, 2880);
  });

  await test("Grand kit : livraison offerte ; seuil de 35 € ; doublons fusionnés", async () => {
    let r = await createCheckout.handler(evenement({ lignes: [{ id: "grand-kit", qte: 1 }], cgv_acceptees: true }));
    assert.strictEqual(JSON.parse(r.body).total, 3990);
    r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }, { id: "raclette-anti-poils", qte: 1 }], cgv_acceptees: true }));
    assert.strictEqual(JSON.parse(r.body).total, 3780);
    appels = [];
    await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }, { id: "rouleau-anti-poils", qte: 2 }], cgv_acceptees: true }));
    const p = decoder(stripeAppel().opts.body);
    assert.strictEqual(p["line_items[0][quantity]"], "3");
    assert.strictEqual(p["line_items[1][quantity]"], undefined);
  });

  await test("entrées invalides : article inconnu, __proto__, quantités 0/11/1,5/texte, CGV non acceptées", async () => {
    for (const lignes of [[{ id: "produit-pirate", qte: 1 }], [{ id: "__proto__", qte: 1 }]]) {
      const r = await createCheckout.handler(evenement({ lignes, cgv_acceptees: true }));
      assert.strictEqual(r.statusCode, 400);
    }
    for (const q of [0, 11, 1.5, "2"]) {
      const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: q }], cgv_acceptees: true }));
      assert.strictEqual(r.statusCode, 400, "qte " + q);
    }
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }] }));
    assert.strictEqual(r.statusCode, 400);
    assert.ok(!stripeAppel());
  });

  await test("phase liste d'attente dans products.json : paiement refusé (503) même si le navigateur envoie « vente »", async () => {
    CAT = catalogue("liste_attente");
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }], cgv_acceptees: true, phase: "vente" }));
    assert.strictEqual(r.statusCode, 503, r.body);
    assert.ok(!stripeAppel());
  });

  await test("stock : une commande qui dépasse le stock affiché est refusée (409), kits compris", async () => {
    CAT = catalogue("vente", { stock: 3 });
    let r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 4 }], cgv_acceptees: true }));
    assert.strictEqual(r.statusCode, 409, r.body);
    r = await createCheckout.handler(evenement({ lignes: [{ id: "duo-rouleaux", qte: 1 }, { id: "rouleau-anti-poils", qte: 2 }], cgv_acceptees: true }));
    assert.strictEqual(r.statusCode, 409, "2 rouleaux du Duo + 2 rouleaux > 3");
    r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 3 }], cgv_acceptees: true }));
    assert.strictEqual(r.statusCode, 200);
    CAT.produits[0].etat = "epuise";
    coeur._viderCache();
    r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }], cgv_acceptees: true }));
    assert.strictEqual(r.statusCode, 409);
  });

  await test("précommande : dates sur la page Stripe et en métadonnées, aucune promesse « 1 jour ouvré »", async () => {
    CAT = catalogue("precommande");
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "grand-kit", qte: 1 }], cgv_acceptees: true }));
    assert.strictEqual(r.statusCode, 200, r.body);
    const corps = stripeAppel().opts.body, p = decoder(corps);
    assert.ok(p["custom_text[submit][message]"].includes("expédition à partir du 02/12/2026, livraison au plus tard le 10/12/2026"));
    assert.ok(!decodeURIComponent(corps).includes("1 jour ouvré"));
    assert.strictEqual(p["metadata[precommande]"], "oui");
    assert.strictEqual(p["metadata[precommande_livraison_max]"], "2026-12-10");
    assert.strictEqual(p["shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]"], undefined);
  });

  await test("origine : absente → 403 (checkout, rétractation, inscription) ; étrangère → 403 ; GET → 405", async () => {
    const sans = { headers: { host: "canapoil.fr" } };
    for (const [h, corps] of [[createCheckout, { lignes: [{ id: "rouleau-anti-poils", qte: 1 }], cgv_acceptees: true }],
      [retractation, { nom: "Martin", prenom: "Camille", commande: "1042", email: "victime@exemple.fr" }],
      [inscription, { email: "victime@exemple.fr", consentement: true }]]) {
      const r = await h.handler(evenement(corps, sans));
      assert.strictEqual(r.statusCode, 403);
    }
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }], cgv_acceptees: true }, { headers: { origin: "https://pirate.example", host: "canapoil.fr" } }));
    assert.strictEqual(r.statusCode, 403);
    assert.strictEqual(mails().length, 0);
    const g = await createCheckout.handler({ httpMethod: "GET", headers: {}, body: "" });
    assert.strictEqual(g.statusCode, 405);
  });

  await test("clé Stripe absente : 503 explicite, aucun appel", async () => {
    const cle = process.env.STRIPE_SECRET_KEY;
    delete process.env.STRIPE_SECRET_KEY;
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }], cgv_acceptees: true }));
    process.env.STRIPE_SECRET_KEY = cle;
    assert.strictEqual(r.statusCode, 503);
  });

  await test("produit de saison hors saison refusé (simulation en juin)", async () => {
    const RealDate = Date;
    global.Date = class extends RealDate { constructor(...a) { super(...(a.length ? a : ["2027-06-15T10:00:00Z"])); } static now() { return new RealDate("2027-06-15T10:00:00Z").getTime(); } };
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "tapis-fenetre-thermique", qte: 1 }], cgv_acceptees: true }));
    global.Date = RealDate;
    assert.strictEqual(r.statusCode, 409, r.body);
  });

  await test("rétractation, commande retrouvée (session Stripe payée, même e-mail) : accusé au client + copie", async () => {
    sessionsStripe = [{ id: "cs_test_a1b2c3d4e5F6G7H8J9", payment_status: "paid" }];
    const r = await retractation.handler(evenement({ nom: "Martin", prenom: "Camille", commande: "e5f6g7h8j9", email: "camille@exemple.fr", produits: "" }));
    assert.strictEqual(r.statusCode, 200, r.body);
    const corps = JSON.parse(r.body);
    assert.ok(corps.horodatage && corps.reference.startsWith("RET-") && corps.commande_verifiee === true);
    const liste = appels.find((a) => a.url.startsWith("https://api.stripe.com/v1/checkout/sessions?"));
    assert.ok(decodeURIComponent(liste.url).includes("customer_details[email]=camille@exemple.fr"));
    const m = mails()[0];
    assert.strictEqual(m.to[0].email, "camille@exemple.fr");
    assert.strictEqual(m.bcc[0].email, "sav@canapoil.fr");
    assert.ok(m.htmlContent.includes("heure de Paris"));
  });

  await test("rétractation, commande non retrouvée : rien vers l'adresse saisie, alerte au service client seulement", async () => {
    const r = await retractation.handler(evenement({ nom: "Martin", prenom: "Camille", commande: "VOTRE-COMPTE-EST-BLOQUE", email: "victime@exemple.fr" }));
    assert.strictEqual(r.statusCode, 200, r.body);
    assert.strictEqual(JSON.parse(r.body).commande_verifiee, false);
    const m = mails();
    assert.strictEqual(m.length, 1);
    assert.strictEqual(m[0].to[0].email, "sav@canapoil.fr");
    assert.ok(!JSON.stringify(m).includes("victime@exemple.fr\"}]"), "aucun destinataire victime");
    assert.ok(m[0].subject.startsWith("Rétractation à vérifier"));
  });

  await test("rétractation : URL, champs manquants et e-mail invalide refusés", async () => {
    for (const corps of [
      { nom: "Martin", prenom: "Camille", commande: "1042", email: "a@exemple.fr", produits: "voir https://pirate.example/connexion" },
      { nom: "www.pirate.example", prenom: "Camille", commande: "1042", email: "a@exemple.fr" },
      { nom: "", prenom: "Camille", commande: "1042", email: "a@exemple.fr" },
      { nom: "Martin", prenom: "Camille", commande: "1042", email: "x" }]) {
      ip++;
      const r = await retractation.handler(evenement(corps));
      assert.strictEqual(r.statusCode, 400, JSON.stringify(corps));
    }
    assert.strictEqual(mails().length, 0);
  });

  await test("limite : 3 requêtes par heure et par adresse IP, la 4e reçoit 429", async () => {
    const corps = { email: "camille@exemple.fr", consentement: true, produit: "rouleau-anti-poils" };
    for (let i = 0; i < 3; i++) assert.strictEqual((await inscription.handler(evenement(corps))).statusCode, 200);
    assert.strictEqual((await inscription.handler(evenement(corps))).statusCode, 429);
    ip++;
    assert.strictEqual((await inscription.handler(evenement(corps))).statusCode, 200, "autre adresse IP");
  });

  await test("Turnstile : jeton exigé et vérifié quand TURNSTILE_SECRET_KEY est défini", async () => {
    process.env.TURNSTILE_SECRET_KEY = "0x_secret";
    let r = await inscription.handler(evenement({ email: "camille@exemple.fr", consentement: true, produit: "lettre" }));
    assert.strictEqual(r.statusCode, 403, "sans jeton");
    turnstileOk = false;
    r = await retractation.handler(evenement({ nom: "Martin", prenom: "Camille", commande: "1042", email: "camille@exemple.fr", turnstile: "faux" }));
    assert.strictEqual(r.statusCode, 403);
    turnstileOk = true;
    r = await inscription.handler(evenement({ email: "camille@exemple.fr", consentement: true, produit: "lettre", turnstile: "bon" }));
    assert.strictEqual(r.statusCode, 200);
    const v = appels.filter((a) => a.url.startsWith("https://challenges.cloudflare.com/")).pop();
    assert.ok(String(v.opts.body).includes("secret=0x_secret") && String(v.opts.body).includes("response=bon"));
    delete process.env.TURNSTILE_SECRET_KEY;
  });

  await test("inscription : consentement obligatoire, produit contrôlé, attributs Brevo datés (produit, UTM)", async () => {
    let r = await inscription.handler(evenement({ email: "camille@exemple.fr", produit: "rouleau-anti-poils" }));
    assert.strictEqual(r.statusCode, 400, "sans consentement");
    ip++;
    r = await inscription.handler(evenement({ email: "camille@exemple.fr", consentement: true, produit: "produit-pirate" }));
    assert.strictEqual(r.statusCode, 400, "produit inconnu");
    ip++;
    r = await inscription.handler(evenement({ email: "camille@exemple.fr", consentement: true, produit: "tapis-de-fouille", source: "liste-attente", utm: { utm_source: "tiktok", utm_content: "TF26" } }));
    assert.strictEqual(r.statusCode, 200);
    const b = JSON.parse(appels.find((a) => a.url.endsWith("/contacts/doubleOptinConfirmation")).opts.body);
    assert.deepStrictEqual(b.includeListIds, [3]);
    assert.strictEqual(b.templateId, 7);
    assert.strictEqual(b.attributes.PRODUIT, "tapis-de-fouille");
    assert.strictEqual(b.attributes.UTM_CONTENT, "tf26");
    assert.ok(/^\d{4}-\d{2}-\d{2}T/.test(b.attributes.CONSENTEMENT_DATE));
  });

  await test("CORS : boutique Shopify autorisée (OPTIONS 204 + POST avec Access-Control-Allow-Origin)", async () => {
    process.env.ORIGINES_AUTORISEES = "https://canapoil.myshopify.com";
    const h = { origin: "https://canapoil.myshopify.com", host: "canapoil.fr", "x-nf-client-connection-ip": "10.9.9.9" };
    const pre = await retractation.handler({ httpMethod: "OPTIONS", headers: h, body: "" });
    assert.strictEqual(pre.statusCode, 204);
    assert.strictEqual(pre.headers["Access-Control-Allow-Origin"], "https://canapoil.myshopify.com");
    const r = await retractation.handler(evenement({ nom: "Martin", prenom: "Camille", commande: "1042", email: "camille@exemple.fr" }, { headers: h }));
    assert.strictEqual(r.statusCode, 200);
    assert.strictEqual(r.headers["Access-Control-Allow-Origin"], "https://canapoil.myshopify.com");
    const refuse = await retractation.handler({ httpMethod: "OPTIONS", headers: { origin: "https://pirate.example" }, body: "" });
    assert.ok(!refuse.headers["Access-Control-Allow-Origin"]);
    delete process.env.ORIGINES_AUTORISEES;
  });

  await test("webhook Stripe (vente) : signature vérifiée, confirmation avec délai standard et CGV en PDF", async () => {
    process.env.STRIPE_WEBHOOK_SECRET = "whsec_test";
    const evt = JSON.stringify({ id: "evt_1", type: "checkout.session.completed", data: { object: { id: "cs_test_abcdef1234", payment_status: "paid", amount_total: 3990,
      total_details: { amount_shipping: 0 }, customer_details: { email: "camille@exemple.fr", name: "Camille Martin" },
      collected_information: { shipping_details: { name: "Camille Martin", address: { line1: "1 rue des Chats", postal_code: "75011", city: "Paris" } } },
      metadata: { panier: "CNP-KIT-GK x1", point_relais: "Relais 123", cgv_version: "2026-10-12-vente", phase: "vente", precommande: "non" } } } });
    const r = await webhook.handler({ httpMethod: "POST", headers: { "stripe-signature": signer(evt, "whsec_test") }, body: evt });
    assert.strictEqual(r.statusCode, 200, r.body);
    const mail = mails()[0];
    assert.strictEqual(mail.to[0].email, "camille@exemple.fr");
    assert.ok(mail.htmlContent.includes("Grand kit") && mail.htmlContent.includes("39,90") && mail.htmlContent.includes("renoncer au contrat ici"));
    assert.ok(mail.htmlContent.includes("sous 1 jour ouvré"));
    assert.ok(mail.attachment[0].url.endsWith("/documents/cgv-canapoil.pdf"));
    const faux = await webhook.handler({ httpMethod: "POST", headers: { "stripe-signature": `t=${Math.floor(Date.now() / 1000)},v1=${"0".repeat(64)}` }, body: evt });
    assert.strictEqual(faux.statusCode, 400);
  });

  await test("webhook Stripe (précommande) : l'e-mail écrit les dates de précommande et jamais « 1 jour ouvré »", async () => {
    const evt = JSON.stringify({ id: "evt_2", type: "checkout.session.completed", data: { object: { id: "cs_test_precommande99", payment_status: "paid", amount_total: 3990,
      total_details: { amount_shipping: 0 }, customer_details: { email: "camille@exemple.fr", name: "Camille Martin" },
      metadata: { panier: "CNP-KIT-GK x1", cgv_version: "2026-10-12-precommande", phase: "precommande", precommande: "oui", precommande_expedition: "2026-12-02", precommande_livraison_max: "2026-12-10" } } } });
    const r = await webhook.handler({ httpMethod: "POST", headers: { "stripe-signature": signer(evt, "whsec_test") }, body: evt });
    assert.strictEqual(r.statusCode, 200, r.body);
    const mail = mails()[0];
    assert.ok(mail.htmlContent.includes("expédition depuis la France à partir du 02/12/2026, livraison en point relais Mondial Relay au plus tard le 10/12/2026"));
    assert.ok(!mail.htmlContent.includes("1 jour ouvré"));
    assert.ok(mail.subject.startsWith("Confirmation de votre précommande"));
  });

  await test("webhook rejoué : un seul e-mail quand le stockage KV est lié (idempotence)", async () => {
    const memoireKv = new Map();
    process.env.CANAPOIL_KV = "";
    const evt = JSON.stringify({ id: "evt_3", type: "checkout.session.completed", data: { object: { id: "cs_test_rejoue", payment_status: "paid", amount_total: 2880, customer_details: { email: "c@exemple.fr" }, metadata: { panier: "CNP-ROU-01 x1" } } } });
    const env = Object.assign({}, process.env, { CANAPOIL_KV: { get: async (k) => memoireKv.get(k) || null, put: async (k, v) => { memoireKv.set(k, v); } } });
    for (let i = 0; i < 2; i++) {
      const res = await coeur.traiter("webhook", { methode: "POST", origine: "", corpsTexte: evt, env, signature: signer(evt, "whsec_test"), hote: "https://canapoil.fr" });
      assert.strictEqual(res.statut, 200);
    }
    assert.strictEqual(mails().length, 1);
    delete process.env.CANAPOIL_KV;
  });

  console.log(`${n} tests réussis.`);
})().catch((e) => { console.error("ÉCHEC :", e.message); process.exit(1); });
