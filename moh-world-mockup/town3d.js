// MOH World — rough 3D mockup (v3: modern buildings + Bot Crossing bots). Fake data, fixed 1600x900 frame.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { createTiltShift } from './vendor/bot-crossing/tiltshift.js';
import { OcclusionPass } from './vendor/bot-crossing/occlusion.js';
import { loadBotKit, makeBot } from './bots.js';

const q = new URLSearchParams(location.search);
const phaseName = q.get('phase') || 'day';
const panelName = q.get('panel') || '';
const W = 1600, H = 900;

// ---------- time of day (the real app blends these minute by minute) ----------
const PH = {
  dawn:  { label: 'Dawn', icon: 'sun', time: [6, 40],
    sky: [[0, '#3E4A8C'], [.55, '#C98AA6'], [1, '#FCD39C']], disc: { x: .1, y: .5, r: 38, c: '#FFC88F' },
    sun: { dir: [-60, 26, 60], color: '#ffb487', int: 2.3 }, hemi: ['#e0bfd4', '#6a5a6e', .45], env: .16,
    cloud: '#f7cdd6', lit: .12, lamps: true, stars: .15, bloom: [.3, .3, .95], dark: false },
  day:   { label: 'Day', icon: 'sun', time: [10, 24],
    sky: [[0, '#4C9BE6'], [.6, '#8CC8F2'], [1, '#D4EEFB']], disc: { x: .86, y: .14, r: 42, c: '#FFE69A' },
    sun: { dir: [50, 80, 30], color: '#fff4e2', int: 2.5 }, hemi: ['#dcecff', '#8fae7f', .45], env: .22,
    cloud: '#ffffff', lit: 0, lamps: false, stars: 0, bloom: [.1, .3, 1.0], dark: false },
  dusk:  { label: 'Dusk', icon: 'sun', time: [18, 35],
    sky: [[0, '#232A5C'], [.45, '#7A4C86'], [.78, '#E9826A'], [1, '#F9C77E']], disc: { x: .92, y: .52, r: 46, c: '#FF9E62' },
    sun: { dir: [70, 18, -55], color: '#ff9a5c', int: 1.9 }, hemi: ['#9a7aac', '#3a2f45', .45], env: .1,
    cloud: '#f2a988', lit: .35, lamps: true, stars: .3, bloom: [.42, .32, .93], dark: true },
  night: { label: 'Night', icon: 'moon', time: [21, 40],
    sky: [[0, '#050A1C'], [.55, '#0D1838'], [1, '#1C2B57']], moon: { x: .84, y: .16, r: 30 },
    sun: { dir: [-35, 70, -45], color: '#a9bcff', int: .5 }, hemi: ['#3d4d85', '#0a0f20', .32], env: .04,
    cloud: '#3a4670', lit: .45, lamps: true, stars: 1, bloom: [.5, .35, .92], dark: true },
};
const P = PH[phaseName];
const night = P.lamps;
if (P.dark) document.getElementById('stage').classList.add('dark');
const hash = i => { const s = Math.sin(i * 12.9898 + 4.1414) * 43758.5453; return s - Math.floor(s); };

// ---------- renderer, scene, camera ----------
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('gl'), antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.NeutralToneMapping;

const scene = new THREE.Scene();
scene.background = skyTexture();
// soft "studio" reflections, generated in code (no image files): makes glass and white walls look clean
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), .04).texture;
scene.environmentIntensity = P.env;

const camera = new THREE.PerspectiveCamera(30, W / H, 1, 1000);
const CAMS = { wide: [[122, 108, 122], [-3, 3, -3]], close: [[92, 62, 92], [-2, 5, -2]], hero: [[25, 11.5, 33], [3.2, 3.4, 5.5]] };
const [camPos, camAt] = CAMS[q.get('cam') || 'wide'];
camera.position.set(...camPos);
const target = new THREE.Vector3(...camAt);
camera.lookAt(target);

scene.add(new THREE.HemisphereLight(P.hemi[0], P.hemi[1], P.hemi[2]));
const sun = new THREE.DirectionalLight(P.sun.color, P.sun.int);
sun.position.set(...P.sun.dir).normalize().multiplyScalar(150);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -75, right: 75, top: 75, bottom: -75, near: 10, far: 340 });
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.04;
sun.shadow.radius = 3;
scene.add(sun, sun.target);

// ---------- palette + modelling helpers ----------
const WHITE = '#f5f4f0', CONCRETE = '#e2e0da', WOOD = '#c99b6d', DARK = '#2f3540', CORE = '#5a6573', NAVY = '#2f4f86';
const mats = new Map();
function mat(color, extra = {}) {
  const key = color + JSON.stringify(extra);
  if (!mats.has(key)) mats.set(key, new THREE.MeshStandardMaterial({ color, roughness: .75, metalness: 0, ...extra }));
  return mats.get(key);
}
const glow = (color, emissive, i = 2) => new THREE.MeshStandardMaterial({ color, emissive, emissiveIntensity: i });
function add(geo, material, x, y, z, parent = scene) {
  const m = new THREE.Mesh(geo, typeof material === 'string' ? mat(material) : material);
  m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; parent.add(m); return m;
}
const box = (w, h, d, c, x, y, z, p) => add(new THREE.BoxGeometry(w, h, d), c, x, y + h / 2, z, p);
const rbox = (w, h, d, c, x, y, z, r = .18) => add(new RoundedBoxGeometry(w, h, d, 3, r), c, x, y + h / 2, z);
const cyl = (rt, rb, h, c, x, y, z, seg = 32, p) => add(new THREE.CylinderGeometry(rt, rb, h, seg), c, x, y + h / 2, z, p);
const sph = (r, c, x, y, z, seg = 24, p) => add(new THREE.SphereGeometry(r, seg, Math.max(8, seg / 2)), c, x, y, z, p);

// glass: light and reflective by day, dark at dusk/night, some panes lit (they glow through the bloom pass)
const glassDay = new THREE.MeshStandardMaterial({ color: '#5f97c2', metalness: .35, roughness: .12 });
const glassDark = new THREE.MeshStandardMaterial({ color: '#2b3650', metalness: .4, roughness: .15 });
const glassLit = glow('#ffe6b0', '#ffc46a', 1.3);
let seed = 0;
const glassMat = () => (P.lit && hash(1000 + seed++) < P.lit) ? glassLit : P.lit ? glassDark : glassDay;

