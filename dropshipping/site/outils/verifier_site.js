/* Vérification de bout en bout du site Canapoil avec Playwright.
   Prérequis : un serveur statique sur le dossier site/, par exemple
     cd site && python3 -m http.server 8765 --bind 127.0.0.1
   Usage :
     NODE_PATH="$(npm root -g)" node site/outils/verifier_site.js [http://127.0.0.1:8765] [dossier_captures]
   Le script parcourt accueil → produit → ajout au panier → panier → commande (démo) → merci
   en 390 px et 1440 px, contrôle la console, la persistance du panier, les liens internes,
   le SEO de chaque page, le consentement, la rétractation, le mode production simulé
   et le mode liste d'attente, puis enregistre des captures. Code de sortie 1 si un contrôle échoue. */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const BASE = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const CAPTURES = path.resolve(process.argv[3] || path.join(__dirname, "../../docs/captures"));
const SITE = path.resolve(__dirname, "..");
fs.mkdirSync(CAPTURES, { recursive: true });

const resultats = [];
const ok = (nom, cond, detail) => { resultats.push({ nom, ok: !!cond, detail: detail || "" }); if (!cond) console.log("ÉCHEC :", nom, detail || ""); };
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

function surveiller(page, etiquette, journal) {
  page.on("console", (m) => { if (["error", "warning"].includes(m.type())) journal.push(`${etiquette} console.${m.type()} : ${m.text()}`); });
  page.on("pageerror", (e) => journal.push(`${etiquette} exception : ${e.message}`));
  page.on("requestfailed", (r) => journal.push(`${etiquette} requête échouée : ${r.url()} ${r.failure() && r.failure().errorText}`));
  page.on("response", (r) => { if (r.status() >= 400) journal.push(`${etiquette} HTTP ${r.status()} : ${r.url()}`); });
}

async function chargerImagesDifferees(page) {
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 30)); }
    window.scrollTo(0, 0);
  });
  await page.waitForLoadState("networkidle");
  await attendre(300);
}

async function capturer(page, nom, complet) {
  if (complet) {
    await chargerImagesDifferees(page);
    await page.addStyleTag({ content: ".barre-achat{display:none!important}" });
  }
  await page.screenshot({ path: path.join(CAPTURES, nom), fullPage: !!complet });
}

