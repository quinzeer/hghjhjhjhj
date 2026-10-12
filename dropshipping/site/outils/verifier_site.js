/* Vérification de bout en bout du site Canapoil avec Playwright.
   Usage :
     NODE_PATH="$(npm root -g)" node site/outils/verifier_site.js [dossier_captures]
   Le script sert lui-même le site (serveur statique interne qui applique les en-têtes de _headers,
   dont la Content-Security-Policy) et génère, dans des copies temporaires, une variante par phase
   avec generer.py --sortie :
     - « livré »       : le site tel que brand.json le décrit (liste d'attente avant la porte 1) ;
     - « vente »       : stock en France, parcours complet accueil → produit → panier → commande → merci ;
     - « précommande » : dates d'expédition et de livraison, contrôle bloquant : la phrase
                          « 1 jour ouvré » ne doit apparaître sur aucune page (correction C1).
   Contrôles en 390 px et 1 440 px : console, persistance du panier, liens internes, SEO, consentement,
   rétractation, mode production simulé, bandeau de démonstration, formulaire de liste d'attente
   (consentement, produit), page du tapis de fouille, refus de publication avec des variables {{...}}.
   Captures dans docs/captures. Code de sortie 1 si un contrôle échoue. */
const path = require("path");
const fs = require("fs");
const os = require("os");
const http = require("http");
const { execFileSync, spawnSync } = require("child_process");
const { chromium } = require("playwright");

const SITE = path.resolve(__dirname, "..");
const CAPTURES = path.resolve(process.argv[2] || path.join(__dirname, "../../docs/captures"));
const GENERER = path.join(__dirname, "generer.py");
fs.mkdirSync(CAPTURES, { recursive: true });

const resultats = [];
const ok = (nom, cond, detail) => { resultats.push({ nom, ok: !!cond, detail: detail || "" }); if (!cond) console.log("ÉCHEC :", nom, detail || ""); };
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

/* ------------------------------------------------------------ variantes et serveur */
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "canapoil-verif-"));
const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
function plusJoursOuvres(d0, n) { const d = new Date(d0); let c = 0; while (c < n) { d.setDate(d.getDate() + 1); if (d.getDay() !== 0 && d.getDay() !== 6) c++; } return d; }
const AUJ = new Date();
const EXP = plusJoursOuvres(AUJ, 8), LMAX = plusJoursOuvres(EXP, 6);

function variante(nom, args) {
  const dest = path.join(TMP, nom);
  fs.cpSync(SITE, dest, { recursive: true, filter: (src) => !src.includes(`${path.sep}__pycache__`) });
  execFileSync("python3", [GENERER, "--sortie", dest].concat(args || []), { stdio: "pipe" });
  return dest;
}

function lireEntetes(racine) {
  const t = fs.readFileSync(path.join(racine, "_headers"), "utf8").split("\n");
  const h = {};
  let dans = false;
  for (const l of t) {
    if (/^\S/.test(l)) { dans = l.trim() === "/*"; continue; }
    const m = l.match(/^\s+([A-Za-z-]+):\s*(.+)$/);
    if (dans && m) h[m[1]] = m[2].trim();
  }
  // Servi en HTTP local : « upgrade-insecure-requests » et HSTS n'ont pas de sens ici.
  if (h["Content-Security-Policy"]) h["Content-Security-Policy"] = h["Content-Security-Policy"].replace(/;\s*upgrade-insecure-requests/, "");
  delete h["Strict-Transport-Security"];
  return h;
}
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "application/javascript", ".json": "application/json", ".svg": "image/svg+xml",
  ".png": "image/png", ".woff2": "font/woff2", ".pdf": "application/pdf", ".xml": "application/xml", ".txt": "text/plain", ".md": "text/plain" };
