// Pipeline de rendu : scène HDR → profondeur de champ → bloom + tone mapping AgX/ACES →
// flou de mouvement → SMAA → étalonnage « caméra ». Rendu hors-ligne, image par image.
import * as THREE from 'three';
import {
  EffectComposer, RenderPass, EffectPass, BloomEffect, DepthOfFieldEffect,
  ToneMappingEffect, ToneMappingMode, SMAAEffect, SMAAPreset,
} from 'postprocessing';
import { GradeEffect, MotionBlurEffect } from './post.js';

export function createRenderer(W, H, { quality = 'final' } = {}) {
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const renderer = new THREE.WebGLRenderer({
    canvas, antialias: false, stencil: false, depth: true,
    preserveDrawingBuffer: true, powerPreference: 'high-performance',
  });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const dummyScene = new THREE.Scene();
  const dummyCam = new THREE.PerspectiveCamera(35, W / H, 0.05, 200);
  const composer = new EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType });

  const renderPass = new RenderPass(dummyScene, dummyCam);
  const dof = new DepthOfFieldEffect(dummyCam, { focusDistance: 4, focusRange: 2.5, bokehScale: 2.5, resolutionScale: 0.5 });
  const dofPass = new EffectPass(dummyCam, dof);
  const bloom = new BloomEffect({ intensity: 0.9, luminanceThreshold: 0.9, luminanceSmoothing: 0.25, mipmapBlur: true, radius: 0.72, levels: 8 });
  const tone = new ToneMappingEffect({ mode: ToneMappingMode.AGX });
  const bloomPass = new EffectPass(dummyCam, bloom, tone);
  const mblur = new MotionBlurEffect();
  const mblurPass = new EffectPass(dummyCam, mblur);
  const smaa = new SMAAEffect({ preset: SMAAPreset.HIGH });
  const smaaPass = new EffectPass(dummyCam, smaa);
  const grade = new GradeEffect();
  const gradePass = new EffectPass(dummyCam, grade);

  composer.addPass(renderPass);
  composer.addPass(dofPass);
  composer.addPass(bloomPass);
  composer.addPass(mblurPass);
  composer.addPass(smaaPass);
  composer.addPass(gradePass);

  const GRADE_DEFAULTS = {
    uExposure: 1.07, uContrast: 1.1, uSaturation: 1.2, uLift: [0.012, 0.016, 0.03], uGain: [1.02, 1.0, 0.97],
    uVignette: 0.55, uGrain: 0.045, uCA: 0.004, uDistort: 0.035, uFlash: 0, uFlashColor: [1, 1, 1], uFade: 0,
    uLeak: 0, uLeakPos: [1.1, 0.8], uLeakColor: [1.0, 0.45, 0.15],
  };
  const TONE = { agx: ToneMappingMode.AGX, aces: ToneMappingMode.ACES_FILMIC, neutral: ToneMappingMode.NEUTRAL };
  const focusTarget = new THREE.Vector3();

  return {
    canvas, renderer, composer,
    render(scene, camera, fx = {}, frameIndex = 0) {
      composer.setMainScene(scene);
      composer.setMainCamera(camera);
      dof.camera = camera;

      // Profondeur de champ (mise au point sur la cible, comme un vrai assistant caméra).
      const useDof = fx.dof && quality !== 'draft';
      dofPass.enabled = !!useDof;
      if (useDof) {
        if (fx.dof.target) { focusTarget.fromArray(fx.dof.target); dof.target = focusTarget; }
        else { dof.target = null; dof.cocMaterial.focusDistance = fx.dof.distance ?? 4; }
        dof.cocMaterial.focusRange = fx.dof.range ?? 2.0;
        dof.bokehScale = fx.dof.bokeh ?? 2.5;
      }

      bloom.intensity = fx.bloom?.intensity ?? 0.9;
      bloom.luminanceMaterial.threshold = fx.bloom?.threshold ?? 0.9;
      tone.mode = TONE[fx.tone || 'aces'];

      const d = fx.motionBlur || { dir: [0, 0], zoom: 0 };
      const blurAmt = Math.hypot(d.dir[0], d.dir[1]) + Math.abs(d.zoom || 0);
      mblurPass.enabled = blurAmt > 0.0015 && quality !== 'draft';
      mblur.uniforms.get('uDir').value.set(d.dir[0], d.dir[1]);
      mblur.uniforms.get('uZoom').value = d.zoom || 0;

      const g = { ...GRADE_DEFAULTS, ...(fx.grade || {}) };
      for (const [k, v] of Object.entries(g)) grade.set(k, v);
      grade.set('uSeed', (frameIndex % 997) * 1.618);

      composer.render(1 / 30);
    },
  };
}
