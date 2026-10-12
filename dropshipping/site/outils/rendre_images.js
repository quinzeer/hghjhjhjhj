/* Rend les images PNG dérivées des illustrations SVG (Playwright, Chromium local) :
   - images/produits/<slug>/principale.png et images/kits/<slug>/principale.png (1200 × 900),
     utilisées par Stripe, le JSON-LD Product, le flux Google et le CSV Shopify ;
   - images/og/*.png (1200 × 630) pour les partages (Open Graph) ;
   - images/og/logo.png (512 × 512) ;
   - documents/cgv-canapoil.pdf (CGV imprimables jointes à l'e-mail de confirmation).
   Usage : NODE_PATH="$(npm root -g)" node site/outils/rendre_images.js
   À relancer après generer.py si les illustrations ou les prix changent.
   Quand de vraies photos existent, remplacez simplement principale.png par la photo. */
const path = require("path");
const fs = require("fs");
const os = require("os");
const { chromium } = require("playwright");

const SITE = path.resolve(__dirname, "..");
const cat = JSON.parse(fs.readFileSync(path.join(SITE, "data/products.json"), "utf8"));
const url = (rel) => "file://" + path.join(SITE, rel.replace(/^\//, ""));
const euros = (v) => (Number.isInteger(v) ? String(v) : v.toFixed(2).replace(".", ",")) + " €";

const polices = `
@font-face{font-family:"Fraunces";src:url("${url("/assets/fonts/fraunces-latin.woff2")}") format("woff2");font-weight:100 900}
@font-face{font-family:"DM Sans";src:url("${url("/assets/fonts/dm-sans-latin.woff2")}") format("woff2");font-weight:100 1000}
*{margin:0;box-sizing:border-box}body{font-family:"DM Sans";color:#2B211B}`;

function og(item) {
  const img = item.images[0];
  const sous = item.type === "kit"
    ? `${euros(item.economie_ttc)} de moins que séparément${item.livraison_offerte ? " · livraison offerte" : ""}`
    : "Testé sur de vrais tissus · expédié depuis la France";
  return `<html><head><style>${polices}
  body{width:1200px;height:630px;background:#FAF5EE;display:grid;grid-template-columns:620px 1fr;align-items:center}
  .v{height:630px;background:#fff;display:flex;align-items:center;justify-content:center}.v img{width:620px;height:465px}
  .t{padding:56px}.logo{font-family:Fraunces;font-weight:700;font-size:44px;color:#B4492A;margin-bottom:28px}
  h1{font-family:Fraunces;font-weight:700;font-size:50px;line-height:1.08;margin-bottom:20px}
  .p{font-size:40px;font-weight:700;margin-bottom:14px}.s{font-size:24px;color:#6A5B50;line-height:1.35}</style></head>
  <body><div class="v"><img src="${url(img.src)}"></div><div class="t"><div class="logo">canapoil</div><h1>${item.nom}</h1><div class="p">${euros(item.prix_ttc)} TTC</div><div class="s">${sous}</div></div></body></html>`;
}

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: 1 });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "canapoil-"));
  const ecrire = async (html, w, h, sortie) => {
    await p.setViewportSize({ width: w, height: h });
    const f = path.join(tmp, "rendu.html");
    fs.writeFileSync(f, html);
    await p.goto("file://" + f, { waitUntil: "load" });
    await p.evaluate(() => document.fonts.ready);
    fs.mkdirSync(path.dirname(sortie), { recursive: true });
    await p.screenshot({ path: sortie, type: "png" });
  };
  for (const it of cat.produits.concat(cat.kits)) {
    const src = it.images[0].src;
    const cible = path.join(SITE, it.image_produit_png.replace(/^\//, ""));
    if (src.endsWith(".svg")) {
      await ecrire(`<html><head><style>*{margin:0}</style></head><body><img src="${url(src)}" width="1200" height="900"></body></html>`, 1200, 900, cible);
    }
    await ecrire(og(it), 1200, 630, path.join(SITE, it.image_partage.replace(/^\//, "")));
  }
  await ecrire(`<html><head><style>${polices}
    body{width:1200px;height:630px;background:#FAF5EE;display:grid;grid-template-columns:1fr 600px;align-items:center}
    .t{padding:0 40px 0 64px}.logo{font-family:Fraunces;font-weight:700;font-size:48px;color:#B4492A;margin-bottom:26px}
    h1{font-family:Fraunces;font-weight:700;font-size:54px;line-height:1.08;margin-bottom:22px}h1 em{color:#B4492A}
    .s{font-size:24px;color:#6A5B50;line-height:1.4}img{width:600px;height:450px}</style></head>
    <body><div class="t"><div class="logo">canapoil</div><h1>Les câlins sur le canapé, <em>les poils à la poubelle.</em></h1><div class="s">Rouleau anti-poils réutilisable · expédié depuis la France</div></div><img src="${url("/images/illustrations/accueil-canape.svg")}"></body></html>`,
    1200, 630, path.join(SITE, "images/og/accueil.png"));
  await ecrire(`<html><head><style>${polices}body{width:512px;height:512px;background:#FAF5EE;display:flex;align-items:center;justify-content:center}
    .l{font-family:Fraunces;font-weight:700;font-size:96px;color:#B4492A;letter-spacing:-2px}</style></head><body><div class="l">canapoil</div></body></html>`,
    512, 512, path.join(SITE, "images/og/logo.png"));
  // CGV en PDF (jointes à l'e-mail de confirmation de commande)
  await p.goto(url("/documents/cgv.html"), { waitUntil: "load" });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.join(SITE, "documents/cgv-canapoil.pdf"), format: "A4", printBackground: true });
  await b.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log("Images PNG rendues.");
})();
