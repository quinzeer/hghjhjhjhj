/* Cloudflare Pages Function : POST /api/retractation.
   Même logique que netlify/functions/retractation.js (fichier partagé netlify/lib/coeur.js).
   Variables d'environnement à déclarer dans Cloudflare Pages > Settings > Variables and Secrets. */
import coeur from "../../netlify/lib/coeur.js";

// Toutes les méthodes passent par le même point d'entrée (POST, OPTIONS pour CORS, 405 sinon).
export const onRequest = coeur.cloudflare("retractation");
