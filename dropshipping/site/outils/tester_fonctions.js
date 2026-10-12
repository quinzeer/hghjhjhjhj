/* Tests de la logique serveur (netlify/lib/coeur.js) sans réseau : fetch est simulé.
   Usage : node site/outils/tester_fonctions.js   (Node 18 ou plus)
   Vérifie : recalcul des prix côté serveur, refus des articles inconnus et des quantités
   invalides, frais de port, paramètres envoyés à Stripe, rétractation et inscription. */
"use strict";
const path = require("path");
const fs = require("fs");
const assert = require("assert");

const SITE = path.resolve(__dirname, "..");
const catalogue = JSON.parse(fs.readFileSync(path.join(SITE, "data/products.json"), "utf8"));
const coeur = require(path.join(SITE, "netlify/lib/coeur.js"));
const createCheckout = require(path.join(SITE, "netlify/functions/create-checkout.js"));
const retractation = require(path.join(SITE, "netlify/functions/retractation.js"));
const inscription = require(path.join(SITE, "netlify/functions/inscription.js"));
const webhook = require(path.join(SITE, "netlify/functions/stripe-webhook.js"));
const crypto = require("crypto");

let appels = [];
global.fetch = async (url, opts) => {
  appels.push({ url: String(url), opts: opts || {} });
  if (String(url).endsWith("/data/products.json")) return { ok: true, status: 200, json: async () => catalogue };
  if (String(url).startsWith("https://api.stripe.com/")) return { ok: true, status: 200, json: async () => ({ id: "cs_test_123", url: "https://checkout.stripe.com/c/pay/cs_test_123" }) };
  if (String(url).startsWith("https://api.brevo.com/")) return { ok: true, status: 201, json: async () => ({}), text: async () => "" };
  throw new Error("URL inattendue " + url);
};

const ENV = { STRIPE_SECRET_KEY: "sk_test_x", SITE_URL: "https://canapoil.fr", BREVO_API_KEY: "xkeysib-x", EMAIL_EXPEDITEUR: "bonjour@canapoil.fr", EMAIL_SERVICE_CLIENT: "sav@canapoil.fr", BREVO_LISTE_ID: "3", BREVO_TEMPLATE_DOI: "7" };
const evenement = (corps, extra) => Object.assign({ httpMethod: "POST", headers: { origin: "https://canapoil.fr", host: "canapoil.fr" }, body: JSON.stringify(corps) }, extra || {});
const decoder = (body) => Object.fromEntries(new URLSearchParams(body));

let n = 0;
async function test(nom, fn) { appels = []; await fn(); n++; console.log("ok -", nom); }

