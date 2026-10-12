/* Netlify Function : POST /api/inscription — liste d'attente et e-mails, double opt-in Brevo.
   Variables : BREVO_API_KEY, BREVO_LISTE_ID, BREVO_TEMPLATE_DOI, SITE_URL. */
"use strict";
const { netlify } = require("../lib/coeur.js");

exports.handler = netlify("inscription");