function servir(racine) {
  const entetes = lireEntetes(racine);
  const srv = http.createServer((req, res) => {
    let u;
    try { u = decodeURIComponent(new URL(req.url, "http://x").pathname); } catch (e) { res.writeHead(400); res.end(); return; }
    let f = path.join(racine, u);
    if (!f.startsWith(racine)) { res.writeHead(403); res.end(); return; }
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, "index.html");
    if (!fs.existsSync(f)) { res.writeHead(404, Object.assign({}, entetes, { "Content-Type": TYPES[".html"] })); res.end(fs.readFileSync(path.join(racine, "404.html"))); return; }
    res.writeHead(200, Object.assign({}, entetes, { "Content-Type": TYPES[path.extname(f)] || "application/octet-stream", "Cache-Control": "no-store" }));
    res.end(fs.readFileSync(f));
  });
  return new Promise((r) => srv.listen(0, "127.0.0.1", () => r({ srv, base: `http://127.0.0.1:${srv.address().port}`, racine })));
}

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
    await page.evaluate(() => document.querySelectorAll(".barre-achat").forEach((b) => { b.style.display = "none"; }));
  }
  await page.screenshot({ path: path.join(CAPTURES, nom), fullPage: !!complet });
}

const consentement = () => { try { localStorage.setItem("canapoil_consentement_v1", JSON.stringify({ mesure: false, publicite: false, date: Date.now(), version: 1 })); } catch (e) { /* */ } };

