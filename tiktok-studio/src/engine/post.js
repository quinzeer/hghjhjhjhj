// Effets de post-production « caméra réelle » : étalonnage, grain argentique, aberration
// chromatique, distorsion d'objectif, vignettage, flash, fuite de lumière, flou de mouvement.
import { Effect, EffectAttribute, BlendFunction } from 'postprocessing';
import { Uniform, Vector2, Vector3 } from 'three';

const gradeFrag = /* glsl */ `
uniform float uExposure;
uniform float uContrast;
uniform float uSaturation;
uniform vec3 uLift;
uniform vec3 uGain;
uniform float uVignette;
uniform float uGrain;
uniform float uSeed;
uniform float uCA;
uniform float uDistort;
uniform float uFlash;
uniform vec3 uFlashColor;
uniform float uFade;
uniform float uLeak;
uniform vec2 uLeakPos;
uniform vec3 uLeakColor;

float hash12(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

vec2 barrel(vec2 uv, float k) {
  vec2 d = uv - 0.5;
  d.x *= aspect;
  float r2 = dot(d, d);
  d *= 1.0 + k * r2;
  d.x /= aspect;
  return d + 0.5;
}

void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec2 duv = barrel(uv, uDistort);
  vec2 dir = (duv - 0.5);
  vec3 c;
  // Aberration chromatique radiale (plus forte sur les bords, comme un vrai objectif).
  float caAmt = uCA * dot(dir, dir) * 4.0;
  c.r = texture2D(inputBuffer, duv - dir * caAmt).r;
  c.g = texture2D(inputBuffer, duv).g;
  c.b = texture2D(inputBuffer, duv + dir * caAmt).b;

  // Passage en espace « affichage » pour un étalonnage prévisible.
  c = pow(max(c, 0.0), vec3(1.0 / 2.2));
  c *= uExposure;
  c = (c - 0.5) * uContrast + 0.5;
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(l), c, uSaturation);
  // Split-toning : ombres (lift) teintées, hautes lumières (gain) chaudes.
  c = c * uGain + uLift * (1.0 - c);
  c = clamp(c, 0.0, 1.0);

  // Fuite de lumière (light leak) additive, douce.
  if (uLeak > 0.001) {
    vec2 lp = uv - uLeakPos; lp.x *= aspect;
    float lk = exp(-dot(lp, lp) * 3.0);
    c += uLeakColor * lk * uLeak;
  }

  // Vignettage optique.
  vec2 vd = uv - 0.5; vd.x *= aspect * 0.9;
  float vig = smoothstep(0.95, 0.25, length(vd));
  c *= mix(1.0, vig, uVignette);

  // Grain argentique pondéré par la luminance (plus visible dans les tons moyens).
  vec2 px = uv * resolution;
  float g1 = hash12(px + uSeed * 17.13);
  float g2 = hash12(px * 0.5 + uSeed * 3.71);
  float grain = (g1 + g2) - 1.0;
  float lw = 1.0 - abs(l - 0.45) * 1.4;
  c += grain * uGrain * clamp(lw, 0.25, 1.0);

  c = mix(c, uFlashColor, clamp(uFlash, 0.0, 1.0));
  c *= (1.0 - uFade);
  c = pow(max(c, 0.0), vec3(2.2));
  outputColor = vec4(c, inputColor.a);
}
`;

export class GradeEffect extends Effect {
  constructor() {
    super('GradeEffect', gradeFrag, {
      blendFunction: BlendFunction.SRC,
      attributes: EffectAttribute.CONVOLUTION,
      uniforms: new Map([
        ['uExposure', new Uniform(1.0)],
        ['uContrast', new Uniform(1.08)],
        ['uSaturation', new Uniform(1.12)],
        ['uLift', new Uniform(new Vector3(0.012, 0.016, 0.03))],
        ['uGain', new Uniform(new Vector3(1.02, 1.0, 0.97))],
        ['uVignette', new Uniform(0.55)],
        ['uGrain', new Uniform(0.045)],
        ['uSeed', new Uniform(0)],
        ['uCA', new Uniform(0.004)],
        ['uDistort', new Uniform(0.035)],
        ['uFlash', new Uniform(0)],
        ['uFlashColor', new Uniform(new Vector3(1, 1, 1))],
        ['uFade', new Uniform(0)],
        ['uLeak', new Uniform(0)],
        ['uLeakPos', new Uniform(new Vector2(1.1, 0.8))],
        ['uLeakColor', new Uniform(new Vector3(1.0, 0.45, 0.15))],
      ]),
    });
  }
  set(name, v) {
    const u = this.uniforms.get(name);
    if (!u) return;
    if (u.value && u.value.isVector3 && Array.isArray(v)) u.value.set(v[0], v[1], v[2]);
    else if (u.value && u.value.isVector2 && Array.isArray(v)) u.value.set(v[0], v[1]);
    else u.value = v;
  }
}

const blurFrag = /* glsl */ `
uniform vec2 uDir;
uniform float uZoom;
uniform vec2 uCenter;
void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec3 acc = vec3(0.0);
  float wsum = 0.0;
  for (int i = 0; i < 18; i++) {
    float t = float(i) / 17.0 - 0.5;
    vec2 o = uDir * t + (uv - uCenter) * uZoom * t;
    float w = 1.0 - abs(t);
    acc += texture2D(inputBuffer, uv + o).rgb * w;
    wsum += w;
  }
  outputColor = vec4(acc / wsum, inputColor.a);
}
`;

// Flou de mouvement d'obturateur (180°) : directionnel (whip pan) + radial (zoom punch).
export class MotionBlurEffect extends Effect {
  constructor() {
    super('MotionBlurEffect', blurFrag, {
      blendFunction: BlendFunction.SRC,
      attributes: EffectAttribute.CONVOLUTION,
      uniforms: new Map([
        ['uDir', new Uniform(new Vector2(0, 0))],
        ['uZoom', new Uniform(0)],
        ['uCenter', new Uniform(new Vector2(0.5, 0.5))],
      ]),
    });
  }
}
