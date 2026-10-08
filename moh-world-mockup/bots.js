// MOH World residents, built from Bot Crossing's bot (MIT code + CC0 body; see vendor/bot-crossing).
// This is a simplified, non-instanced version of Bot Crossing's astronauts.js: one ordinary
// SkinnedMesh per bot, posed with three's AnimationMixer. Fine for ten residents.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { helmetGeometry, visorGeometry, screenGeometry } from './vendor/bot-crossing/model.js';
import { buildFaceAtlas, FACE, FRAME_COLS, FRAME_ROWS } from './vendor/bot-crossing/faces.js';

// Where the worn parts sit on their bones, in the rig's own units (values from astronauts.js).
const P = { helmetR: .48, headUp: .40, packZ: -.3, packUp: .06, antX: .16, antY: .82, antZ: -.05, antRx: .06, antRz: -.12, lightZ: .26, lightY: .05 };

// Mood -> lamp trim + eye colour. Eyes go past 1.0 so the bloom pass picks them out.
export const LOOK = {
  working:     { trim: 0x4f9a63, eye: [0.35, 2.5, 1.15] },
  waiting:     { trim: 0x4f7ec9, eye: [0.45, 1.5, 3.0] },
  blocked:     { trim: 0xc94f4f, eye: [3.0, 0.5, 0.45] },
  celebrating: { trim: 0xc9a24f, eye: [2.9, 2.1, 0.6] },
  idle:        { trim: 0x8b8b85, eye: [1.1, 1.5, 1.7] },
  sleeping:    { trim: 0x5a5a70, eye: [0.7, 0.8, 1.4] },
};

export async function loadBotKit(url) {
  const gltf = await new GLTFLoader().loadAsync(url);
  return { gltf, atlas: buildFaceAtlas(512) };
}

/**
 * One resident. `face` is a FACE name, `clip` an animation in crew.glb, `t` how far into it
 * the pose is taken. Returns the root plus `headTop()`, the world point a speech bubble hangs from.
 */
export function makeBot(kit, { look = 'idle', face = 'idle', clip = 'Idle_A', t = 0, scale = 1.45, suit = 0xf3f1ec, pack = 0xf3f1ec, night = false }) {
  const L = LOOK[look];
  const eye = new THREE.Color(...L.eye);
  const root = SkeletonUtils.clone(kit.gltf.scene);
  const suitMat = new THREE.MeshStandardMaterial({ color: suit, roughness: .66, metalness: .04 });
  let head, chest;
  root.traverse(o => {
    if (o.isMesh) {
      o.visible = o.name !== 'Mannequin_Medium_Head';   // the helmet replaces the mannequin's head
      o.material = suitMat; o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false;
    }
    if (o.isBone && o.name === 'head') head = o;
    if (o.isBone && o.name === 'chest') chest = o;
  });

  const clipData = THREE.AnimationClip.findByName(kit.gltf.animations, clip);
  const mixer = new THREE.AnimationMixer(root);
  mixer.clipAction(clipData).play();
  mixer.setTime(t % clipData.duration);

  const R = P.helmetR;
  const worn = (geo, mat, bone, x, y, z, shadow = true) => {
    const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = shadow; bone.add(m); return m;
  };
  worn(helmetGeometry(R), new THREE.MeshStandardMaterial({ color: suit, roughness: .34, metalness: .03, vertexColors: true, envMapIntensity: .9 }), head, 0, P.headUp, 0);
  worn(screenGeometry(R), faceMaterial(kit.atlas, FACE[face], eye), head, 0, P.headUp, 0, false);
  worn(visorGeometry(R), visorMaterial(), head, 0, P.headUp, 0, false).renderOrder = 2;

  const antennaH = R * .57;
  const antGeo = new THREE.CylinderGeometry(R * .035, R * .046, antennaH, 8); antGeo.translate(0, antennaH / 2, 0);
  const tipGeo = new THREE.SphereGeometry(R * .105, 12, 8); tipGeo.translate(0, antennaH, 0);
  const ant = worn(antGeo, new THREE.MeshStandardMaterial({ color: suit, roughness: .34 }), head, P.antX, P.antY, P.antZ);
  ant.rotation.set(P.antRx, 0, P.antRz);
  const tip = new THREE.Mesh(tipGeo, new THREE.MeshBasicMaterial({ color: eye.clone().multiplyScalar(night ? 1.2 : .8) }));
  tip.position.copy(ant.position); tip.rotation.copy(ant.rotation); head.add(tip);

  worn(new RoundedBoxGeometry(R * .89, R * .98, R * .55, 3, R * .19), new THREE.MeshStandardMaterial({ color: pack, roughness: .5 }), chest, 0, P.packUp, P.packZ);
  worn(new THREE.SphereGeometry(R * .16, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(L.trim).multiplyScalar(night ? 2.2 : 1.4) }), chest, 0, P.lightY, P.lightZ, false);

  root.scale.setScalar(scale);
  root.updateMatrixWorld(true);
  const headTop = () => { const v = new THREE.Vector3(); head.localToWorld(v.set(0, P.headUp + R + .55, 0)); return v; };
  return { root, mixer, headTop };
}