/* ------------------------------------------------------------ 1. parcours d'achat (variante vente) */
async function parcours(browser, BASE, format) {
  const mobile = format === "mobile";
  const ctx = await browser.newContext(mobile
    ? { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: "fr-FR", timezoneId: "Europe/Paris" }
    : { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, locale: "fr-FR", timezoneId: "Europe/Paris" });
  const page = await ctx.newPage();
  const journal = [];
  const externes = [];
  page.on("request", (r) => { if (!r.url().startsWith(BASE) && !r.url().startsWith("data:")) externes.push(r.url()); });
  surveiller(page, format, journal);

  await page.goto(BASE + "/?utm_source=tiktok&utm_content=R02", { waitUntil: "networkidle" });
  const bandeau = page.locator("#bandeau-cookies");
  ok(`[${format}] bandeau cookies affiché à la première visite`, await bandeau.isVisible());
  ok(`[${format}] bandeau « Démonstration » visible en mode demo`, await page.locator(".js-bandeau-demo").isVisible());
  const bRef = await page.locator(".js-cookies-refuser").boundingBox();
  const bAcc = await page.locator(".js-cookies-accepter").boundingBox();
  ok(`[${format}] « Tout refuser » aussi visible que « Tout accepter »`, bRef && bAcc && Math.abs(bRef.width - bAcc.width) < 2 && Math.abs(bRef.height - bAcc.height) < 2);
  const memeStyle = await page.evaluate(() => {
    const a = getComputedStyle(document.querySelector(".js-cookies-refuser")), b = getComputedStyle(document.querySelector(".js-cookies-accepter"));
    return a.backgroundColor === b.backgroundColor && a.color === b.color && a.fontSize === b.fontSize && a.fontWeight === b.fontWeight;
  });
  ok(`[${format}] boutons du bandeau de même style`, memeStyle);
  ok(`[${format}] aucun script de traceur avant consentement`, (await page.locator("script[data-traceur]").count()) === 0);
  ok(`[${format}] UTM conservés pour la visite`, (await page.evaluate(() => sessionStorage.getItem("canapoil_utm") || "")).includes("r02"));
  if (mobile) await page.screenshot({ path: path.join(CAPTURES, "bandeau-cookies-mobile.png") });
  await page.locator(".js-cookies-refuser").click();
  ok(`[${format}] refus enregistré, bandeau fermé`, !(await bandeau.isVisible()) && (await page.evaluate(() => JSON.parse(localStorage.getItem("canapoil_consentement_v1") || "{}").publicite === false)));
  await capturer(page, `accueil-${format}.png`);
  await capturer(page, `accueil-${format}-complet.png`, true);

  await page.locator(".hero__actions a.btn--primaire").click();
  await page.waitForURL("**/produits/rouleau-anti-poils-reutilisable/");
  await page.waitForLoadState("networkidle");
  const ajout = page.locator(".js-ajouter");
  ok(`[${format}] prix affiché sur la fiche`, (await page.locator(".js-prix-offre").innerText()).includes("24,90"));
  ok(`[${format}] délai avec dates affiché`, /entre le .+ et le .+/.test(await page.locator(".js-dates-livraison").first().innerText()));
  ok(`[${format}] bloc GPSR présent`, (await page.locator(".gpsr").count()) >= 1);
  ok(`[${format}] avis : état vide, aucun aggregateRating`, (await page.locator(".avis-vide").count()) === 1 && !(await page.content()).includes("aggregateRating"));
  ok(`[${format}] pluriel correct (« 2 rouleaux »)`, (await page.content()).includes("2 rouleaux") && !(await page.content()).includes("rouleaus"));
  if (mobile) {
    const box = await page.locator(".benefices li").first().boundingBox();
    ok("[mobile] premier bénéfice visible sans défiler", box && box.y + box.height <= 844, `y=${box && Math.round(box.y)}`);
  }
  await capturer(page, `produit-${format}.png`);
  await page.locator('label.offre[data-offre="grand-kit"]').click();
  ok(`[${format}] sélecteur d'offre : prix du Grand kit`, (await page.locator(".js-prix-offre").innerText()).includes("39,90"));
  await page.locator('label.offre[data-offre="rouleau-anti-poils"]').click();
  if (mobile) {
    await page.evaluate(() => window.scrollTo(0, 2200));
    await attendre(500);
    ok("[mobile] barre d'achat collante visible après défilement", await page.locator(".js-barre-achat").isVisible());
    await page.evaluate(() => window.scrollTo(0, 0));
    await attendre(300);
  }
  await capturer(page, `produit-${format}-complet.png`, true);
  await page.reload({ waitUntil: "networkidle" });

  await ajout.click();
  const tiroir = page.locator("#tiroir-panier");
  await tiroir.waitFor({ state: "visible" });
  await attendre(400);
  ok(`[${format}] tiroir ouvert après ajout`, await tiroir.isVisible());
  ok(`[${format}] compteur = 1`, (await page.locator(".js-compteur").first().innerText()).trim() === "1");
  ok(`[${format}] barre de progression vers la livraison offerte`, (await page.locator("#tiroir-panier .progression__texte").innerText()).includes("Plus que"));
  ok(`[${format}] focus dans le tiroir`, await page.evaluate(() => document.getElementById("tiroir-panier").contains(document.activeElement)));
  await page.screenshot({ path: path.join(CAPTURES, mobile ? "panier-mobile.png" : "panier-desktop.png") });
  await page.locator('#tiroir-panier [data-action="plus"]').click();
  await attendre(150);
  ok(`[${format}] quantité 2 : total 49,80 € et livraison offerte`, (await page.locator("#tiroir-panier .recap__ligne--total").innerText()).includes("49,80") && (await page.locator("#tiroir-panier .progression__texte").innerText()).includes("Livraison offerte"));
  await page.locator('#tiroir-panier [data-action="moins"]').click();
  await attendre(150);
  await page.keyboard.press("Escape");
  await attendre(400);
  ok(`[${format}] Échap ferme le tiroir`, !(await tiroir.isVisible()));

  await page.reload({ waitUntil: "networkidle" });
  ok(`[${format}] panier conservé après rechargement`, (await page.locator(".js-compteur").first().innerText()).trim() === "1");
  await page.goto(BASE + "/faq/", { waitUntil: "networkidle" });
  ok(`[${format}] panier conservé sur une autre page`, (await page.locator(".js-compteur").first().innerText()).trim() === "1");

  await page.goto(BASE + "/panier/", { waitUntil: "networkidle" });
  ok(`[${format}] page panier : 1 ligne`, (await page.locator(".panneau .ligne").count()) === 1);
  ok(`[${format}] page panier : suggestion Grand kit loyale (écart réel)`, (await page.locator(".panneau .js-suggestion").innerText()).includes("Grand kit"));
  if (mobile) await capturer(page, "panier-page-mobile.png");

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

  await page.goto(BASE + "/boutique/", { waitUntil: "networkidle" });
  await page.locator('[data-ajouter="grand-kit"]').first().click();
  await tiroir.waitFor({ state: "visible" });
  ok(`[${format}] ajout rapide d'un kit : livraison offerte`, (await page.locator("#tiroir-panier .progression__texte").innerText()).includes("Livraison offerte"));
  await page.keyboard.press("Escape");

  ok(`[${format}] aucune requête vers un domaine tiers`, externes.length === 0, externes.slice(0, 5).join(" "));
  ok(`[${format}] zéro erreur ou avertissement console / HTTP (CSP appliquée)`, journal.length === 0, journal.join(" | "));
  await ctx.close();
}