// a curtain wall: glass panes in a grid with slim frames, on the +z (front) or +x (side) face of a block
function glassWall(b, face, y0, floors, fh, bays, frame = '#e9ebee', paneH = fh - .3) {
  const span = face === 'z' ? b.w : b.d, bw = span / bays;
  const at = (t, y, off) => face === 'z' ? [b.x + t, y, b.z + b.d / 2 + off] : [b.x + b.w / 2 + off, y, b.z - t];
  for (let f = 0; f < floors; f++) for (let i = 0; i < bays; i++) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(bw - .12, paneH), glassMat());
    m.position.set(...at(-span / 2 + bw * (i + .5), y0 + fh * (f + .5), .03));
    if (face === 'x') m.rotation.y = Math.PI / 2;
    m.receiveShadow = true; scene.add(m);
  }
  const H = floors * fh;
  for (let i = 0; i <= bays; i++) add(new THREE.BoxGeometry(.1, H, .1), frame, ...at(-span / 2 + bw * i, y0 + H / 2, .06)).castShadow = false;
  for (let f = 0; f <= floors; f++) {
    add(face === 'z' ? new THREE.BoxGeometry(span, .14, .12) : new THREE.BoxGeometry(.12, .14, span), frame, ...at(0, y0 + f * fh, .06)).castShadow = false;
  }
}
function clockFace(x, y, z, r, face) {
  const [h, m] = P.time, ha = ((h % 12) + m / 60) * Math.PI / 6, ma = m * Math.PI / 30;
  const g = new THREE.Group(); g.position.set(x, y, z); if (face === 'x') g.rotation.y = Math.PI / 2; scene.add(g);
  add(new THREE.CircleGeometry(r, 40), night ? glow('#fff5dc', '#ffe6b0', 1.2) : mat('#ffffff'), 0, 0, .02, g).castShadow = false;
  add(new THREE.RingGeometry(r, r + .12, 40), DARK, 0, 0, .03, g).castShadow = false;
  for (const [len, wd, ang] of [[r * .5, .14, ha], [r * .8, .09, ma]]) {
    const geo = new THREE.BoxGeometry(wd, len, .04); geo.translate(0, len / 2, 0);
    const hand = add(geo, DARK, 0, 0, .06, g); hand.rotation.z = -ang; hand.castShadow = false;
  }
}

// ---------- the island (an architectural-model base) ----------
const S = 42, C = 28.25, BASE = .35;
{
  const side = mat('#e6dfd2'), grass = mat('#9fcf86'), under = mat('#d6cebf');
  add(new RoundedBoxGeometry(2 * S, 3, 2 * S, 2, .4), [side, side, grass, under, side, side], 0, -1.5, 0);
  rbox(2 * S - 4, 3, 2 * S - 4, '#d9d1c3', 0, -5.6, 0, .4);
  rbox(2 * S - 10, 3, 2 * S - 10, '#cbc2b3', 0, -8.2, 0, .4);
  for (const k of [-13, 13]) { box(2 * S - .8, .06, 5, '#545b67', 0, 0, k); box(5, .07, 2 * S - .8, '#545b67', k, 0, 0); }
  for (let t = -S + 2; t < S; t += 4) {
    if (Math.abs(t - 13) < 4 || Math.abs(t + 13) < 4 || Math.abs(t) < 3.5) continue;
    for (const k of [-13, 13]) { box(2, .02, .2, '#f1f1ee', t, .07, k); box(.2, .02, 2, '#f1f1ee', k, .08, t); }
  }
  // zebra crossings on all four sides of the central plaza
  for (const k of [-13, 13]) for (let s = -2; s <= 2; s++) {
    box(3, .02, .45, '#f4f4f1', 0, .08, k + s * .9); box(.45, .02, 3, '#f4f4f1', k + s * .9, .09, 0);
  }
  const spans = [[-S + 1, -15.5], [-10.5, 10.5], [15.5, S - 1]];
  for (const [x0, x1] of spans) for (const [z0, z1] of spans) {
    const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, sx = x1 - x0, sz = z1 - z0, centre = cx === 0 && cz === 0;
    rbox(sx, .3, sz, '#f1eee8', cx, 0, cz, .1);
    rbox(sx - 2.4, .34, sz - 2.4, centre ? '#e8e3d9' : '#a3d28a', cx, 0, cz, .1);
  }
}

// plot kerbs: a dashed accent-coloured light strip round each block, faint by day, lit at night
{
  const spans = [[-S + 1, -15.5], [-10.5, 10.5], [15.5, S - 1]];
  const ACCENT_GRID = { '0,0': '#7f98b5', '1,0': '#e8963f', '2,0': '#9b7fd1', '0,1': '#2a9d8f', '1,1': '#8b6fd1', '2,1': '#4a7bd0', '0,2': '#2f80ed', '2,2': '#e07a5f' };
  const kerbMat = new Map();
  const km = c => { if (!kerbMat.has(c)) kerbMat.set(c, glow(c, c, night ? 2.4 : .35)); return kerbMat.get(c); };
  spans.forEach(([x0, x1], i) => spans.forEach(([z0, z1], j) => {
    const a = x0 + 1.2, b = x1 - 1.2, c = z0 + 1.2, d = z1 - 1.2;
    const colourAt = x => ACCENT_GRID[`${i},${j}`] || (x < .5 ? '#d9534f' : '#4e9a5b');   // food block: Kitchen red | Market green
    for (let x = a + .8; x < b - .4; x += 1.6) for (const z of [c, d]) add(new THREE.BoxGeometry(1, .07, .16), km(colourAt(x)), x, .38, z).castShadow = false;
    for (let z = c + .8; z < d - .4; z += 1.6) for (const x of [a, b]) add(new THREE.BoxGeometry(.16, .07, 1), km(colourAt(x)), x, .38, z).castShadow = false;
  }));
}