async function parcours(browser, format) {
  const mobile = format === "mobile";
  const ctx = await browser.newContext(mobile
    ? { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "fr-FR", timezoneId: "Europe/Paris" }
    : { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, locale: "fr-FR", timezoneId: "Europe/Paris" });
  const page = await ctx.newPage();
  const journal = [];
  const externes = [];
  page.on("request", (r) => { if (!r.url().startsWith(BASE) && !r.url().startsWith("data:")) externes.push(r.url()); });
  surveiller(page, format, journal);

  // 1. Accueil + bandeau cookies
  await page.goto(BASE + "/", { waitUntil: "networkidle" });
  const bandeau = page.locator("#bandeau-cookies");
  ok(`[${format}] bandeau cookies affiché à la première visite`, await bandeau.isVisible());
  const bRef = await page.locator(".js-cookies-refuser").boundingBox();
  const bAcc = await page.locator(".js-cookies-accepter").boundingBox();
  ok(`[${format}] « Tout refuser » aussi visible que « Tout accepter »`, bRef && bAcc && Math.abs(bRef.width - bAcc.width) < 2 && Math.abs(bRef.height - bAcc.height) < 2,
    JSON.stringify({ refuser: bRef && [Math.round(bRef.width), Math.round(bRef.height)], accepter: bAcc && [Math.round(bAcc.width), Math.round(bAcc.height)] }));
  const memeStyle = await page.evaluate(() => {
    const a = getComputedStyle(document.querySelector(".js-cookies-refuser")), b = getComputedStyle(document.querySelector(".js-cookies-accepter"));
    return a.backgroundColor === b.backgroundColor && a.color === b.color && a.fontSize === b.fontSize && a.fontWeight === b.fontWeight;
  });
  ok(`[${format}] boutons du bandeau de même style`, memeStyle);
  ok(`[${format}] aucun script de traceur avant consentement`, (await page.locator("script[data-traceur]").count()) === 0);
  if (mobile) await page.screenshot({ path: path.join(CAPTURES, "bandeau-cookies-mobile.png") });
  await page.locator(".js-cookies-refuser").click();
  ok(`[${format}] refus enregistré, bandeau fermé`, !(await bandeau.isVisible()) && (await page.evaluate(() => JSON.parse(localStorage.getItem("canapoil_consentement_v1") || "{}").publicite === false)));
  await capturer(page, `accueil-${format}.png`);
  await capturer(page, `accueil-${format}-complet.png`, true);

  // 2. Fiche produit héros
  await page.locator(".hero__actions a.btn--primaire").click();
  await page.waitForURL("**/produits/rouleau-anti-poils-reutilisable/");
  await page.waitForLoadState("networkidle");
  const ajout = page.locator(".js-ajouter");
  ok(`[${format}] prix affiché sur la fiche`, (await page.locator(".js-prix-offre").innerText()).includes("24,90"));
  ok(`[${format}] délai avec dates affiché`, /entre le .+ et le .+/.test(await page.locator(".js-dates-livraison").first().innerText()));
  ok(`[${format}] bloc GPSR présent`, (await page.locator(".gpsr").count()) >= 1);
  ok(`[${format}] avis : état vide, aucun aggregateRating`, (await page.locator(".avis-vide").count()) === 1 && !(await page.content()).includes("aggregateRating"));
  if (mobile) {
    const box = await page.locator(".benefices li").first().boundingBox();
    ok("[mobile] premier bénéfice visible sans défiler", box && box.y + box.height <= 844, `y=${box && Math.round(box.y)}`);
  }
  await capturer(page, `produit-${format}.png`);
  // le sélecteur d'offre met à jour le prix
  await page.locator('label.offre[data-offre="grand-kit"]').click();
  ok(`[${format}] sélecteur d'offre : prix du Grand kit`, (await page.locator(".js-prix-offre").innerText()).includes("39,90"));
  await page.locator('label.offre[data-offre="rouleau-anti-poils"]').click();
  // barre collante mobile
  if (mobile) {
    await page.evaluate(() => window.scrollTo(0, 2200));
    await attendre(500);
    ok("[mobile] barre d'achat collante visible après défilement", await page.locator(".js-barre-achat").isVisible());
    await page.evaluate(() => window.scrollTo(0, 0));
    await attendre(300);
  }
  await capturer(page, `produit-${format}-complet.png`, true);
  await page.reload({ waitUntil: "networkidle" });

  // 3. Ajout au panier → tiroir
  await ajout.click();
  const tiroir = page.locator("#tiroir-panier");
  await tiroir.waitFor({ state: "visible" });
  await attendre(400);
  ok(`[${format}] tiroir ouvert après ajout`, await tiroir.isVisible());
  ok(`[${format}] compteur = 1`, (await page.locator(".js-compteur").first().innerText()).trim() === "1");
  ok(`[${format}] barre de progression vers la livraison offerte`, (await page.locator("#tiroir-panier .progression__texte").innerText()).includes("Plus que"));
  ok(`[${format}] focus dans le tiroir`, await page.evaluate(() => document.getElementById("tiroir-panier").contains(document.activeElement)));
  if (mobile) await page.screenshot({ path: path.join(CAPTURES, "panier-mobile.png") });
  else await page.screenshot({ path: path.join(CAPTURES, "panier-desktop.png") });
  await page.locator('#tiroir-panier [data-action="plus"]').click();
  await attendre(150);
  ok(`[${format}] quantité 2 : total 49,80 € et livraison offerte`, (await page.locator("#tiroir-panier .recap__ligne--total").innerText()).includes("49,80") && (await page.locator("#tiroir-panier .progression__texte").innerText()).includes("Livraison offerte"));
  await page.locator('#tiroir-panier [data-action="moins"]').click();
  await attendre(150);
  await page.keyboard.press("Escape");
  await attendre(400);
  ok(`[${format}] Échap ferme le tiroir`, !(await tiroir.isVisible()));

  // 4. Persistance après rechargement et sur une autre page
  await page.reload({ waitUntil: "networkidle" });
  ok(`[${format}] panier conservé après rechargement`, (await page.locator(".js-compteur").first().innerText()).trim() === "1");
  await page.goto(BASE + "/faq/", { waitUntil: "networkidle" });
  ok(`[${format}] panier conservé sur une autre page`, (await page.locator(".js-compteur").first().innerText()).trim() === "1");

  // 5. Page panier
  await page.goto(BASE + "/panier/", { waitUntil: "networkidle" });
  ok(`[${format}] page panier : 1 ligne`, (await page.locator(".panneau .ligne").count()) === 1);
  ok(`[${format}] page panier : suggestion Grand kit loyale (écart réel)`, (await page.locator(".panneau .js-suggestion").innerText()).includes("Grand kit"));
  if (mobile) await capturer(page, "panier-page-mobile.png");

  // 6. Commande démo
  await page.locator("aside .js-vers-commande").click();
  await page.waitForURL("**/commande/");
  await page.waitForLoadState("networkidle");
  ok(`[${format}] avertissement mode démo affiché`, await page.locator(".js-avertissement-demo").isVisible());
  ok(`[${format}] case CGV non pré-cochée`, !(await page.locator("#cgv").isChecked()));
  await page.locator(".js-payer").click();
  ok(`[${format}] refus sans acceptation des CGV`, (await page.locator("#erreur-cgv").innerText()).includes("Cochez") && page.url().includes("/commande/"));
  await page.locator("#point-relais").fill("Relais 012345 Paris 11e");
  await page.locator("#cgv").check();
  if (mobile) { await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" })); await attendre(200); await capturer(page, "commande-mobile.png"); }
  await page.locator(".js-payer").click();
  await page.waitForURL("**/merci.html?demo=1");
  await page.waitForLoadState("networkidle");
  ok(`[${format}] merci : avertissement « simulation »`, await page.locator(".js-merci-demo").isVisible());
  ok(`[${format}] merci : récapitulatif affiché`, await page.locator(".js-merci-recap").isVisible());
  ok(`[${format}] merci : panier vidé`, (await page.locator(".js-compteur").first().innerText()).trim() === "0" && (await page.evaluate(() => localStorage.getItem("canapoil_panier_v1"))) === null);
  if (mobile) await capturer(page, "merci-mobile.png");

  // 7. Ajout rapide depuis la boutique (kit) puis tiroir
  await page.goto(BASE + "/boutique/", { waitUntil: "networkidle" });
  await page.locator('[data-ajouter="grand-kit"]').first().click();
  await tiroir.waitFor({ state: "visible" });
  ok(`[${format}] ajout rapide d'un kit : livraison offerte`, (await page.locator("#tiroir-panier .progression__texte").innerText()).includes("Livraison offerte"));
  await page.keyboard.press("Escape");

  ok(`[${format}] aucune requête vers un domaine tiers`, externes.length === 0, externes.slice(0, 5).join(" "));
  ok(`[${format}] zéro erreur ou avertissement console / HTTP`, journal.length === 0, journal.join(" | "));
  await ctx.close();
}

async function controlerPages(browser) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx.addInitScript(() => { try { localStorage.setItem("canapoil_consentement_v1", JSON.stringify({ mesure: false, publicite: false, date: Date.now(), version: 1 })); } catch (e) { /* */ } });
  const page = await ctx.newPage();
  const journal = [];
  surveiller(page, "pages", journal);
  const sitemap = fs.readFileSync(path.join(SITE, "sitemap.xml"), "utf8");
  const pages = Array.from(sitemap.matchAll(/<loc>https:\/\/[^/]+(\/[^<]*)<\/loc>/g)).map((m) => m[1]);
  ["/panier/", "/commande/", "/merci.html", "/retractation/", "/404.html"].forEach((p) => pages.push(p));
  const titres = new Map(), descriptions = new Map(), liens = new Set();
  for (const u of pages) {
    const r = await page.goto(BASE + u, { waitUntil: "networkidle" });
    ok(`page ${u} : HTTP 200`, r && r.status() === 200, r && String(r.status()));
    const info = await page.evaluate(() => {
      const ld = Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map((s) => { try { return JSON.parse(s.textContent)["@type"]; } catch (e) { return "INVALIDE"; } });
      return {
        h1: document.querySelectorAll("h1").length,
        lang: document.documentElement.lang,
        titre: document.title,
        desc: (document.querySelector('meta[name="description"]') || {}).content || "",
        canon: (document.querySelector('link[rel="canonical"]') || {}).href || "",
        og: !!document.querySelector('meta[property="og:image"]'),
        imgSansAlt: Array.from(document.images).filter((i) => !i.hasAttribute("alt")).length,
        champsSansLabel: Array.from(document.querySelectorAll("input:not([type=hidden]),textarea,select")).filter((c) => !(c.labels && c.labels.length) && !c.getAttribute("aria-label")).map((c) => c.name || c.id),
        ld,
        liens: Array.from(document.querySelectorAll("a[href]")).map((a) => a.getAttribute("href")).concat(
          Array.from(document.querySelectorAll("img[src],script[src],link[href]")).map((x) => x.getAttribute("src") || x.getAttribute("href"))),
        renoncer: Array.from(document.querySelectorAll("footer a")).some((a) => a.textContent.trim() === "renoncer au contrat ici"),
        mediateur: document.body.innerText.includes("Médiateur de la consommation"),
        largeur: document.documentElement.scrollWidth,
      };
    });
    ok(`page ${u} : un seul h1`, info.h1 === 1, String(info.h1));
    ok(`page ${u} : lang="fr"`, info.lang === "fr");
    ok(`page ${u} : title et description présents`, info.titre.length > 10 && info.desc.length > 20);
    ok(`page ${u} : canonical et Open Graph`, info.canon.startsWith("https://") && info.og);
    ok(`page ${u} : images avec attribut alt`, info.imgSansAlt === 0, String(info.imgSansAlt));
    ok(`page ${u} : champs de formulaire étiquetés`, info.champsSansLabel.length === 0, info.champsSansLabel.join(","));
    ok(`page ${u} : JSON-LD valide`, !info.ld.includes("INVALIDE"), info.ld.join(","));
    ok(`page ${u} : lien « renoncer au contrat ici » en pied de page`, info.renoncer);
    ok(`page ${u} : médiateur mentionné`, info.mediateur);
    ok(`page ${u} : aucun défilement horizontal à 390 px`, info.largeur <= 390, String(info.largeur));
    if (titres.has(info.titre)) ok(`page ${u} : title unique`, false, "doublon de " + titres.get(info.titre)); else titres.set(info.titre, u);
    if (descriptions.has(info.desc)) ok(`page ${u} : description unique`, false, "doublon de " + descriptions.get(info.desc)); else descriptions.set(info.desc, u);
    info.liens.forEach((l) => { if (l && l.startsWith("/") && !l.startsWith("//")) liens.add(l.split("#")[0]); });
    if (u.startsWith("/produits/")) ok(`page ${u} : JSON-LD Product`, info.ld.includes("Product"));
    if (u === "/faq/") ok("FAQ : JSON-LD FAQPage", info.ld.includes("FAQPage"));
    if (u === "/") ok("Accueil : JSON-LD Organization", info.ld.includes("Organization"));
  }
  // Liens internes et ressources
  const casses = [];
  for (const l of liens) {
    const r = await page.request.get(BASE + l);
    if (r.status() !== 200) casses.push(`${l} (${r.status()})`);
  }
  ok(`liens internes et ressources : ${liens.size} URL testées, toutes en 200`, casses.length === 0, casses.join(", "));
  ok("pages : zéro erreur console / HTTP", journal.length === 0, journal.join(" | "));
  await ctx.close();
}