/* ------------------------------------------------------------ 2. pages (site livré) */
async function controlerPages(browser, BASE, racine, etiquette) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx.addInitScript(consentement);
  const page = await ctx.newPage();
  const journal = [];
  surveiller(page, etiquette, journal);
  const sitemap = fs.readFileSync(path.join(racine, "sitemap.xml"), "utf8");
  const pages = Array.from(sitemap.matchAll(/<loc>https:\/\/[^/]+(\/[^<]*)<\/loc>/g)).map((m) => m[1]);
  ["/panier/", "/commande/", "/merci.html", "/retractation/", "/404.html", "/liste-attente/tapis-de-fouille/"].forEach((p) => pages.push(p));
  const titres = new Map(), descriptions = new Map(), liens = new Set();
  let variables = 0;
  for (const u of pages) {
    const r = await page.goto(BASE + u, { waitUntil: "networkidle" });
    ok(`[${etiquette}] page ${u} : HTTP 200`, r && r.status() === 200, r && String(r.status()));
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
        variables: (document.documentElement.outerHTML.match(/\{\{[A-Z0-9_]+\}\}/g) || []).length,
        lancementNovembre: document.body.innerText.includes("Lancement en novembre"),
      };
    });
    variables += info.variables;
    ok(`[${etiquette}] page ${u} : un seul h1`, info.h1 === 1, String(info.h1));
    ok(`[${etiquette}] page ${u} : lang="fr"`, info.lang === "fr");
    ok(`[${etiquette}] page ${u} : title et description présents`, info.titre.length > 10 && info.desc.length > 20);
    ok(`[${etiquette}] page ${u} : canonical et Open Graph`, info.canon.startsWith("https://") && info.og);
    ok(`[${etiquette}] page ${u} : images avec attribut alt`, info.imgSansAlt === 0, String(info.imgSansAlt));
    ok(`[${etiquette}] page ${u} : champs de formulaire étiquetés`, info.champsSansLabel.length === 0, info.champsSansLabel.join(","));
    ok(`[${etiquette}] page ${u} : JSON-LD valide`, !info.ld.includes("INVALIDE"), info.ld.join(","));
    ok(`[${etiquette}] page ${u} : lien « renoncer au contrat ici » en pied de page`, info.renoncer);
    ok(`[${etiquette}] page ${u} : médiateur mentionné`, info.mediateur);
    ok(`[${etiquette}] page ${u} : aucun défilement horizontal à 390 px`, info.largeur <= 390, String(info.largeur));
    ok(`[${etiquette}] page ${u} : aucune date de lancement périmée`, !info.lancementNovembre);
    if (titres.has(info.titre)) ok(`[${etiquette}] page ${u} : title unique`, false, "doublon de " + titres.get(info.titre)); else titres.set(info.titre, u);
    if (descriptions.has(info.desc)) ok(`[${etiquette}] page ${u} : description unique`, false, "doublon de " + descriptions.get(info.desc)); else descriptions.set(info.desc, u);
    info.liens.forEach((l) => { if (l && l.startsWith("/") && !l.startsWith("//")) liens.add(l.split("#")[0]); });
    if (u.startsWith("/produits/")) ok(`[${etiquette}] page ${u} : JSON-LD Product`, info.ld.includes("Product"));
    if (u === "/faq/") ok(`[${etiquette}] FAQ : JSON-LD FAQPage`, info.ld.includes("FAQPage"));
    if (u === "/") ok(`[${etiquette}] accueil : JSON-LD Organization`, info.ld.includes("Organization"));
  }
  const casses = [];
  for (const l of liens) {
    const r = await page.request.get(BASE + l);
    if (r.status() !== 200) casses.push(`${l} (${r.status()})`);
  }
  ok(`[${etiquette}] liens internes et ressources : ${liens.size} URL testées, toutes en 200`, casses.length === 0, casses.join(", "));
  ok(`[${etiquette}] pages : zéro erreur console / HTTP (CSP appliquée)`, journal.length === 0, journal.join(" | "));
  await ctx.close();
  return variables;
}