(async () => {
  Object.assign(process.env, ENV);

  await test("rouleau seul : 24,90 € + 3,90 € de port, prix venant du serveur", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1, prix_ttc: 0.01 }], cgv_acceptees: true, cgv_version: "2026-10-12", point_relais: "Relais 123", phase: "vente" }));
    assert.strictEqual(r.statusCode, 200, r.body);
    const stripe = appels.find((a) => a.url.startsWith("https://api.stripe.com"));
    const p = decoder(stripe.opts.body);
    assert.strictEqual(p["line_items[0][price_data][unit_amount]"], "2490");
    assert.strictEqual(p["line_items[0][quantity]"], "1");
    assert.strictEqual(p["shipping_options[0][shipping_rate_data][fixed_amount][amount]"], "390");
    assert.strictEqual(p["shipping_address_collection[allowed_countries][0]"], "FR");
    assert.strictEqual(p["locale"], "fr");
    assert.strictEqual(p["mode"], "payment");
    assert.strictEqual(p["metadata[point_relais]"], "Relais 123");
    assert.ok(p["success_url"].startsWith("https://canapoil.fr/merci.html?session_id={CHECKOUT_SESSION_ID}"));
    assert.strictEqual(JSON.parse(r.body).total, 2880);
    assert.ok(stripe.opts.headers.Authorization === "Bearer sk_test_x");
  });

  await test("Grand kit : livraison offerte", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "grand-kit", qte: 1 }], cgv_acceptees: true }));
    const p = decoder(appels.find((a) => a.url.startsWith("https://api.stripe.com")).opts.body);
    assert.strictEqual(p["line_items[0][price_data][unit_amount]"], "3990");
    assert.strictEqual(p["shipping_options[0][shipping_rate_data][fixed_amount][amount]"], "0");
    assert.strictEqual(JSON.parse(r.body).total, 3990);
  });

  await test("seuil de 35 € : rouleau + raclette = 37,80 €, port offert", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }, { id: "raclette-anti-poils", qte: 1 }], cgv_acceptees: true }));
    assert.strictEqual(JSON.parse(r.body).total, 3780);
  });

  await test("doublons fusionnés : 2 lignes rouleau → quantité 3", async () => {
    await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }, { id: "rouleau-anti-poils", qte: 2 }], cgv_acceptees: true }));
    const p = decoder(appels.find((a) => a.url.startsWith("https://api.stripe.com")).opts.body);
    assert.strictEqual(p["line_items[0][quantity]"], "3");
    assert.strictEqual(p["line_items[1][quantity]"], undefined);
  });

  await test("article inconnu refusé (400)", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "produit-pirate", qte: 1 }], cgv_acceptees: true }));
    assert.strictEqual(r.statusCode, 400);
    assert.ok(!appels.some((a) => a.url.startsWith("https://api.stripe.com")));
  });

  await test("quantités invalides refusées (0, 11, 1.5, texte)", async () => {
    for (const q of [0, 11, 1.5, "2"]) {
      const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: q }], cgv_acceptees: true }));
      assert.strictEqual(r.statusCode, 400, "qte " + q);
    }
  });

  await test("prototype pollution : id « __proto__ » refusé", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "__proto__", qte: 1 }], cgv_acceptees: true }));
    assert.strictEqual(r.statusCode, 400);
  });

  await test("CGV non acceptées : refus", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }] }));
    assert.strictEqual(r.statusCode, 400);
  });

  await test("origine étrangère : 403", async () => {
    const r = await createCheckout.handler(evenement({ lignes: [{ id: "rouleau-anti-poils", qte: 1 }], cgv_acceptees: true }, { headers: { origin: "https://pirate.example", host: "canapoil.fr" } }));
    assert.strictEqual(r.statusCode, 403);
  });

  await test("méthode GET : 405", async () => {
    const r = await createCheckout.handler({ httpMethod: "GET", headers: {}, body: "" });
    assert.strictEqual(r.statusCode, 405);
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
    assert.strictEqual(r.statusCode, 400, r.body);
  });

  await test("rétractation : accusé horodaté envoyé au client et au service client", async () => {
    const r = await retractation.handler(evenement({ nom: "Martin", prenom: "Camille", commande: "1042", email: "camille@exemple.fr", produits: "" }));
    assert.strictEqual(r.statusCode, 200, r.body);
    const corps = JSON.parse(r.body);
    assert.ok(corps.horodatage && corps.reference.startsWith("RET-"));
    const brevo = JSON.parse(appels.find((a) => a.url.endsWith("/smtp/email")).opts.body);
    assert.strictEqual(brevo.to[0].email, "camille@exemple.fr");
    assert.strictEqual(brevo.bcc[0].email, "sav@canapoil.fr");
    assert.ok(brevo.htmlContent.includes("heure de Paris") && brevo.htmlContent.includes("1042"));
  });

  await test("rétractation : champs manquants refusés", async () => {
    const r = await retractation.handler(evenement({ nom: "", prenom: "Camille", commande: "1042", email: "x" }));
    assert.strictEqual(r.statusCode, 400);
  });

  await test("inscription : double opt-in Brevo", async () => {
    const r = await inscription.handler(evenement({ email: "camille@exemple.fr", source: "liste-attente" }));
    assert.strictEqual(r.statusCode, 200);
    const b = JSON.parse(appels.find((a) => a.url.endsWith("/contacts/doubleOptinConfirmation")).opts.body);
    assert.deepStrictEqual(b.includeListIds, [3]);
    assert.strictEqual(b.templateId, 7);
  });

  await test("CORS : boutique Shopify autorisée (OPTIONS 204 + POST avec Access-Control-Allow-Origin)", async () => {
    process.env.ORIGINES_AUTORISEES = "https://canapoil.myshopify.com";
    const h = { origin: "https://canapoil.myshopify.com", host: "canapoil.fr" };
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

  await test("webhook Stripe : signature vérifiée, confirmation envoyée avec CGV en PDF", async () => {
    process.env.STRIPE_WEBHOOK_SECRET = "whsec_test";
    const evt = JSON.stringify({ type: "checkout.session.completed", data: { object: { id: "cs_test_abcdef1234", payment_status: "paid", amount_total: 3990,
      total_details: { amount_shipping: 0 }, customer_details: { email: "camille@exemple.fr", name: "Camille Martin" },
      collected_information: { shipping_details: { name: "Camille Martin", address: { line1: "1 rue des Chats", postal_code: "75011", city: "Paris" } } },
      metadata: { panier: "CNP-KIT-GK x1", point_relais: "Relais 123", cgv_version: "2026-10-12" } } } });
    const t = Math.floor(Date.now() / 1000);
    const sig = crypto.createHmac("sha256", "whsec_test").update(`${t}.${evt}`).digest("hex");
    const r = await webhook.handler({ httpMethod: "POST", headers: { "stripe-signature": `t=${t},v1=${sig}` }, body: evt });
    assert.strictEqual(r.statusCode, 200, r.body);
    const mail = JSON.parse(appels.find((a) => a.url.endsWith("/smtp/email")).opts.body);
    assert.strictEqual(mail.to[0].email, "camille@exemple.fr");
    assert.ok(mail.htmlContent.includes("Grand kit") && mail.htmlContent.includes("39,90") && mail.htmlContent.includes("renoncer au contrat ici"));
    assert.ok(mail.attachment[0].url.endsWith("/documents/cgv-canapoil.pdf"));
    const faux = await webhook.handler({ httpMethod: "POST", headers: { "stripe-signature": `t=${t},v1=${"0".repeat(64)}` }, body: evt });
    assert.strictEqual(faux.statusCode, 400);
  });

  console.log(`${n} tests réussis.`);
})().catch((e) => { console.error("ÉCHEC :", e.message); process.exit(1); });
