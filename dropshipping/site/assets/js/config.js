/* Configuration du site Canapoil — seul fichier à modifier pour passer en production.
   Les prix ne sont PAS ici : ils viennent de /data/products.json (généré depuis
   strategie/brand.json) et sont recalculés côté serveur au moment du paiement. */
window.CANAPOIL_CONFIG = {
  // "demo" : aucun appel serveur, le paiement est simulé et mène à merci.html.
  // "production" : appelle les fonctions serveur (/api/...) qui créent la session Stripe.
  mode: "demo",

  // "vente" : vente normale.
  // "precommande" : boutons « Précommander » et dates d'expédition ci-dessous.
  // "liste_attente" : aucune vente, formulaire d'inscription au lancement (avant la porte 1).
  phase: "vente",

  precommande: {
    expedition_a_partir_du: "2026-11-23", // AAAA-MM-JJ
    livraison_au_plus_tard_le: "2026-12-04", // 30 jours maximum après la commande (L216-1)
    prime: "Gant de toilettage offert aux 30 premières précommandes", // laisser "" pour masquer
  },

  // Points d'accès des fonctions serveur (Netlify ou Cloudflare Pages Functions).
  api: {
    checkout: "/api/create-checkout",
    retractation: "/api/retractation",
    inscription: "/api/inscription",
  },

  // Le délai annoncé (3 à 6 jours ouvrés) vient de products.json. Après 30 livraisons,
  // remplacer ces valeurs par le 90e centile constaté + 2 jours ouvrés.
  livraison: { delai_min: null, delai_max: null },

  // Régime de TVA : "assujetti" (prix TTC, TVA 20 % incluse) ou "franchise"
  // (« TVA non applicable, art. 293 B du CGI »).
  tva: "assujetti",

  // Bandeau de consentement : durée de conservation du choix (6 mois).
  consentement: { duree_jours: 182 },

  // Traceurs chargés UNIQUEMENT après consentement. Exemple :
  // publicite: [{ nom: "TikTok", src: "https://analytics.tiktok.com/i18n/pixel/events.js" }]
  // Penser à autoriser le domaine dans l'en-tête Content-Security-Policy (_headers).
  traceurs: { mesure: [], publicite: [] },

  // Liens vers les comptes de la marque (laisser vide pour masquer).
  reseaux: { TikTok: "", Instagram: "", Pinterest: "", YouTube: "" },
};