// The recessed CRT face: Bot Crossing's _faceMaterial, with the per-instance attribute swapped
// for a uniform (one mesh per bot here) and the world-curve hook left out.
function faceMaterial(atlas, frame, eye) {
  const mat = new THREE.MeshBasicMaterial({ map: atlas, toneMapped: true });
  const origin = new THREE.Vector2((frame % FRAME_COLS) / FRAME_COLS, 1 - (Math.floor(frame / FRAME_COLS) + 1) / FRAME_ROWS);
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uFrameScale = { value: new THREE.Vector2(1 / FRAME_COLS, 1 / FRAME_ROWS) };
    shader.uniforms.uFrameOrigin = { value: origin };
    shader.uniforms.uEye = { value: eye };
    shader.uniforms.uGlow = { value: 1.55 };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
        varying vec2 vScreenUv;`)
      .replace('#include <uv_vertex>', `#include <uv_vertex>
        vScreenUv = uv;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
        uniform float uGlow; uniform vec2 uFrameScale; uniform vec2 uFrameOrigin; uniform vec3 uEye;
        varying vec2 vScreenUv;`)
      .replace('#include <map_fragment>', `
        vec2 tube = ( vScreenUv - 0.5 ) * 2.0;
        vec2 crtUv = 0.5 + 0.5 * tube * ( 1.0 + 0.085 * dot( tube, tube ) );
        vec2 atlasUv = clamp( crtUv, 0.003, 0.997 ) * uFrameScale + uFrameOrigin;
        float mask = texture2D( map, atlasUv ).r;
        float scanY = crtUv.y * 44.0;
        float scanDetail = 1.0 - smoothstep( 0.28, 0.5, fwidth( scanY ) );
        float raster = 0.77 - scanDetail * 0.23 * cos( scanY * 6.2831853 );
        float edge = smoothstep( 0.25, 0.5, length( vScreenUv - 0.5 ) );
        vec3 screen = vec3( 0.014, 0.031, 0.079 ) * ( 1.0 - edge * 0.48 );
        vec3 bed = screen * ( 0.74 - scanDetail * 0.26 * cos( scanY * 6.2831853 ) );
        diffuseColor.rgb = bed + uEye * mask * uGlow * raster;
        diffuseColor.a = 1.0;
      `)
      .replace('#include <color_fragment>', '');
  };
  return mat;
}

// The clear outer glass: Bot Crossing's _visorMaterial minus the curve and local-reflection hooks.
function visorMaterial() {
  const mat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: .08, metalness: 0, ior: 1.46, transparent: true, opacity: 1, depthWrite: false, envMapIntensity: 1 });
  mat.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>',
      `float facing = clamp( dot( normal, normalize( vViewPosition ) ), 0.0, 1.0 );
       float fresnel = 0.035 + 0.965 * pow( 1.0 - facing, 5.0 );
       diffuseColor.a = 2.0 * fresnel / ( 1.0 + fresnel );
       outgoingLight = reflectedLight.indirectSpecular / max( fresnel, 0.035 );
       #include <opaque_fragment>`);
  };
  return mat;
}
