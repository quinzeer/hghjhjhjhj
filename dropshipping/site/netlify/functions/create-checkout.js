/* Netlify Function : POST /api/create-checkout (réécrit vers /.netlify/functions/create-checkout).
   Crée une session Stripe Checkout hébergée par Stripe. Les prix sont recalculés côté
   serveur depuis /data/products.json ; le navigateur n'envoie que { lignes: [{ id, qte }],
   point_relais, cgv_acceptees, cgv_version, phase }.
   Variables d'environnement : STRIPE_SECRET_KEY (obligatoire), SITE_URL (recommandé),
   STRIPE_CASE_CGV="oui" (facultatif : seconde case CGV sur la page Stripe),
   ORIGINES_AUTORISEES (facultatif, liste séparée par des virgules). */
"use strict";
const { netlify } = require("../lib/coeur.js");

exports.handler = netlify("checkout");
