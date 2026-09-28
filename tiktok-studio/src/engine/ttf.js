// Conversion TTF → police Three.js (typeface) avec opentype.js installé localement
// (le TTFLoader de three importe opentype depuis un CDN, inaccessible en rendu hors-ligne).
import opentype from 'opentype.js';
import { Font } from 'three/examples/jsm/loaders/FontLoader.js';

export async function loadFont3D(url) {
  const buf = await (await fetch(url)).arrayBuffer();
  const font = opentype.parse(buf);
  const round = Math.round;
  const scale = 100000 / ((font.unitsPerEm || 2048) * 72);
  const glyphs = {};
  const map = font.encoding.cmap.glyphIndexMap;
  for (const unicode of Object.keys(map)) {
    const glyph = font.glyphs.get(map[unicode]);
    const token = { ha: round(glyph.advanceWidth * scale), x_min: round((glyph.xMin || 0) * scale), x_max: round((glyph.xMax || 0) * scale), o: '' };
    for (const c of glyph.path.commands) {
      const type = c.type.toLowerCase() === 'c' ? 'b' : c.type.toLowerCase();
      token.o += type + ' ';
      if (c.x !== undefined) token.o += round(c.x * scale) + ' ' + round(c.y * scale) + ' ';
      if (c.x1 !== undefined) token.o += round(c.x1 * scale) + ' ' + round(c.y1 * scale) + ' ';
      if (c.x2 !== undefined) token.o += round(c.x2 * scale) + ' ' + round(c.y2 * scale) + ' ';
    }
    glyphs[String.fromCodePoint(parseInt(unicode, 10))] = token;
  }
  return new Font({
    glyphs,
    familyName: font.getEnglishName('fullName'),
    ascender: round(font.ascender * scale),
    descender: round(font.descender * scale),
    underlinePosition: font.tables.post.underlinePosition,
    underlineThickness: font.tables.post.underlineThickness,
    boundingBox: { xMin: font.tables.head.xMin, xMax: font.tables.head.xMax, yMin: font.tables.head.yMin, yMax: font.tables.head.yMax },
    resolution: 1000,
  });
}