/* ------------------------------------------------------------ 3. liste d'attente (site livré) */
async function controlerListeAttente(browser, BASE) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await ctx.addInitScript(consentement);
  const page = await ctx.newPage();
  const journal = [];
  surveiller(page, "attente", journal);
  await page.goto(BASE + "/produits/rouleau-anti-poils-reutilisable/", { waitUntil: "networkidle" });
  ok("liste d'attente : bouton d'ajout remplacé par l'inscription", (await page.locator(".js-ajouter").count()) === 0 && (await page.locator(".js-achat .js-form-inscription").count()) === 1);
  ok("liste d'attente : champ caché « produit » = rouleau", (await page.locator('.js-achat input[name="produit"]').getAttribute("value")) === "rouleau-anti-poils");
  ok("liste d'attente : aucune promesse « 1 jour ouvré » sur la fiche", !(await page.locator("main").innerText()).includes("1 jour ouvré"));
  ok("liste d'attente : panier masqué", !(await page.locator(".js-ouvrir-panier").isVisible()));
  const caseC = page.locator('.js-achat input[name="consentement"]');
  ok("liste d'attente : case de consentement non pré-cochée", (await caseC.count()) === 1 && !(await caseC.isChecked()));
  await page.locator(".js-achat input[type=email]").fill("test@exemple.fr");
  await page.locator(".js-achat button[type=submit]").click();
  ok("liste d'attente : inscription refusée sans consentement", (await page.locator(".js-achat .js-erreur").innerText()).includes("Cochez"));
  await caseC.check();
  await page.evaluate(() => document.querySelector(".js-achat").scrollIntoView({ block: "center" }));
  await page.screenshot({ path: path.join(CAPTURES, "liste-attente-mobile.png") });
  await page.locator(".js-achat button[type=submit]").click();
  ok("liste d'attente : confirmation (simulation)", (await page.locator(".js-achat .message--succes").innerText()).includes("Simulation"));
  await page.goto(BASE + "/liste-attente/tapis-de-fouille/", { waitUntil: "networkidle" });
  ok("tapis de fouille : page de liste d'attente avec produit = tapis-de-fouille", (await page.locator('input[name="produit"]').getAttribute("value")) === "tapis-de-fouille");
  ok("tapis de fouille : avertissement d'ingestion affiché", (await page.locator(".gpsr").innerText()).includes("ingestion"));
  await capturer(page, "tapis-de-fouille-mobile.png");
  await page.goto(BASE + "/commande/", { waitUntil: "networkidle" });
  ok("liste d'attente : paiement bloqué sur la page Commande", await page.locator(".js-payer").isDisabled());
  ok("liste d'attente : zéro erreur console", journal.length === 0, journal.join(" | "));
  await ctx.close();
}

