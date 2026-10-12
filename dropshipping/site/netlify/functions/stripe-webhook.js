/* Netlify Function : POST /api/stripe-webhook — appelée par Stripe après un paiement.
   Vérifie la signature (STRIPE_WEBHOOK_SECRET) puis envoie la confirmation de commande
   (récapitulatif, CGV en PDF, lien « renoncer au contrat ici ») via Brevo.
   À déclarer dans Stripe : Développeurs > Webhooks > Ajouter un endpoint
   https://VOTRE-DOMAINE/api/stripe-webhook, événement checkout.session.completed. */
"use strict";
const { netlify } = require("../lib/coeur.js");

exports.handler = netlify("webhook");