// ---------- props ----------
function tree(x, z, s = 1, kind = hash(x * 7 + z) > .5 ? 'round' : 'cypress') {
  cyl(.12 * s, .16 * s, 1.7 * s, '#8b6b4f', x, BASE, z, 8);
  if (kind === 'cypress') add(new THREE.CapsuleGeometry(.85 * s, 2.6 * s, 6, 16), '#5f9f5b', x, BASE + 3.4 * s, z);
  else sph(1.7 * s, '#82c06f', x, BASE + 3 * s, z);
}
const LAMPS = [[-10, -10], [10, -10], [-10, 10], [10, 10], [-16.2, -16.2], [16.2, -16.2], [-16.2, 16.2], [16.2, 16.2]];
function lamp(x, z) {
  cyl(.08, .1, 4.4, DARK, x, BASE, z, 10);
  box(1.3, .14, .32, DARK, x + .45, BASE + 4.4, z + .45).rotation.y = -Math.PI / 4;
  const led = box(1.1, .05, .22, night ? glow('#fff4d6', '#ffdca0', 2.4) : mat('#f2f2ee'), x + .45, BASE + 4.33, z + .45);
  led.rotation.y = -Math.PI / 4; led.castShadow = false;
  if (night) { const l = new THREE.PointLight('#ffd89a', 26, 16, 2); l.position.set(x + .5, BASE + 4.1, z + .5); scene.add(l); }
}
for (const [x, z] of LAMPS) lamp(x, z);
function cloud(x, y, z, s) {
  const m = new THREE.MeshStandardMaterial({ color: P.cloud, roughness: 1, transparent: true, opacity: night ? .5 : .92 });
  for (const [dx, dy, dz, r] of [[0, 0, 0, 3.2], [3.4, -.6, .5, 2.4], [-3.2, -.8, -.3, 2.2], [1, 1.6, -.4, 2.3]]) {
    add(new THREE.SphereGeometry(r * s, 24, 16), m, x + dx * s, y + dy * s, z + dz * s).castShadow = false;
  }
}
cloud(-38, 34, -58, 1.3); cloud(52, 30, -30, 1); cloud(-66, 22, 6, .9);
const water = new THREE.MeshStandardMaterial({ color: '#7fc3e4', metalness: .2, roughness: .05 });

// ---------- the ten buildings ----------
const B = {};   // id -> { name, color, label:[x,y,z], ring:[x,z,r], agent }

// Town Hall: glass ground floor, floating white volume, slim clock tower, reflecting pool
{
  const z0 = -3.5;
  box(15.6, 3.2, 8.6, CORE, 0, BASE, z0);
  glassWall({ x: 0, z: z0, w: 15.6, d: 8.6 }, 'z', BASE, 1, 3.2, 8); glassWall({ x: 0, z: z0, w: 15.6, d: 8.6 }, 'x', BASE, 1, 3.2, 5);
  rbox(17.6, 3.6, 10.6, WHITE, 0, BASE + 3.2, z0, .25);
  box(17.7, .16, 10.7, '#8b6fd1', 0, BASE + 3.12, z0);
  glassWall({ x: 0, z: z0, w: 17.6, d: 10.6 }, 'z', BASE + 4.3, 1, 1.5, 10, WHITE, 1.2);
  glassWall({ x: 0, z: z0, w: 17.6, d: 10.6 }, 'x', BASE + 4.3, 1, 1.5, 6, WHITE, 1.2);
  rbox(8, .3, 4.6, WHITE, 0, BASE + 2.75, 4.2, .08);
  for (const x of [-3.6, 3.6]) cyl(.1, .1, 2.75, '#d5d9de', x, BASE, 6.2, 12);
  rbox(10, .18, 2.4, '#e4e0d7', 0, BASE, 6.4, .06);
  rbox(2.8, 15, 2.8, WHITE, 6.8, BASE, -7.4, .2);
  rbox(3, .4, 3, '#8b6fd1', 6.8, BASE + 15, -7.4, .1);
  clockFace(6.8, BASE + 12.8, -7.4 + 1.42, 1, 'z'); clockFace(6.8 + 1.42, BASE + 12.8, -7.4, 1, 'x');
  rbox(9.2, .3, 3.8, '#f1efe9', -4, BASE, 8.3, .1);
  box(8.6, .06, 3.2, water, -4, BASE + .26, 8.3);
  for (const x of [3.5, 6]) rbox(1.8, .5, .6, WOOD, x, BASE, 9.2, .08);
  tree(-8.6, -8.6, .8, 'cypress'); tree(8.6, 8.6, .75, 'round'); tree(-8.6, 4.5, .7, 'cypress');
  B.hall = { name: 'Town Hall', color: '#8B6FD1', label: [0, 10.5, -3.5], ring: [0, -1, 11],
    agent: { x: 2.4, z: 7.6, shirt: '#2B3A67', skin: '#A0673C', hair: '#222', hat: 'top' } };
}

// Office: stepped glass tower with white floor plates
{
  const x = -C, z = -C;
  box(11, 18, 11, CORE, x, BASE, z);
  glassWall({ x, z, w: 11, d: 11 }, 'z', BASE, 6, 3, 4, '#f3f4f5'); glassWall({ x, z, w: 11, d: 11 }, 'x', BASE, 6, 3, 4, '#f3f4f5');
  rbox(11.8, .5, 11.8, WHITE, x, BASE + 18, z, .1);
  const ux = x - .8, uz = z - .8;
  box(8.4, 10.5, 8.4, CORE, ux, BASE + 18.5, uz);
  glassWall({ x: ux, z: uz, w: 8.4, d: 8.4 }, 'z', BASE + 18.5, 3, 3.5, 3, '#f3f4f5'); glassWall({ x: ux, z: uz, w: 8.4, d: 8.4 }, 'x', BASE + 18.5, 3, 3.5, 3, '#f3f4f5');
  rbox(9, .7, 9, WHITE, ux, BASE + 29, uz, .1);
  rbox(3, 1.3, 3, CONCRETE, ux - 1.5, BASE + 29.7, uz - 1.5, .1);
  for (const [px, pz] of [[x + 4.6, z + 4.6], [x + 4.6, z - 1], [x - 1, z + 4.6]]) rbox(1.2, .6, 1.2, '#7dbb6a', px, BASE + 18.5, pz, .2);
  cyl(.06, .06, 4, '#9aa3ae', ux + 2.5, BASE + 29.7, uz - 2.5, 6);
  sph(.25, night ? glow('#ff5a5f', '#ff2a30', 3) : mat('#d64545'), ux + 2.5, BASE + 33.9, uz - 2.5, 10);
  rbox(5, .3, 2.4, WHITE, x, BASE + 3.1, z + 6.6, .08);
  tree(x - 9, z + 9, .9); tree(x + 9, z - 9, .9, 'round');
  B.office = { name: 'Office', color: '#5D7085', label: [ux, 31.5, uz], ring: [x, z, 9.5],
    agent: { x: x + 2.5, z: z + 8.6, shirt: '#3D4B5C', skin: '#F1C27D', hair: '#6B4423' } };
}

