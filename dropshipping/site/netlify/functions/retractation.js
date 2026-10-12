/* Netlify Function : POST /api/retractation — fonctionnalité « renoncer au contrat ici ».
   Envoie l'accusé de réception horodaté au client (copie cachée au service client) via Brevo.
   Variables : BREVO_API_KEY, EMAIL_EXPEDITEUR (expéditeur validé dans Brevo),
   EMAIL_SERVICE_CLIENT, NOM_EXPEDITEUR (facultatif, « Canapoil » par défaut). */
"use strict";
const { netlify } = require("../lib/coeur.js");

exports.handler = netlify("retractation");
