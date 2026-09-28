// Crée un projet vidéo à partir d'un modèle : node new_project.mjs <modèle> <dossier>
// Modèles : ls ../templates
import fs from 'node:fs';
import path from 'node:path';
const HERE = path.dirname(new URL(import.meta.url).pathname);
const [tpl, dest] = process.argv.slice(2);
const src = path.join(HERE, '..', 'templates', tpl || '');
if (!tpl || !dest || !fs.existsSync(src)) {
  console.error(`usage : node new_project.mjs <modèle> <dossier>\nmodèles : ${fs.readdirSync(path.join(HERE, '..', 'templates')).join(', ')}`);
  process.exit(1);
}
fs.mkdirSync(dest, { recursive: true });
for (const f of fs.readdirSync(src)) fs.cpSync(path.join(src, f), path.join(dest, f), { recursive: true });
console.log(`projet créé : ${path.resolve(dest)} (modèle ${tpl}) — éditer story.json puis scene.js`);