// School: glass ground floor + cantilevered timber upper floor + orange stair tower
{
  const x = 0, z = -C;
  box(16, 3.6, 10, CORE, x, BASE, z);
  glassWall({ x, z, w: 16, d: 10 }, 'z', BASE, 1, 3.6, 7); glassWall({ x, z, w: 16, d: 10 }, 'x', BASE, 1, 3.6, 4);
  const up = { x: x + 1.5, z: z - .4, w: 18, d: 9.2 };
  rbox(18, 4.4, 9.2, WOOD, up.x, BASE + 3.6, up.z, .2);
  glassWall(up, 'z', BASE + 4.4, 1, 2.8, 9, '#a97e54'); glassWall(up, 'x', BASE + 4.4, 1, 2.8, 4, '#a97e54');
  rbox(18.4, .4, 9.6, WHITE, up.x, BASE + 8, up.z, .1);
  rbox(3, 9.4, 3, '#e8963f', x - 8.6, BASE, z + 2.6, .2);
  glassWall({ x: x - 8.6, z: z + 2.6, w: 3, d: 3 }, 'z', BASE + 1, 3, 2.6, 1, '#e8963f');
  for (const px of [-4, 0, 4]) sph(.7, '#82c06f', up.x + px, BASE + 9, up.z - 2, 16);
  rbox(4, .2, 1.8, '#e4e0d7', x + 1, BASE, z + 5.9, .06);
  tree(x - 9.5, z + 8.5, .85, 'cypress'); tree(x + 9.5, z - 9, .9, 'round');
  B.school = { name: 'School', color: '#E0913A', label: [up.x, 11.5, up.z], ring: [x, z, 10.8],
    agent: { x: x + 3, z: z + 8.2, shirt: '#F2A541', skin: '#F1C27D', hair: '#4A2C1A' } };
}

// Lab: white block with ribbon windows, glossy dome, solar panels, teal entrance
{
  const x = -C, z = 0, b = { x, z, w: 14, d: 12 };
  rbox(14, 7.6, 12, '#f6f8f8', x, BASE, z, .3);
  glassWall(b, 'z', BASE + 1, 2, 3, 6, '#f6f8f8', 1.6); glassWall(b, 'x', BASE + 1, 2, 3, 5, '#f6f8f8', 1.6);
  rbox(4, 3.2, 1.2, '#2a9d8f', x + 3.6, BASE, z + 6.2, .15);
  add(new THREE.SphereGeometry(3.2, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2), mat('#f2f5f6', { roughness: .25 }), x - 3, BASE + 7.6, z - 2.5);
  const slit = box(.7, 2.6, .25, DARK, x - 3, BASE + 8.2, z + .4); slit.rotation.x = -.6;
  const solar = mat('#22406e', { metalness: .5, roughness: .25 });
  for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) { const s = box(2.6, .1, 1.6, solar, x + 2 + j * 3, BASE + 7.9, z - 3.2 + i * 2.3); s.rotation.x = -.35; }
  tree(x - 9.5, z + 9.5, .9, 'round'); tree(x + 9.5, z - 9.5, .85, 'cypress');
  B.lab = { name: 'Lab', color: '#2A9D8F', label: [x, 12.5, z], ring: [x, z, 10.2],
    agent: { x: x - 1.5, z: z + 9, shirt: '#F5F7F8', skin: '#E0AC69', hair: '#222' } };
}

// Ideas: white round tower with glass rings and a glowing glass lantern + bulb on top
{
  const x = C, z = -C, tx = x - 1.5, tz = z - 1.5;
  rbox(11, 3.6, 8, WHITE, x + 1.5, BASE, z + 1.5, .25);
  box(11.05, .28, 8.05, '#9b7fd1', x + 1.5, BASE + 3.2, z + 1.5);
  glassWall({ x: x + 1.5, z: z + 1.5, w: 11, d: 8 }, 'z', BASE + .2, 1, 2.8, 5, WHITE);
  cyl(2.8, 2.8, 16, WHITE, tx, BASE, tz, 48);
  for (const y of [4, 8, 12]) cyl(2.86, 2.86, 1.3, glassMat(), tx, BASE + y, tz, 48);
  cyl(2.4, 2.4, 2.6, glassMat(), tx, BASE + 16, tz, 48);
  cyl(3.1, 3.1, .35, WHITE, tx, BASE + 18.6, tz, 48);
  cyl(.7, .9, .9, '#c9ced4', tx, BASE + 18.95, tz, 24);
  sph(2, night ? glow('#fff3b8', '#ffd84a', 2.2) : mat('#fffbea', { roughness: .4, emissive: '#fff3c4', emissiveIntensity: .15 }), tx, BASE + 21.6, tz, 40);
  if (night) { const l = new THREE.PointLight('#ffe066', 110, 34, 2); l.position.set(tx, BASE + 21.6, tz); scene.add(l); }
  tree(x + 9, z - 9, .9, 'round'); tree(x - 9, z + 9.5, .8, 'cypress');
  B.ideas = { name: 'Ideas', color: '#9B7FD1', label: [tx, 26, tz], ring: [x, z, 9.2],
    agent: { x: x + 6.5, z: z + 8.6, shirt: '#9B7FD1', skin: '#F1C27D', hair: '#E9A23B' } };
}

