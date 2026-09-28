// Sol réfléchissant à réflexions floues (béton ciré / résine de plateau TV).
// Réflexion planaire rendue à mi-résolution, floutée (Kawase), puis mélangée selon la rugosité
// et l'effet Fresnel dans un MeshStandardMaterial PBR.
import * as THREE from 'three';
import { KawaseBlurPass, KernelSize } from 'postprocessing';

export class ReflectiveFloor extends THREE.Mesh {
  constructor({ size = 60, resolution = 540, aspect = 9 / 16, color = 0x0b0b0e, roughness = 0.42,
    strength = 0.9, roughnessMap = null, normalMap = null, normalScale = 0.25, repeat = 8 } = {}) {
    const geo = new THREE.PlaneGeometry(size, size);
    const mat = new THREE.MeshStandardMaterial({ color, roughness, metalness: 0.0 });
    if (roughnessMap) { mat.roughnessMap = roughnessMap; roughnessMap.repeat.set(repeat, repeat); roughnessMap.wrapS = roughnessMap.wrapT = THREE.RepeatWrapping; }
    if (normalMap) { mat.normalMap = normalMap; mat.normalScale.set(normalScale, normalScale); normalMap.repeat.set(repeat, repeat); normalMap.wrapS = normalMap.wrapT = THREE.RepeatWrapping; }
    super(geo, mat);
    this.rotation.x = -Math.PI / 2;
    this.receiveShadow = true;

    const w = resolution, h = Math.round(resolution / aspect);
    this.rtSharp = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType });
    this.rtBlur = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType });
    this.blur = new KawaseBlurPass({ kernelSize: KernelSize.LARGE, resolutionScale: 0.5 });
    this.blur.setSize(w, h);
    this.textureMatrix = new THREE.Matrix4();
    this.reflCam = new THREE.PerspectiveCamera();
    this.strength = strength;

    const uniforms = {
      tReflSharp: { value: this.rtSharp.texture },
      tReflBlur: { value: this.rtBlur.texture },
      uTexMatrix: { value: this.textureMatrix },
      uReflStrength: { value: strength },
    };
    this.reflUniforms = uniforms;
    mat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, uniforms);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nuniform mat4 uTexMatrix;\nvarying vec4 vReflUv;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nvReflUv = uTexMatrix * vec4(position, 1.0);');
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform sampler2D tReflSharp;\nuniform sampler2D tReflBlur;\nuniform float uReflStrength;\nvarying vec4 vReflUv;')
        .replace('#include <opaque_fragment>', `
          {
            vec4 ruv = vReflUv;
            ruv.xy += normal.xy * 0.012 * ruv.w;
            vec3 rs = texture2DProj(tReflSharp, ruv).rgb;
            vec3 rb = texture2DProj(tReflBlur, ruv).rgb;
            float rgh = clamp(roughnessFactor, 0.0, 1.0);
            vec3 refl = mix(rs, rb, smoothstep(0.08, 0.5, rgh));
            float ndv = clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0);
            float fres = 0.04 + 0.96 * pow(1.0 - ndv, 5.0);
            outgoingLight += refl * uReflStrength * mix(0.18, 1.0, fres) * (1.0 - rgh * 0.6);
          }
          #include <opaque_fragment>`);
    };
  }

  update(renderer, scene, camera) {
    const reflCam = this.reflCam;
    const normal = new THREE.Vector3(0, 1, 0);
    const pos = new THREE.Vector3().setFromMatrixPosition(this.matrixWorld);
    const camPos = new THREE.Vector3().setFromMatrixPosition(camera.matrixWorld);
    const rot = new THREE.Matrix4().extractRotation(camera.matrixWorld);
    const view = new THREE.Vector3().subVectors(pos, camPos);
    if (view.dot(normal) > 0) return;
    view.reflect(normal).negate().add(pos);
    const look = new THREE.Vector3(0, 0, -1).applyMatrix4(rot).add(camPos);
    const target = new THREE.Vector3().subVectors(pos, look).reflect(normal).negate().add(pos);
    reflCam.position.copy(view);
    reflCam.up.set(0, 1, 0).applyMatrix4(rot).reflect(normal);
    reflCam.lookAt(target);
    reflCam.far = camera.far; reflCam.near = camera.near;
    reflCam.updateMatrixWorld();
    reflCam.projectionMatrix.copy(camera.projectionMatrix);

    this.textureMatrix.set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1);
    this.textureMatrix.multiply(reflCam.projectionMatrix).multiply(reflCam.matrixWorldInverse).multiply(this.matrixWorld);

    // Plan de coupe oblique (Lengyel) : rien sous le sol n'apparaît dans le reflet.
    const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(normal, pos).applyMatrix4(reflCam.matrixWorldInverse);
    const clip = new THREE.Vector4(plane.normal.x, plane.normal.y, plane.normal.z, plane.constant);
    const p = reflCam.projectionMatrix.elements;
    const q = new THREE.Vector4((Math.sign(clip.x) + p[8]) / p[0], (Math.sign(clip.y) + p[9]) / p[5], -1, (1 + p[10]) / p[14]);
    clip.multiplyScalar(2 / clip.dot(q));
    p[2] = clip.x; p[6] = clip.y; p[10] = clip.z + 1 - 0.003; p[14] = clip.w;

    this.visible = false;
    const prevRT = renderer.getRenderTarget();
    renderer.setRenderTarget(this.rtSharp);
    renderer.clear();
    renderer.render(scene, reflCam);
    this.blur.render(renderer, this.rtSharp, this.rtBlur);
    renderer.setRenderTarget(prevRT);
    this.visible = true;
  }
}
