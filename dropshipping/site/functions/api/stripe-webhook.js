/* Cloudflare Pages Function : POST /api/stripe-webhook (même logique que netlify/functions/stripe-webhook.js). */
import coeur from "../../netlify/lib/coeur.js";

export const onRequest = coeur.cloudflare("webhook");