// Gym: dark-framed glass box with a running track on the roof + blue fin
{
  const x = -C, z = C, b = { x, z, w: 15, d: 11 };
  box(15, 5.4, 11, CORE, x, BASE, z);
  glassWall(b, 'z', BASE, 1, 5.4, 5, DARK); glassWall(b, 'x', BASE, 1, 5.4, 4, DARK);
  rbox(15.8, .7, 11.8, WHITE, x, BASE + 5.4, z, .15);
  const track = add(new THREE.RingGeometry(3.3, 4.5, 64), mat('#3b82f6'), x, BASE + 6.12, z); track.rotation.x = -Math.PI / 2; track.scale.set(1.45, 1, 1);
  const field = add(new THREE.CircleGeometry(3.3, 64), mat('#86c875'), x, BASE + 6.11, z); field.rotation.x = -Math.PI / 2; field.scale.set(1.45, 1, 1);
  rbox(.6, 7.6, 2.4, '#2f80ed', x + 7.9, BASE, z + 4.4, .15);
  tree(x - 9.5, z - 9, .9, 'round'); tree(x + 9.5, z + 9.5, .8, 'cypress');
  B.gym = { name: 'Gym', color: '#2F80ED', label: [x, 10.5, z], ring: [x, z, 10.2],
    agent: { x: x + 3, z: z + 8.6, shirt: '#2F80ED', skin: '#C68642', hair: '#2B1B0E' } };
}

// Post Office: white block, navy portal + band, envelope plate, parcel lockers
{
  const x = C, z = 0;
  rbox(13, 7, 10, WHITE, x, BASE, z, .25);
  glassWall({ x, z, w: 5.4, d: 10 }, 'z', BASE, 2, 2.6, 3, NAVY);
  for (const s of [-1, 1]) box(.6, 5.6, .8, NAVY, x + s * 3, BASE, z + 5.2);
  box(6.6, .6, .8, NAVY, x, BASE + 5.4, z + 5.2);
  glassWall({ x, z, w: 13, d: 10 }, 'x', BASE + 1, 2, 2.6, 4, WHITE, 1.8);
  box(13.05, .35, 10.05, NAVY, x, BASE + 6.4, z);
  rbox(2.4, 1.6, .2, NAVY, x - 4.6, BASE + 4.2, z + 5.05, .08);
  for (const s of [-1, 1]) { const v = box(1.3, .1, .05, '#ffffff', x - 4.6 + s * .55, BASE + 5.15, z + 5.17); v.rotation.z = s * .55; }
  rbox(4.2, 2.3, .9, NAVY, x + 4.3, BASE, z + 7.4, .1);
  for (let i = 1; i < 4; i++) box(.04, 2.2, .05, '#8fa6cf', x + 2.2 + i * 1.05, BASE + .05, z + 7.86);
  box(4.1, .04, .05, '#8fa6cf', x + 4.3, BASE + 1.15, z + 7.86);
  tree(x + 9.5, z - 9, .9, 'cypress'); tree(x - 9.5, z - 9.5, .8, 'round');
  B.post = { name: 'Post Office', color: '#2F4F86', label: [x, 11.5, z], ring: [x, z, 9.8],
    agent: { x: x - 1.5, z: z + 8.4, shirt: '#2F4F86', skin: '#FFDBAC', hair: '#A0522D', hat: 'cap' } };
}

// Kitchen (glass café, timber roof, terrace with red umbrellas) + Market (open hall, folded roof)
{
  const z = C, kx = -5.5, kz = z - 1.5, k = { x: kx, z: kz, w: 8, d: 7 };
  box(8, 3.6, 7, CORE, kx, BASE, kz);
  glassWall(k, 'z', BASE, 1, 3.6, 4, DARK); glassWall(k, 'x', BASE, 1, 3.6, 3, DARK);
  rbox(10, .55, 9, WOOD, kx, BASE + 3.6, kz + .6, .12);
  cyl(.22, .22, 2.4, '#a3abb5', kx + 2.6, BASE + 4.1, kz - 2, 16);
  const steam = new THREE.MeshStandardMaterial({ color: '#ffffff', transparent: true, opacity: night ? .18 : .55 });
  [[0, 7, .4], [.3, 7.9, .55], [.7, 9, .7]].forEach(([dx, y, r]) => { add(new THREE.SphereGeometry(r, 16, 12), steam, kx + 2.6 + dx, BASE + y, kz - 2).castShadow = false; });
  for (const [tx, tz] of [[kx - 3, z + 4.6], [kx + .2, z + 4.9]]) {
    cyl(.55, .55, .08, WHITE, tx, BASE + 1, tz, 24); cyl(.05, .05, 1, DARK, tx, BASE, tz, 8);
    cyl(.04, .04, 2.6, DARK, tx, BASE, tz, 8); add(new THREE.ConeGeometry(1.35, .45, 24), '#d9534f', tx, BASE + 2.75, tz);
  }
  B.kitchen = { name: 'Kitchen', color: '#D9534F', label: [kx, 9, kz], ring: [kx, z - .5, 6.6],
    agent: { x: kx - 1.4, z: z + 7, shirt: '#FAFAFA', skin: '#E0AC69', hair: '#3B2A1A', hat: 'chef' } };

  const mx = 6;
  for (const px of [-3.8, 0, 3.8]) for (const pz of [-3, 3]) cyl(.12, .12, 4.3, DARK, mx + px, BASE, z + pz, 12);
  for (let i = 0; i < 4; i++) { const r = rbox(2.4, .22, 7.6, WHITE, mx - 3.6 + i * 2.4, BASE + 4.5, z, .05); r.rotation.z = (i % 2 ? -1 : 1) * .26; }
  box(9.8, .16, .16, '#4e9a5b', mx, BASE + 4.2, z + 3.85);
  const fruit = ['#d9443a', '#f09a3e', '#6dbe45', '#e9c33b'];
  for (const [sx, n] of [[mx - 1.9, 0], [mx + 1.9, 2]]) {
    rbox(3.2, 1, 1.8, WOOD, sx, BASE, z + 1, .08);
    for (let i = 0; i < 6; i++) sph(.3, fruit[(i + n) % 4], sx - 1.1 + (i % 3) * 1.1, BASE + 1.3, z + .6 + Math.floor(i / 3) * .8, 12);
  }
  for (const cx of [mx - 2, mx + 2]) rbox(.9, .5, .7, '#d6b48a', cx, BASE, z - 1.8, .06);
  if (night) for (let i = 0; i < 12; i++) add(new THREE.SphereGeometry(.12, 10, 8), glow('#fff0b8', '#ffd060', 2.6), mx - 4 + i * .73, BASE + 4.05, z + 3.95).castShadow = false;
  tree(-9, z + 9.5, .7, 'round'); tree(9.5, z - 9.5, .7, 'cypress');
  B.market = { name: 'Market', color: '#4E9A5B', label: [mx, 8, z], ring: [mx, z, 6.6],
    agent: { x: mx + 1.5, z: z + 7, shirt: '#4E9A5B', skin: '#8D5524', hair: '#111' } };
}