/* ------------------------------------------------------------ 4. précommande : aucune promesse « 1 jour ouvré » */
async function controlerPrecommande(browser, BASE, racine) {
  // a) texte brut de toutes les pages HTML générées et des données publiques
  const fichiers = [];
  (function parcourir(d) {
    for (const f of fs.readdirSync(d)) {
      const p = path.join(d, f);
      if (["outils", "netlify", "functions", "node_modules"].includes(f)) continue;
      if (fs.statSync(p).isDirectory()) parcourir(p); else if (/\.(html|json|xml)$/.test(f)) fichiers.push(p);
    }
  })(racine);
  const fautifs = fichiers.filter((f) => fs.readFileSync(f, "utf8").includes("1 jour ouvré")).map((f) => path.relative(racine, f));
  ok(`précommande : « 1 jour ouvré » absent des ${fichiers.length} fichiers publics (pages, CGV, products.json, flux)`, fautifs.length === 0, fautifs.join(", "));
  const cat = JSON.parse(fs.readFileSync(path.join(racine, "data/products.json"), "utf8"));
  const d1 = cat.livraison.precommande.expedition_a_partir_du, d2 = cat.livraison.precommande.livraison_au_plus_tard_le;
  const FDATE = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long", year: "numeric" });
  const txt1 = FDATE.format(new Date(d1 + "T12:00:00")), txt2 = FDATE.format(new Date(d2 + "T12:00:00"));
  // b) rendu réel : fiche, tiroir, panier, commande
  for (const [format, vp] of [["mobile", { width: 390, height: 844 }], ["desktop", { width: 1440, height: 900 }]]) {
    const ctx = await browser.newContext({ viewport: vp, locale: "fr-FR", timezoneId: "Europe/Paris" });
    await ctx.addInitScript(consentement);
    const page = await ctx.newPage();
    const journal = [];
    surveiller(page, "précommande " + format, journal);
    await page.goto(BASE + "/produits/rouleau-anti-poils-reutilisable/", { waitUntil: "networkidle" });
    const corps = await page.locator("body").innerText();
    ok(`[précommande ${format}] fiche : bandeau, encart et FAQ sans « 1 jour ouvré »`, !corps.includes("1 jour ouvré"));
    ok(`[précommande ${format}] fiche : dates d'expédition et de livraison écrites`, (await page.locator(".js-encart-livraison").innerText()).includes("au plus tard le"));
    ok(`[précommande ${format}] fiche : bouton « Précommander »`, (await page.locator(".js-libelle-ajout").innerText()).trim() === "Précommander");
    ok(`[précommande ${format}] fiche : prime de lancement affichée avec sa limite`, corps.includes("dans la limite des 30 gants"));
    if (format === "mobile") await capturer(page, "precommande-produit-mobile.png");
    await page.locator(".js-ajouter").click();
    await page.locator("#tiroir-panier").waitFor({ state: "visible" });
    await page.goto(BASE + "/panier/", { waitUntil: "networkidle" });
    const panier = await page.locator("main").innerText();
    ok(`[précommande ${format}] panier : dates de précommande, aucun « 3 à 6 jours ouvrés » seul`, panier.includes(txt1) && panier.includes(txt2) && !panier.includes("1 jour ouvré"), panier.slice(0, 300));
    await page.goto(BASE + "/commande/", { waitUntil: "networkidle" });
    const cmd = await page.locator("main").innerText();
    ok(`[précommande ${format}] commande : dates de précommande affichées`, cmd.includes(txt2) && !cmd.includes("1 jour ouvré"));
    if (format === "mobile") await capturer(page, "precommande-commande-mobile.png");
    ok(`[précommande ${format}] zéro erreur console`, journal.length === 0, journal.join(" | "));
    await ctx.close();
  }
}

