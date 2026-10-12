/* Configuration du site Canapoil côté navigateur.
   La phase de vente (liste d'attente, précommande, vente), les dates de précommande, le stock,
   le régime de TVA affiché et l'identité légale ne sont PAS ici : ils viennent de
   strategie/brand.json, recopiés dans les pages et dans /data/products.json par generer.py.
   Le serveur relit products.json : le navigateur ne peut ni choisir la phase ni dépasser le stock. */
window.CANAPOIL_CONFIG = {
  // "demo" (par défaut) : aucun appel serveur, bandeau « Démonstration » en haut de chaque page,
  //   paiement, rétractation et inscriptions simulés à l'écran.
  // "production" : appelle les fonctions serveur (/api/...). À n'activer qu'après la porte 1,
  //   avec l'identité légale remplie (generer.py --publication) et les clés saisies chez l'hébergeur.
  mode: "demo",

  // Points d'accès des fonctions serveur (Netlify ou Cloudflare Pages Functions).
  api: {
    checkout: "/api/create-checkout",
    retractation: "/api/retractation",
    inscription: "/api/inscription",
  },

  // Cloudflare Turnstile (anti-robot des formulaires d'inscription et de rétractation).
  // Clé de site publique créée dans le tableau de bord Cloudflare > Turnstile ; la clé secrète
  // va dans la variable TURNSTILE_SECRET_KEY de l'hébergeur. Vide = widget non chargé.
  turnstile: { cle_site: "" },

  // Bandeau de consentement : durée de conservation du choix (6 mois).
  consentement: { duree_jours: 182 },

  // Traceurs chargés UNIQUEMENT après consentement. Exemple :
  // publicite: [{ nom: "TikTok", src: "https://analytics.tiktok.com/i18n/pixel/events.js" }]
  // Penser à autoriser le domaine dans l'en-tête Content-Security-Policy (_headers).
  // Cloudflare Web Analytics (sans cookie) est injecté par Cloudflare Pages : rien à ajouter ici.
  traceurs: { mesure: [], publicite: [] },

  // Liens vers les comptes de la marque (laisser vide pour masquer).
  reseaux: { TikTok: "", Instagram: "", Pinterest: "", YouTube: "" },
};