// People: three modern homes, a pool and hedges
{
  const x = C, z = C;
  rbox(6, 3, 5.4, WHITE, x - 5.5, BASE, z - 4.5, .15);
  glassWall({ x: x - 5.5, z: z - 4.5, w: 6, d: 5.4 }, 'z', BASE + .2, 1, 2.5, 2, DARK);
  rbox(5.6, 2.8, 5, WOOD, x - 4.8, BASE + 3, z - 4.9, .15);
  glassWall({ x: x - 4.8, z: z - 4.9, w: 5.6, d: 5 }, 'x', BASE + 3.2, 1, 2.3, 2, '#a97e54');
  glassWall({ x: x - 4.8, z: z - 4.9, w: 5.6, d: 5 }, 'z', BASE + 3.2, 1, 2.3, 1, '#a97e54', 1.6);
  box(6, 4.2, 6, '#4b515a', x + 4, BASE, z - 5);
  const roof = box(6.6, .3, 6.8, '#3a3f47', x + 4, BASE + 4.6, z - 5); roof.rotation.x = .16;
  glassWall({ x: x + 4, z: z - 5, w: 6, d: 6 }, 'z', BASE + .2, 1, 3.6, 3, '#3a3f47'); glassWall({ x: x + 4, z: z - 5, w: 6, d: 6 }, 'x', BASE + 1, 1, 2.2, 2, '#3a3f47');
  rbox(6, 3, 5, WHITE, x + 1.5, BASE, z + 4.5, .15);
  glassWall({ x: x + 1.5, z: z + 4.5, w: 6, d: 5 }, 'x', BASE + .2, 1, 2.5, 2, DARK);
  for (let i = 0; i < 12; i++) box(.16, 2.6, .12, WOOD, x - 1.1 + i * .48, BASE + .1, z + 7.06);
  rbox(4.6, .3, 3.2, '#f1efe9', x - 5.5, BASE, z + 1.5, .08);
  box(3.6, .06, 2.2, water, x - 5.5, BASE + .27, z + 1.5);
  for (const [hx, hz, w] of [[x - 5.5, z + 9.6, 8], [x + 9.6, z + 2, .9]]) rbox(w, .9, w > 1 ? .9 : 10, '#6fae62', hx, BASE, hz, .35);
  tree(x + 9, z + 9, .8, 'round'); tree(x - 9.5, z - 9.5, .8, 'cypress');
  B.people = { name: 'People', color: '#E07A5F', label: [x, 10.5, z - 1], ring: [x, z, 11],
    agent: { x: x - 5, z: z + 5.6, shirt: '#E07A5F', skin: '#8D5524', hair: '#1B1B1B' } };
}

// ---------- residents: Bot Crossing bots ----------
// mood per building: eye colour + face + what the body is doing; at night, idle residents sit and sleep
const MOOD = {
  people:  { look: 'waiting',     face: 'alert',  clip: 'Waving',    t: .4 },
  school:  { look: 'blocked',     face: 'sad',    clip: 'Waving',    t: .9 },
  gym:     { look: 'working',     face: 'work',   clip: 'Working_A', t: .5 },
  kitchen: { look: 'idle',        face: 'idle',   clip: 'Idle_A',    t: 1.2, rests: true },
  office:  { look: 'blocked',     face: 'sad',    clip: 'Waving',    t: .2 },
  hall:    { look: 'celebrating', face: 'alert',  clip: 'Waving',    t: .6 },
  post:    { look: 'waiting',     face: 'wait',   clip: 'Interact',  t: .7 },
  market:  { look: 'working',     face: 'work',   clip: 'Hammering', t: .3 },
  lab:     { look: 'idle',        face: 'think2', clip: 'Idle_B',    t: .8, rests: true },
  ideas:   { look: 'celebrating', face: 'happy',  clip: 'Cheering',  t: .5, rests: true },
};
const kit = await loadBotKit('./vendor/bot-crossing/crew.glb');
const SUITS = [0xf3f1ec, 0xe8e4dc, 0xf7f4ee, 0xdfe4e8, 0xf1e9df];
Object.entries(B).forEach(([id, b], i) => {
  let m = MOOD[id];
  if (night && m.rests) m = { look: 'sleeping', face: 'sleep', clip: 'Sit_Floor_Idle', t: 1 };
  const bot = makeBot(kit, { ...m, scale: 1.9, suit: SUITS[i % SUITS.length], pack: new THREE.Color(b.color).getHex(), night: P.lamps });
  bot.root.position.set(b.agent.x, BASE, b.agent.z);
  bot.root.rotation.y = Math.PI / 4;   // face the camera
  scene.add(bot.root);
  bot.root.updateMatrixWorld(true);
  b.agent.top = bot.headTop();
});

// selected building: a glowing ring on the ground
if (panelName && B[panelName]) {
  const [rx, rz, rr] = B[panelName].ring;
  const ring = new THREE.Mesh(new THREE.RingGeometry(rr, rr + .5, 96), glow('#ffd166', '#ffc23d', 2));
  ring.rotation.x = -Math.PI / 2; ring.position.set(rx, BASE + .12, rz); scene.add(ring);
}