/* ------------------------------------------------------------ 5. production simulée et rétractation (variante vente) */
async function controlesSpeciaux(browser, BASE) {
  const configOrigine = fs.readFileSync(path.join(SITE, "assets/js/config.js"), "utf8");
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
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ url: BASE + "/merci.html?session_id=cs_test_simule0123456789" }) });
    });
    await page.goto(BASE + "/kits/grand-kit/?utm_source=pinterest&utm_content=K21", { waitUntil: "networkidle" });
    ok("production : pas de bandeau « Démonstration »", !(await page.locator(".js-bandeau-demo").isVisible()));
    await page.locator(".js-ajouter").click();
    await page.goto(BASE + "/commande/", { waitUntil: "networkidle" });
    ok("production : pas d'avertissement démo", !(await page.locator(".js-avertissement-demo").isVisible()));
    await page.locator("#cgv").check();
    await page.locator(".js-payer").click();
    await page.waitForURL("**/merci.html?session_id=*");
    await page.waitForLoadState("networkidle");
    await attendre(200);
    const cles = envoye ? Object.keys(envoye).sort().join(",") : "";
    ok("production : corps envoyé sans prix ni phase (le serveur les relit), UTM joints", envoye && cles === "cgv_acceptees,cgv_version,lignes,point_relais,utm" && JSON.stringify(envoye.lignes) === '[{"id":"grand-kit","qte":1}]' && envoye.utm.utm_content === "k21", JSON.stringify(envoye));
    ok("production : numéro de commande affiché au retour de Stripe", (await page.locator(".js-merci-numero").innerText()).includes("3456789".slice(-7)));
    ok("production : panier vidé au retour de Stripe", (await page.evaluate(() => localStorage.getItem("canapoil_panier_v1"))) === null);
    ok("production : zéro erreur console", journal.length === 0, journal.join(" | "));
    await ctx.close();
  }
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

/* ------------------------------------------------------------ programme */
(async () => {
  let browser;
  const serveurs = [];
  try {
    const livre = await servir(SITE);
    serveurs.push(livre);
    const vente = await servir(variante("vente", ["--phase", "vente", "--stock", "20"]));
    serveurs.push(vente);
    const preco = await servir(variante("precommande", ["--phase", "precommande", "--expedition", iso(EXP), "--livraison-max", iso(LMAX), "--stock", "20"]));
    serveurs.push(preco);
    // Publication refusée tant qu'il reste des variables {{...}} (correction C4)
    const pub = path.join(TMP, "publication");
    fs.cpSync(SITE, pub, { recursive: true, filter: (src) => !src.includes(`${path.sep}__pycache__`) });
    const r = spawnSync("python3", [GENERER, "--sortie", pub, "--publication"], { encoding: "utf8" });
    const phaseLivree = JSON.parse(fs.readFileSync(path.join(SITE, "data/products.json"), "utf8")).livraison.phase;
    ok(`site livré en phase « ${phaseLivree} » (liste d'attente attendue avant la porte 1)`, phaseLivree === "liste_attente");

    browser = await chromium.launch();
    await parcours(browser, vente.base, "mobile");
    await parcours(browser, vente.base, "desktop");
    const variables = await controlerPages(browser, livre.base, SITE, "livré");
    ok(`generer.py --publication refuse le site tant que ${variables > 0 ? "des variables {{…}} restent visibles" : "rien ne manque"}`,
      variables > 0 ? r.status !== 0 && /publication refusée/.test(r.stderr) : r.status === 0, (r.stderr || "").trim().slice(0, 200));
    await controlerListeAttente(browser, livre.base);
    await controlerPrecommande(browser, preco.base, preco.racine);
    await controlesSpeciaux(browser, vente.base);
  } catch (e) {
    ok("exécution du script sans exception", false, e.stack);
  }
  if (browser) await browser.close();
  serveurs.forEach((s) => s.srv.close());
  fs.rmSync(TMP, { recursive: true, force: true });
  const js = ["assets/js/app.js", "assets/js/config.js"].reduce((s, f) => s + fs.statSync(path.join(SITE, f)).size, 0);
  ok(`JavaScript total < 60 Ko (${(js / 1024).toFixed(1)} Ko)`, js < 60 * 1024);
  const echecs = resultats.filter((x) => !x.ok);
  fs.writeFileSync(path.join(CAPTURES, "rapport-verification.json"), JSON.stringify({ date: new Date().toISOString(), total: resultats.length, echecs: echecs.length, resultats }, null, 2));
  console.log(`${resultats.length - echecs.length}/${resultats.length} contrôles réussis.`);
  process.exit(echecs.length ? 1 : 0);
})();
