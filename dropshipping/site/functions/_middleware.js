/* Cloudflare Pages : bloque les fichiers de travail présents dans le dossier publié
   (scripts, sources des fonctions, README). Grâce à _routes.json, ce middleware ne
   s'exécute que sur ces chemins et sur /api/* : les pages statiques restent servies
   sans invocation de fonction (quota gratuit préservé). */
const INTERDITS = [/^\/outils\//, /^\/netlify\//, /^\/functions\//, /^\/README\.md$/, /^\/netlify\.toml$/, /^\/images\/README\.md$/, /^\/_routes\.json$/];

export async function onRequest({ request, next }) {
  const chemin = new URL(request.url).pathname;
  if (INTERDITS.some((r) => r.test(chemin))) return new Response("Page introuvable", { status: 404, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  return next();
}