async function controlesSpeciaux(browser) {
  const configOrigine = fs.readFileSync(path.join(SITE, "assets/js/config.js"), "utf8");
  const consentement = () => { try { localStorage.setItem("canapoil_consentement_v1", JSON.stringify({ mesure: false, publicite: false, date: Date.now(), version: 1 })); } catch (e) { /* */ } };

  // a) Mode production simulé : le navigateur n'envoie que des identifiants et des quantités.
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    await ctx.addInitScript(consentement);
    const page = await ctx.newPage();
    const journal = [];
    surveiller(page, "production", journal);
    await page.route("**/assets/js/config.js*", (route) => route.fulfill({ contentType: "application/javascript", body: configOrigine.replace('mode: "demo"', 'mode: "production"') }));
    let envoye = null;
    await page.route("**/api/create-checkout", async (route) => {
      envoye = JSON.parse(route.request().postData() || "{}");
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ url: BASE + "/merci.html?session_id=cs_test_simule" }) });
    });
    await page.goto(BASE + "/kits/grand-kit/", { waitUntil: "networkidle" });
    await page.locator(".js-ajouter").click();
    await page.goto(BASE + "/commande/", { waitUntil: "networkidle" });
    ok("production : pas d'avertissement démo", !(await page.locator(".js-avertissement-demo").isVisible()));
    await page.locator("#cgv").check();
    await page.locator(".js-payer").click();
    await page.waitForURL("**/merci.html?session_id=cs_test_simule");
    await page.waitForLoadState("networkidle");
    await attendre(200);
    const cles = envoye ? Object.keys(envoye).sort().join(",") : "";
    ok("production : corps envoyé sans aucun prix", envoye && cles === "cgv_acceptees,cgv_version,lignes,phase,point_relais" && JSON.stringify(envoye.lignes) === '[{"id":"grand-kit","qte":1}]', JSON.stringify(envoye));
    ok("production : panier vidé au retour de Stripe", (await page.evaluate(() => localStorage.getItem("canapoil_panier_v1"))) === null);
    ok("production : zéro erreur console", journal.length === 0, journal.join(" | "));
    await ctx.close();
  }
  // b) Phase liste d'attente : aucune vente, formulaire d'inscription.
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    await ctx.addInitScript(consentement);
    const page = await ctx.newPage();
    const journal = [];
    surveiller(page, "attente", journal);
    await page.route("**/assets/js/config.js*", (route) => route.fulfill({ contentType: "application/javascript", body: configOrigine.replace('phase: "vente"', 'phase: "liste_attente"') }));
    await page.goto(BASE + "/produits/rouleau-anti-poils-reutilisable/", { waitUntil: "networkidle" });
    ok("liste d'attente : bouton d'ajout remplacé par l'inscription", (await page.locator(".js-ajouter").count()) === 0 && (await page.locator(".js-achat .js-form-inscription").count()) === 1);
    await page.locator(".js-achat input[type=email]").fill("test@exemple.fr");
    await page.locator(".js-achat button[type=submit]").click();
    ok("liste d'attente : confirmation (simulation)", (await page.locator(".js-achat .message--succes").innerText()).includes("Simulation"));
    await page.evaluate(() => document.querySelector(".js-achat").scrollIntoView({ block: "center" }));
    await page.screenshot({ path: path.join(CAPTURES, "liste-attente-mobile.png") });
    ok("liste d'attente : zéro erreur console", journal.length === 0, journal.join(" | "));
    await ctx.close();
  }
  // c) Rétractation en ligne (démo) + gestion des cookies + clavier
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const journal = [];
    surveiller(page, "retractation", journal);
    await page.goto(BASE + "/retractation/", { waitUntil: "networkidle" });
    await page.keyboard.press("Tab");
    ok("clavier : le premier Tab atteint le lien d'évitement", await page.evaluate(() => document.activeElement.classList.contains("lien-evitement")));
    const contour = await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle);
    ok("clavier : focus visible (outline)", contour && contour !== "none", contour);
    await page.locator(".js-cookies-accepter").click();
    await page.locator(".js-gerer-cookies").click();
    ok("« Gérer mes cookies » rouvre le choix avec les cases", await page.locator(".js-cookies-choix").isVisible() && (await page.locator('.js-cookies-choix [name="publicite"]').isChecked()));
    await page.locator(".js-cookies-refuser").click();
    await page.waitForLoadState("networkidle");
    ok("retrait du consentement enregistré", await page.evaluate(() => JSON.parse(localStorage.getItem("canapoil_consentement_v1")).publicite === false));
    await page.locator(".js-form-retractation button[type=submit]").click();
    ok("rétractation : champs obligatoires signalés", (await page.locator("#r-nom").getAttribute("aria-invalid")) === "true");
    ok("rétractation : bouton libellé « confirmer la rétractation »", (await page.locator(".js-form-retractation button[type=submit]").innerText()).trim() === "confirmer la rétractation");
    await page.fill("#r-nom", "Martin");
    await page.fill("#r-prenom", "Camille");
    await page.fill("#r-commande", "DEMO-ABC123");
    await page.fill("#r-email", "camille@exemple.fr");
    await page.locator(".js-form-retractation button[type=submit]").click();
    ok("rétractation : accusé de réception horodaté affiché", (await page.locator(".js-accuse").innerText()).includes("heure de Paris"));
    await page.screenshot({ path: path.join(CAPTURES, "retractation-desktop.png") });
    ok("rétractation : zéro erreur console", journal.length === 0, journal.join(" | "));
    await ctx.close();
  }
}

(async () => {
  const browser = await chromium.launch();
  try {
    await parcours(browser, "mobile");
    await parcours(browser, "desktop");
    await controlerPages(browser);
    await controlesSpeciaux(browser);
  } catch (e) {
    ok("exécution du script sans exception", false, e.stack);
  }
  await browser.close();
  // Poids du JavaScript livré au navigateur
  const js = ["assets/js/app.js", "assets/js/config.js"].reduce((s, f) => s + fs.statSync(path.join(SITE, f)).size, 0);
  ok(`JavaScript total < 60 Ko (${(js / 1024).toFixed(1)} Ko)`, js < 60 * 1024);
  const echecs = resultats.filter((r) => !r.ok);
  fs.writeFileSync(path.join(CAPTURES, "rapport-verification.json"), JSON.stringify({ date: new Date().toISOString(), base: BASE, total: resultats.length, echecs: echecs.length, resultats }, null, 2));
  console.log(`${resultats.length - echecs.length}/${resultats.length} contrôles réussis.`);
  process.exit(echecs.length ? 1 : 0);
})();