// ---------- render (bloom makes lit windows and lamps glow) ----------
// colour grade shader, from Bot Crossing's engine.js (MIT)
const GRADE_SHADER = {
  uniforms: { tDiffuse: { value: null }, uSaturation: { value: 1 }, uWarmth: { value: 0 }, uVignette: { value: 0.3 } },
  vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 ); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float uSaturation; uniform float uWarmth; uniform float uVignette; varying vec2 vUv;
    void main() {
      vec4 c = texture2D( tDiffuse, vUv ); vec3 col = c.rgb;
      col += ( 1.0 - col ) * vec3( 0.035, 0.045, 0.075 ) * ( 1.0 - smoothstep( 0.0, 0.5, dot( col, vec3( 0.333 ) ) ) );
      float l = dot( col, vec3( 0.2126, 0.7152, 0.0722 ) );
      col = mix( vec3( l ), col, uSaturation );
      col *= vec3( 1.0 + uWarmth * 0.9, 1.0 + uWarmth * 0.25, 1.0 - uWarmth * 0.9 );
      col = mix( col, col * col * ( 3.0 - 2.0 * col ), 0.16 );
      vec2 d = vUv - 0.5; col *= 1.0 - dot( d, d ) * uVignette * 1.15;
      gl_FragColor = vec4( clamp( col, 0.0, 1.0 ), c.a );
    }`,
};

const depthTexture = new THREE.DepthTexture(W, H); depthTexture.type = THREE.UnsignedIntType;
const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: true, depthTexture });
const composer = new EffectComposer(renderer, rt);
composer.setPixelRatio(1); composer.setSize(W, H);
composer.addPass(new RenderPass(scene, camera));
const ao = new OcclusionPass(camera); ao.setSize(W, H); ao.setStrength(.25); composer.addPass(ao);
composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), ...P.bloom));
const tilt = createTiltShift();                       // miniature look: sharp where you look, soft beyond
for (const p of tilt.passes) composer.addPass(p);
tilt.setSize(W, H); tilt.setCamera(camera); tilt.setStrength(.3); tilt.setAngle(0);
tilt.setFocusDistance(camera.position.distanceTo(target));
composer.addPass(new OutputPass());
const grade = new ShaderPass(GRADE_SHADER);           // Bot Crossing's grade: lifted blacks, saturation, S-curve, vignette
grade.uniforms.uSaturation.value = 1.06; grade.uniforms.uWarmth.value = .02; grade.uniforms.uVignette.value = .3;
composer.addPass(grade);
tilt.setDepthTexture(composer.readBuffer.depthTexture);
composer.render();

// ---------- HTML layer: labels + speech bubbles pinned to 3D positions ----------
const interactive = !navigator.webdriver || q.get('controls') === '1';
const toScreen = ([x, y, z]) => { const v = new THREE.Vector3(x, y, z).project(camera); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; };
const BUBBLES = {
  people:  { k: 'follow',  label: 'Follow-up · late', t: 'Follow up with Ali', bang: true },
  school:  { k: 'overdue', label: 'Overdue · 2 days', t: 'OS assignment 3', bang: true },
  gym:     { k: 'today',   label: 'Today', t: 'Leg day + 20 min cardio' },
  kitchen: { k: 'next',    label: 'Sun · Oct 11', t: 'Meal prep for the week' },
  office:  { k: 'overdue', label: 'Overdue · 1 day', t: 'Submit internship application', bang: true },
  hall:    { k: 'brief',   label: "Today's brief", t: '3 overdue · 3 due today', bang: true },
  post:    { k: 'draft',   label: 'Draft waiting', t: 'Reply to Prof. Lee', bang: true },
  market:  { k: 'today',   label: 'Today', t: 'Groceries: eggs, rice, oats' },
  lab:     { k: 'next',    label: 'Thu · Oct 15', t: 'CloudGuard: add S3 checks' },
  ideas:   { k: 'clear',   label: 'All clear', t: 'Nothing due', idle: true },
};
const icon = P.icon === 'moon'
  ? '<svg width="14" height="14" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" fill="currentColor"/></svg>'
  : '<svg width="14" height="14" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5" fill="#F5B301"/><g stroke="#F5B301" stroke-width="2" stroke-linecap="round"><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></g></svg>';
const [hh, mm] = P.time;
const timeStr = `${((hh + 11) % 12) + 1}:${String(mm).padStart(2, '0')} ${hh < 12 ? 'AM' : 'PM'}`;
let ui = `<div class="topbar">
  <div class="brand"><svg width="26" height="26" viewBox="0 0 26 26"><rect x="3" y="11" width="20" height="13" rx="2" fill="#8B6FD1"/><path d="M1 12 L13 3 L25 12" fill="none" stroke="#5E4AA0" stroke-width="2.5" stroke-linejoin="round"/><rect x="11" y="16" width="5" height="8" fill="#FFD670"/></svg>
    MOH World <small>your second brain, as a town</small></div>
  <div class="clock">Thursday, October 8 <b>${timeStr}</b> <span class="pill">${icon} ${P.label}</span></div>
  <div class="status"><span><span class="mini-bang">!</span> needs you</span><span><span class="dot"></span> Live · vault read-only</span></div>
