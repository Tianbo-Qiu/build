// N-704: a Blender-baked robot whose head follows the pointer, drawn with three.js.
// Expects an import map for "three" and "three/addons/".
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const D2R = Math.PI / 180;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

for (const root of document.querySelectorAll("[data-robot3d]")) start(root);

function start(root) {
  const canvas = root.querySelector("canvas");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Load only when the robot is near the viewport.
  const io = new IntersectionObserver((entries) => {
    if (!entries.some((e) => e.isIntersecting)) return;
    io.disconnect();
    try { boot(); } catch (err) { root.classList.add("robot3d--failed"); } // no WebGL: keep the still image
  }, { rootMargin: "200px" });
  io.observe(root);

  function boot() {
    // Transparent canvas: the page's own light or dark background shows through.
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.AgXToneMapping;
    renderer.toneMappingExposure = 0.95;

    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = 0.5;

    // Same framing as the Blender camera: 70 mm lens on a 36 mm sensor, 2.25 m away.
    const camera = new THREE.PerspectiveCamera(2 * Math.atan(18 / 70) / D2R, 1, 0.1, 20);
    camera.position.set(0, 1.0, 2.25);
    camera.lookAt(0, 1.0, 0);

    const key = new THREE.DirectionalLight(0xffffff, 2.6); key.position.set(-1.8, 2.2, 1.6); scene.add(key);
    const fill = new THREE.DirectionalLight(0xdfe8ff, 0.45); fill.position.set(1.8, 1.2, 2.0); scene.add(fill);
    const rim = new THREE.DirectionalLight(0xffffff, 1.4); rim.position.set(1.2, 2.0, -1.6); scene.add(rim);

    function resize() {
      const w = root.clientWidth || 300;
      renderer.setSize(w, w, false);
      dirty = true;
    }

    // Soft glow in front of the CRT, carried by the head bone.
    function glowPlane() {
      const c = document.createElement("canvas"); c.width = c.height = 128;
      const g = c.getContext("2d"), grd = g.createRadialGradient(64, 64, 8, 64, 64, 64);
      grd.addColorStop(0, "rgba(225,236,255,0.55)"); grd.addColorStop(0.45, "rgba(205,222,255,0.18)"); grd.addColorStop(1, "rgba(200,220,255,0)");
      g.fillStyle = grd; g.fillRect(0, 0, 128, 128);
      const mat = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
      const m = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.5), mat);
      m.position.set(0, 1.26, 0.125);   // screen centre, just in front of the glass
      return m;
    }
    new ResizeObserver(resize).observe(root);

    const draco = new DRACOLoader().setDecoderPath(root.dataset.draco);
    const loader = new GLTFLoader().setDRACOLoader(draco);
    let rig = null, screenMat = null, dirty = true;

    loader.load(root.dataset.model, (gltf) => {
      scene.add(gltf.scene);
      const bones = {};
      gltf.scene.traverse((o) => {
        if (o.isBone) bones[o.name] = o;
        if (o.isMesh && o.material.emissiveMap) { screenMat = o.material; screenMat.emissive.set(0xffffff); }
        if (o.isMesh) {
          o.frustumCulled = false; // skinned bounds don't follow the bones
          if (o.material.aoMap) o.material.aoMapIntensity = 1.6;
        }
      });
      gltf.scene.updateMatrixWorld(true);
      const glow = glowPlane(); scene.add(glow); bones.Head.attach(glow);
      const rest = {};
      for (const n of ["Body", "Neck", "Head"]) rest[n] = bones[n].getWorldQuaternion(new THREE.Quaternion());
      rig = { bones, rest };
      root.classList.add("robot3d--ready");
      dirty = true;
      requestAnimationFrame(tick);
    }, undefined, () => root.classList.add("robot3d--failed"));

    // Turn a bone by a world-space rotation about its own pivot.
    const qR = new THREE.Quaternion(), qP = new THREE.Quaternion(), e = new THREE.Euler();
    function turn(name, yaw, pitch, roll) {
      const b = rig.bones[name];
      e.set(pitch * D2R, yaw * D2R, -roll * D2R, "YZX");
      qR.setFromEuler(e).multiply(rig.rest[name]);            // desired world rotation
      b.parent.getWorldQuaternion(qP);
      b.quaternion.copy(qP.invert().multiply(qR));            // into parent space
      b.updateMatrixWorld(true);
    }

    // ---- motion: pointer target or idle glances, followed by a spring ----
    const LIM = { yaw: [-50, 50], pitch: [-14, 22] };
    const st = { yaw: 0, pitch: 3, vy: 0, vp: 0 };
    let target = { yaw: 0, pitch: 3 }, lastInput = -1e9, nextGlance = 0;

    function aim(x, y) {
      const r = canvas.getBoundingClientRect();
      const dx = (x - (r.left + r.width * 0.5)) / (r.width * 0.9);
      const dy = (y - (r.top + r.height * 0.27)) / (r.height * 0.9);
      target = {
        yaw: clamp(Math.atan(dx * 1.6) / D2R, ...LIM.yaw),
        pitch: clamp(3 + Math.atan(dy * 1.4) / D2R * 0.7, ...LIM.pitch),
      };
      lastInput = performance.now();
    }
    if (!reduced) {
      addEventListener("pointermove", (ev) => aim(ev.clientX, ev.clientY), { passive: true });
      canvas.addEventListener("pointerdown", (ev) => aim(ev.clientX, ev.clientY));
    }
    function idle(now) {
      if (now < nextGlance) return;
      const r = Math.random();
      if (r < 0.25) target = { yaw: 30 + Math.random() * 12, pitch: 17 + Math.random() * 4 };   // down at its left shoulder
      else if (r < 0.45) target = { yaw: 0, pitch: 3 };                                           // back to you
      else target = { yaw: (Math.random() * 2 - 1) * 45, pitch: -10 + Math.random() * 18 };
      nextGlance = now + 1500 + Math.random() * 2600;
    }

    let prev = performance.now();
    function tick(now) {
      requestAnimationFrame(tick);
      const dt = Math.min((now - prev) / 1000, 0.05); prev = now;
      const t = now / 1000;
      if (!reduced) {
        if (now - lastInput > 3500) idle(now);
        const k = 30, c = 10.4;
        st.vy += (k * (target.yaw - st.yaw) - c * st.vy) * dt; st.yaw += st.vy * dt;
        st.vp += (k * (target.pitch - st.pitch) - c * st.vp) * dt; st.pitch += st.vp * dt;
        // body follows a little; neck takes half; head takes the rest
        turn("Body", st.yaw * 0.15, 0, 0);
        turn("Neck", st.yaw * 0.5, st.pitch * 0.5, st.yaw * 0.05);
        turn("Head", st.yaw, st.pitch, st.yaw * 0.1);
        rig.bones.Body.scale.y = 1 + 0.004 * Math.sin(t * 1.6);     // breathing
        if (screenMat) screenMat.emissiveIntensity = 3.2 + 0.18 * Math.sin(t * 23) * Math.sin(t * 3.1);
        dirty = true;
      } else if (screenMat) {
        screenMat.emissiveIntensity = 3.2;
      }
      if (dirty) { renderer.render(scene, camera); dirty = !reduced; }
    }
  }
}