</div>`;
for (const [id, b] of Object.entries(B)) {
  if (q.get('ui') === '0') break;
  const [lx, ly] = toScreen(b.label);
  ui += `<div class="label ${id === panelName ? 'sel' : ''}" style="left:${lx}px;top:${ly}px"><i style="background:${b.color}"></i>${b.name}</div>`;
  const a = b.agent;
  const [ax, ay] = toScreen([a.top.x, a.top.y, a.top.z]);
  const d = BUBBLES[id];
  ui += `<div class="bubble ${d.idle ? 'idle' : ''}" style="left:${ax}px;top:${ay}px">
    <span class="k ${d.k}">${d.label}</span><span class="t">${d.t}</span>${d.bang ? '<span class="bang">!</span>' : ''}</div>`;
}
if (!panelName && q.get('hint') !== '0' && q.get('ui') !== '0') {
  ui += `<div class="hint"><b>Click a building</b> to see its open tasks · the sky follows your clock</div>`;
  if (!interactive) ui += `<div class="controls">Drag to rotate · scroll to zoom</div>`;
}
const tag = id => `<span class="tag" style="background:${B[id].color}">${B[id].name}</span>`;
const row = (title, id, file, due, cls = '') => `<div class="row"><div class="main"><div class="title">${title}</div>
  <div class="meta">${tag(id)}<span>${file}</span></div></div><div class="due ${cls}">${due}</div><div class="open">↗</div></div>`;
if (panelName === 'hall') ui += `<div class="panel"><div class="close">✕</div>
  <div class="eyebrow">Town Hall</div><h2>Morning brief</h2><div class="sub">Thursday, October 8 · across all buildings</div>
  <div class="sec"><h3>Overdue <span class="count red">3</span></h3>
    ${row('OS assignment 3', 'school', 'OS/Assignment 3.md', '2 days late', 'red')}
    ${row('Submit internship application', 'office', 'Internships.md', '1 day late', 'red')}
    ${row('Return library books', 'school', 'Library.md', '1 day late', 'red')}</div>
  <div class="sec"><h3>Due today <span class="count amber">3</span></h3>
    ${row('Leg day + 20 min cardio', 'gym', 'Plan - October.md', 'today', 'amber')}
    ${row('Groceries: eggs, rice, oats', 'market', 'Shopping list.md', 'today', 'amber')}
    ${row('Pay phone bill', 'office', 'Bills.md', 'today', 'amber')}</div>
  <div class="sec"><h3>Follow-ups due <span class="count red">2</span></h3>
    ${row('Follow up with Ali', 'people', 'Ali.md', '1 day late', 'red')}
    ${row('Check in with Sara', 'people', 'Sara.md', 'today', 'amber')}</div>
  <div class="sec"><h3>Drafts waiting <span class="count blue">1</span></h3>
    ${row('Reply to Prof. Lee', 'post', 'Reply - Prof Lee.md', 'draft', 'blue')}</div>
  <div class="foot"><span>↗ opens the note in Obsidian</span><span>read-only</span></div></div>`;
if (panelName === 'school') ui += `<div class="panel"><div class="close">✕</div>
  <div class="eyebrow">School · 01 School</div><h2>5 open tasks</h2><div class="sub">Sorted by due date</div>
  <div class="sec"><h3>Overdue <span class="count red">2</span></h3>
    ${row('OS assignment 3', 'school', 'OS/Assignment 3.md', 'Oct 6', 'red')}
    ${row('Return library books', 'school', 'Library.md', 'Oct 7', 'red')}</div>
  <div class="sec"><h3>Upcoming <span class="count">3</span></h3>
    ${row('Read Networks ch. 7', 'school', 'Networks/Week 7.md', 'Tomorrow', 'amber')}
    ${row('Email TA about regrade', 'school', 'DB/Midterm.md', 'Mon, Oct 12')}
    ${row('DB midterm prep', 'school', 'DB/Midterm.md', 'Wed, Oct 14')}</div>
  <div class="foot"><span>↗ opens the note in Obsidian</span><span>read-only</span></div></div>`;
// mockup-only switcher (hidden in automated screenshots): every view is a link that reloads the page
if (interactive) {
  const DEF = { phase: 'day', cam: 'wide', panel: '', ui: '1' };
  const link = (k, v, label) => {
    const p = new URLSearchParams(location.search);
    if (v === DEF[k]) p.delete(k); else p.set(k, v);
    const on = (q.get(k) ?? DEF[k]) === v;
    return `<a class="${on ? 'on' : ''}" href="?${p}">${label}</a>`;
  };
  ui += `<div class="mock" style="${panelName ? 'left:592px' : ''}">
    <b>Time</b>${link('phase', 'dawn', 'Dawn')}${link('phase', 'day', 'Day')}${link('phase', 'dusk', 'Dusk')}${link('phase', 'night', 'Night')}
    <b>View</b>${link('cam', 'wide', 'Town')}${link('cam', 'close', 'Closer')}${link('cam', 'hero', 'Bot close-up')}
    <b>Panel</b>${link('panel', '', 'None')}${link('panel', 'hall', 'Town Hall')}${link('panel', 'school', 'School')}
    <b>Bubbles</b>${link('ui', '1', 'On')}${link('ui', '0', 'Off')}</div>`;
}
document.getElementById('ui').innerHTML = ui;
if (interactive) {   // scale the fixed 1600x900 frame to fit the window
  const stage = document.getElementById('stage');
  const fit = () => { const k = Math.min(innerWidth / W, innerHeight / H); stage.style.transformOrigin = '0 0'; stage.style.transform = `scale(${k})`; };
  fit(); addEventListener('resize', fit);
}
// labels that land on top of a speech bubble get nudged upward until they're clear
const overlaps = (a, b, m = 6) => a.left < b.right + m && b.left < a.right + m && a.top < b.bottom + m && b.top < a.bottom + m;
const placed = [...document.querySelectorAll('.bubble')].map(e => e.getBoundingClientRect());
for (const el of document.querySelectorAll('.label')) {
  let top = parseFloat(el.style.top);
  for (let i = 0; i < 40 && placed.some(r => overlaps(el.getBoundingClientRect(), r)); i++) { top -= 4; el.style.top = top + 'px'; }
  placed.push(el.getBoundingClientRect());
}
window.__ready = true;

// ---------- sky: a painted gradient behind the 3D scene ----------
function skyTexture() {
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, H);
  for (const [o, col] of P.sky) grad.addColorStop(o, col);
  g.fillStyle = grad; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 140 * P.stars; i++) {
    g.globalAlpha = .35 + hash(i + 900) * .65; g.fillStyle = '#fff';
    g.beginPath(); g.arc(hash(i) * W, hash(i + 300) * H * .75, .6 + hash(i + 600) * 1.3, 0, Math.PI * 2); g.fill();
  }
  g.globalAlpha = 1;
  if (P.disc) {
    const { x, y, r, c: col } = P.disc, cx = x * W, cy = y * H;
    const rg = g.createRadialGradient(cx, cy, 0, cx, cy, r * 3.2);
    rg.addColorStop(0, col + 'cc'); rg.addColorStop(1, col + '00');
    g.fillStyle = rg; g.fillRect(cx - r * 4, cy - r * 4, r * 8, r * 8);
    g.fillStyle = col; g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.fill();
  }
  if (P.moon) {
    const { x, y, r } = P.moon, cx = x * W, cy = y * H;
    const rg = g.createRadialGradient(cx, cy, 0, cx, cy, r * 3.4);
    rg.addColorStop(0, 'rgba(221,230,255,.35)'); rg.addColorStop(1, 'rgba(221,230,255,0)');
    g.fillStyle = rg; g.fillRect(cx - r * 4, cy - r * 4, r * 8, r * 8);
    const m = document.createElement('canvas'); m.width = m.height = r * 2 + 4;
    const mg = m.getContext('2d');
    mg.fillStyle = '#F4F1E1'; mg.beginPath(); mg.arc(r + 2, r + 2, r, 0, Math.PI * 2); mg.fill();
    mg.globalCompositeOperation = 'destination-out'; mg.beginPath(); mg.arc(r + 2 + 13, r + 2 - 8, r, 0, Math.PI * 2); mg.fill();
    g.drawImage(m, cx - r - 2, cy - r - 2);
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
