// CBRE Lab Safety Induction — Phase 3a (UMD / non-module)
// PC: drag-to-look + WASD + crosshair raycast.
// VR: two-controller laser pointer, contextual trigger (hazard → flag/fix, floor → teleport).
// Globals from index.html: THREE, THREE.GLTFLoader, VRButton.

(function () {
  var statusEl = document.getElementById("status");
  function setStatus(t) { if (statusEl) statusEl.textContent = t; }

  if (typeof THREE === "undefined") { setStatus("Failed to load Three.js."); return; }
  if (typeof THREE.GLTFLoader === "undefined") { setStatus("Failed to load GLTFLoader."); return; }

  // -------------------------------------------------------------------------
  // Constants
  // -------------------------------------------------------------------------
  var WALL_INSET = 0.25;
  var ROOMS = {
    main: { name: "Main lab",  x1: 0.0  + WALL_INSET, x2: 8.0  - WALL_INSET, z1: 0.0 + WALL_INSET, z2: 6.0 - WALL_INSET },
    prep: { name: "Prep room", x1: 8.0  + WALL_INSET, x2: 12.0 - WALL_INSET, z1: 1.0 + WALL_INSET, z2: 5.0 - WALL_INSET },
    door: { name: "Doorway",   x1: 7.6,                x2: 8.4,               z1: 2.05,            z2: 2.95 }
  };
  var EYE_HEIGHT = 1.65;
  var WALK_SPEED = 2.5;
  var SPRINT_MULT = 1.8;
  var CLICK_DRAG_THRESHOLD_PX = 5;
  var RAYCAST_MAX_DIST = 12;
  var TELEPORT_MAX_DIST = 25;

  var COLOR_LASER_DEFAULT = 0xffffff;
  var COLOR_LASER_HAZARD  = 0x9bd6a4;
  var COLOR_LASER_FLOOR   = 0x6ab0d8;

  // -------------------------------------------------------------------------
  // Hazard definitions
  // -------------------------------------------------------------------------
  var HAZARDS = [
    { id: 1, prefix: "HAZARD_01_",
      title: "Fume hood sash left fully raised",
      why: "An open sash defeats the engineering control — solvent vapours escape into the breathing zone. Always work with the sash at the marked working level (typically ~45 cm).",
      fix: "Lower the sash to the marked working height.",
      runFix: function (root) {
        moveBy(root, "HAZARD_01_fume_hood_sash",      "y", -0.95, 1000);
        moveBy(root, "HAZARD_01_fume_hood_sash_rail", "y", -0.95, 1000);
      } },
    { id: 2, prefix: "HAZARD_02_",
      title: "Eyewash station blocked",
      why: "A blocked eyewash can't be reached in the 10–15 seconds you have after a chemical splash. Access must be kept clear at all times — eyewashes are not storage zones.",
      fix: "Remove the obstruction so access is unimpeded.",
      runFix: function (root) {
        scaleHide(root, "HAZARD_02_eyewash_obstruction_a", 800);
        scaleHide(root, "HAZARD_02_eyewash_obstruction_b", 800);
      } },
    { id: 3, prefix: "HAZARD_03_",
      title: "Unlabelled chemical bottle",
      why: "An unidentified substance is a serious risk — you cannot follow COSHH controls, choose the right PPE, or respond correctly to a spill. As FM staff: do NOT touch — escalate to the lab user immediately.",
      fix: "Bottle is tagged 'do not use' and removed from service for the lab user to identify.",
      runFix: function (root) {
        ["HAZARD_03_unlabelled_bottle",
         "HAZARD_03_unlabelled_bottle_neck",
         "HAZARD_03_unlabelled_bottle_cap",
         "HAZARD_03_unlabelled_bottle_label"].forEach(function (n) { fadeAndHide(root, n, 800); });
      } },
    { id: 4, prefix: "HAZARD_04_",
      title: "Trip hazard — extension lead across walkway",
      why: "Cables across walkways cause falls and pull equipment off benches when caught. Power should reach equipment via fitted bench sockets or properly cable-managed routing — never a floor-running extension.",
      fix: "Floor-run cable removed; equipment to be re-powered via the fitted bench socket.",
      runFix: function (root) {
        ["HAZARD_04_extension_lead",
         "HAZARD_04_extension_lead_plug",
         "HAZARD_04_power_strip",
         "HAZARD_04_power_strip_socket_0",
         "HAZARD_04_power_strip_socket_1",
         "HAZARD_04_power_strip_socket_2"].forEach(function (n) { fadeAndHide(root, n, 800); });
      } },
    { id: 5, prefix: "HAZARD_05_",
      title: "Compressed gas cylinder unsecured",
      why: "An untethered cylinder can topple. If the valve breaks off, the cylinder becomes a projectile capable of going through a wall. Cylinders must be chained to a fixed point at all times — including when empty.",
      fix: "Cylinder secured to the wall bracket using the chain.",
      runFix: function (root) {
        for (var i = 0; i < 5; i++) fadeAndHide(root, "HAZARD_05_loose_chain_" + i, 600);
        flashEmissive(root, "HAZARD_05_gas_cylinder", 0x4ad17a, 1400);
        flashEmissive(root, "HAZARD_05_bracket_plate", 0x4ad17a, 1400);
      } },
    { id: 6, prefix: "HAZARD_06_",
      title: "Sharps disposed in general waste",
      why: "Needles in general waste cause needlestick injuries to anyone handling the bag — cleaners, FM staff, waste contractors. Sharps must go into a yellow rigid sharps-only bin and be reported as a near-miss.",
      fix: "Sharps moved to the yellow sharps-only bin and reported as a near-miss.",
      runFix: function (root) {
        ["HAZARD_06_sharps_barrel_1",
         "HAZARD_06_sharps_needle_1",
         "HAZARD_06_sharps_barrel_2",
         "HAZARD_06_sharps_barrel_3"].forEach(function (n) {
          moveBy(root, n, "z", -0.75, 800, function () {
            var o = root.getObjectByName(n); if (o) o.visible = false;
          });
        });
      } },
    { id: 7, prefix: "HAZARD_07_",
      title: "Lab coat sharing a hook with street coat",
      why: "Lab coats can carry trace contamination — pairing them with street wear spreads chemicals or biologicals out of the lab. Lab coats must be hung separately from outdoor clothing.",
      fix: "Street coat moved to a separate hook; lab coat kept isolated.",
      runFix: function (root) {
        ["HAZARD_07_street_coat_yoke",
         "HAZARD_07_street_coat_torso",
         "HAZARD_07_street_coat_hem",
         "HAZARD_07_street_coat_sleeve_l",
         "HAZARD_07_street_coat_sleeve_r",
         "HAZARD_07_street_coat_hood",
         "HAZARD_07_street_coat_hood_opening",
         "HAZARD_07_street_coat_zip"].forEach(function (n) { moveBy(root, n, "x", 1.5, 1000); });
      } }
  ];
  HAZARDS.forEach(function (h) { h.found = false; h.fixed = false; });

  // -------------------------------------------------------------------------
  // Scene + rig (camera lives inside a Group so XR headset can move the
  // camera locally while our locomotion moves the rig)
  // -------------------------------------------------------------------------
  var scene = new THREE.Scene();
  scene.background = new THREE.Color(0x9bb0c4);
  scene.fog = new THREE.Fog(0x9bb0c4, 30, 80);

  var rig = new THREE.Group();
  scene.add(rig);

  var camera = new THREE.PerspectiveCamera(72, window.innerWidth / window.innerHeight, 0.05, 200);
  camera.position.set(0, EYE_HEIGHT, 0);
  rig.add(camera);

  var renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.xr.enabled = true;
  document.getElementById("app").appendChild(renderer.domElement);

  // Image-based ambient lighting (subtle studio reflections on stainless/worktops)
  if (typeof THREE.RoomEnvironment !== "undefined") {
    var pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new THREE.RoomEnvironment(), 0.04).texture;
  }

  if (typeof VRButton !== "undefined") {
    var vrBtn = VRButton.createButton(renderer);
    vrBtn.style.zIndex = "13";
    document.body.appendChild(vrBtn);
  }

  window.addEventListener("resize", function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  scene.add(new THREE.HemisphereLight(0xfff5e8, 0x4a5360, 0.22));

  // Sun shining in through the north window bank, casting interior shadows
  var sun = new THREE.DirectionalLight(0xfff0d8, 1.5);
  sun.position.set(3.0, 8.0, -14.0);
  sun.target.position.set(4.5, 0.0, -2.5);
  scene.add(sun.target);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -9;
  sun.shadow.camera.right = 9;
  sun.shadow.camera.top = 9;
  sun.shadow.camera.bottom = -9;
  sun.shadow.camera.near = 1;
  sun.shadow.camera.far = 40;
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.015;
  scene.add(sun);

  // Ceiling fill lights at troffer positions (no shadows — cheap)
  // Blender (x, y) → Three (x, -y); troffers sit at z≈2.5
  var fillPositions = [
    [2.0, 2.45, -1.6], [5.0, 2.45, -1.6],
    [2.0, 2.45, -4.2], [5.0, 2.45, -4.2],
    [10.0, 2.45, -3.0]
  ];
  for (var fi = 0; fi < fillPositions.length; fi++) {
    var pl = new THREE.PointLight(0xfff8ec, 0.30, 7.5, 2.0);
    pl.position.set(fillPositions[fi][0], fillPositions[fi][1], fillPositions[fi][2]);
    scene.add(pl);
  }

  // Exterior grass plane (visible through the windows)
  var ground = new THREE.Mesh(
    new THREE.PlaneGeometry(80, 80),
    new THREE.MeshStandardMaterial({ color: 0x5f7050, roughness: 1.0 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.05;
  ground.receiveShadow = true;
  scene.add(ground);

  // -------------------------------------------------------------------------
  // GLB load
  // -------------------------------------------------------------------------
  var hudRoom = document.getElementById("hud-room");
  var loader = new THREE.GLTFLoader();
  var labRoot = null;
  setStatus("Loading lab…");
  loader.load(
    "./assets/lab.glb",
    function (gltf) {
      labRoot = gltf.scene;
      scene.add(labRoot);
      var spawn = labRoot.getObjectByName("SPAWN_POINT");
      if (spawn) {
        var wp = new THREE.Vector3();
        spawn.getWorldPosition(wp);
        rig.position.set(wp.x, 0, wp.z);
      } else {
        rig.position.set(1.5, 0, -1.0);
      }
      labRoot.traverse(function (o) {
        if (!o.isMesh) return;
        if (o.name.indexOf("HAZARD_") === 0) o.userData.hazard = true;
        // Shadow flags: glass and emissive troffers must not cast (or the
        // window light and ceiling lights would be blocked by their own glazing)
        var isGlass = o.name.indexOf("window") !== -1 || o.name.indexOf("vision_glass") !== -1 ||
                      (o.material && o.material.transparent);
        var isLightPanel = o.name.indexOf("troffer_light") === 0;
        o.castShadow = !isGlass && !isLightPanel;
        o.receiveShadow = true;
        // Troffer diffusers: force always-bright (emission export varies by exporter)
        if (isLightPanel) {
          o.material = new THREE.MeshBasicMaterial({ color: 0xfffaf0 });
        }
        // Damp environment reflections — full-strength IBL washes the scene out
        if (o.material && o.material.envMapIntensity !== undefined) {
          o.material.envMapIntensity = 0.35;
        }
      });
      renderHazardList();
      setStatus("Ready — click Start");
    },
    function (xhr) { if (xhr && xhr.loaded) setStatus("Loading lab… " + (xhr.loaded / 1024).toFixed(0) + " KB"); },
    function (err) { console.error(err); setStatus("Could not load lab.glb. Run build.bat then serve.bat."); }
  );

  // -------------------------------------------------------------------------
  // Tween system + material safety
  // -------------------------------------------------------------------------
  var tweens = [];
  function pushTween(t) { tweens.push(t); }
  function moveBy(root, name, axis, delta, ms, onDone) {
    var o = root.getObjectByName(name);
    if (!o) { console.warn("[fix] mesh not found:", name); if (onDone) onDone(); return; }
    var from = o.position[axis];
    pushTween({ obj: o.position, prop: axis, from: from, to: from + delta,
                start: performance.now(), dur: ms, onDone: onDone });
  }
  function scaleHide(root, name, ms, onDone) {
    var o = root.getObjectByName(name);
    if (!o) { if (onDone) onDone(); return; }
    var from = o.scale.x;
    var done = false;
    function finish() { if (done) return; done = true; o.visible = false; if (onDone) onDone(); }
    pushTween({ obj: o.scale, prop: "x", from: from, to: 0.001, start: performance.now(), dur: ms });
    pushTween({ obj: o.scale, prop: "y", from: from, to: 0.001, start: performance.now(), dur: ms });
    pushTween({ obj: o.scale, prop: "z", from: from, to: 0.001, start: performance.now(), dur: ms, onDone: finish });
  }
  function ensureUniqueMaterial(o) {
    if (!o || !o.material) return;
    if (o.userData.__uniqueMat) return;
    o.material = o.material.clone();
    o.userData.__uniqueMat = true;
  }
  function fadeAndHide(root, name, ms, onDone) {
    var o = root.getObjectByName(name);
    if (!o) { if (onDone) onDone(); return; }
    if (!o.material) { o.visible = false; if (onDone) onDone(); return; }
    ensureUniqueMaterial(o);
    o.material.transparent = true;
    o.material.depthWrite = false;
    pushTween({ obj: o.material, prop: "opacity",
                from: o.material.opacity != null ? o.material.opacity : 1, to: 0,
                start: performance.now(), dur: ms,
                onDone: function () { o.visible = false; if (onDone) onDone(); } });
  }
  function flashEmissive(root, name, hex, ms) {
    var o = root.getObjectByName(name);
    if (!o || !o.material || !o.material.emissive) return;
    ensureUniqueMaterial(o);
    var origHex = o.material.emissive.getHex();
    var origI = o.material.emissiveIntensity || 0;
    o.material.emissive.setHex(hex);
    o.material.emissiveIntensity = 0.6;
    setTimeout(function () {
      if (o && o.material && o.material.emissive) {
        o.material.emissive.setHex(origHex);
        o.material.emissiveIntensity = origI;
      }
    }, ms);
  }
  function setMissedHighlight(root, prefix) {
    if (!root) return;
    root.traverse(function (o) {
      if (o.isMesh && o.name.indexOf(prefix) === 0 && o.material && o.material.emissive) {
        ensureUniqueMaterial(o);
        o.material.emissive.setHex(0xef3030);
        o.material.emissiveIntensity = 0.45;
      }
    });
  }
  function updateTweens(now) {
    for (var i = tweens.length - 1; i >= 0; i--) {
      var t = tweens[i];
      var k = Math.min(1, (now - t.start) / t.dur);
      var e = k * k * (3 - 2 * k);
      t.obj[t.prop] = t.from + (t.to - t.from) * e;
      if (k >= 1) { tweens.splice(i, 1); if (t.onDone) t.onDone(); }
    }
  }

  // -------------------------------------------------------------------------
  // PC controls (drag-to-look + WASD)
  // -------------------------------------------------------------------------
  var overlay = document.getElementById("overlay");
  var startBtn = document.getElementById("start-btn");
  var yaw = 0, pitch = 0;
  var dragging = false, lastMX = 0, lastMY = 0, dragMoveDist = 0;
  var usingPointerLock = false;
  var LOOK_SENS = 0.0025;
  var startTime = 0;
  var inVRMode = false;

  function dismissOverlay() {
    if (overlay.style.display === "none") return;
    overlay.style.display = "none";
    startTime = performance.now();
    var el = renderer.domElement;
    if (!inVRMode && el.requestPointerLock) {
      try { var p = el.requestPointerLock(); if (p && typeof p.then === "function") p.catch(function(){}); }
      catch (_) {}
    }
  }
  startBtn.addEventListener("click", dismissOverlay);

  document.addEventListener("pointerlockchange", function () {
    usingPointerLock = (document.pointerLockElement === renderer.domElement);
  });

  renderer.domElement.addEventListener("mousedown", function (e) {
    if (e.button !== 0 || inVRMode) return;
    if (overlay.style.display !== "none") { dismissOverlay(); return; }
    if (modalOpen()) return;
    if (!usingPointerLock) {
      dragging = true; lastMX = e.clientX; lastMY = e.clientY; dragMoveDist = 0;
    }
    e.preventDefault();
  });
  window.addEventListener("mouseup", function (e) {
    if (e.button !== 0 || inVRMode) return;
    if (modalOpen()) return;
    if (usingPointerLock) handleClick();
    else if (dragging) {
      if (dragMoveDist <= CLICK_DRAG_THRESHOLD_PX) handleClick();
      dragging = false;
    }
  });
  window.addEventListener("mousemove", function (e) {
    if (inVRMode) return;
    var dx, dy;
    if (usingPointerLock) { dx = e.movementX || 0; dy = e.movementY || 0; }
    else if (dragging) {
      dx = e.clientX - lastMX; dy = e.clientY - lastMY;
      lastMX = e.clientX; lastMY = e.clientY;
      dragMoveDist += Math.hypot(dx, dy);
    } else return;
    yaw -= dx * LOOK_SENS;
    pitch -= dy * LOOK_SENS;
    var lim = Math.PI / 2 - 0.05;
    if (pitch > lim) pitch = lim; if (pitch < -lim) pitch = -lim;
    camera.rotation.set(pitch, yaw, 0, "YXZ");
  });

  var keys = { w: false, a: false, s: false, d: false, shift: false };
  window.addEventListener("keydown", function (e) {
    var k = e.key.toLowerCase();
    if (k in keys) keys[k] = true;
    if (e.key === "Shift") keys.shift = true;
    if (e.key === "Escape") {
      if (document.pointerLockElement) document.exitPointerLock();
      if (modalOpen()) closeAllModals();
    }
    if (k === "h" || k === "?") { if (!modalOpen()) overlay.style.display = "flex"; }
  });
  window.addEventListener("keyup", function (e) {
    var k = e.key.toLowerCase();
    if (k in keys) keys[k] = false;
    if (e.key === "Shift") keys.shift = false;
  });

  // -------------------------------------------------------------------------
  // Collision (room AABBs)
  // -------------------------------------------------------------------------
  function inAnyRoom(bx, by) {
    var keysList = ["main", "prep", "door"];
    for (var i = 0; i < keysList.length; i++) {
      var r = ROOMS[keysList[i]];
      if (bx >= r.x1 && bx <= r.x2 && by >= r.z1 && by <= r.z2) return keysList[i];
    }
    return null;
  }
  function clampToRooms(prevX, prevZ, nextX, nextZ) {
    var outX = prevX, outZ = prevZ;
    if (inAnyRoom(nextX, -prevZ)) outX = nextX;
    if (inAnyRoom(outX, -nextZ))  outZ = nextZ;
    return [outX, outZ];
  }

  // -------------------------------------------------------------------------
  // PC raycasting (centre-screen)
  // -------------------------------------------------------------------------
  var pcRaycaster = new THREE.Raycaster();
  var screenCenter = new THREE.Vector2(0, 0);
  pcRaycaster.far = RAYCAST_MAX_DIST;
  var currentTarget = null;
  var currentTargetFixed = null;
  var crosshairEl = document.getElementById("crosshair");
  var tipEl = document.getElementById("target-tip");

  function findHazardForObject(obj) {
    while (obj) {
      if (obj.name) {
        for (var i = 0; i < HAZARDS.length; i++) {
          if (obj.name.indexOf(HAZARDS[i].prefix) === 0) return HAZARDS[i];
        }
      }
      obj = obj.parent;
    }
    return null;
  }

  function updateTargeting() {
    if (!labRoot || modalOpen()) {
      if (currentTarget) { currentTarget = null; crosshairEl.classList.remove("targeting"); tipEl.classList.remove("show"); }
      return;
    }
    pcRaycaster.setFromCamera(screenCenter, camera);
    var hits = pcRaycaster.intersectObjects(labRoot.children, true);
    var hazard = (hits.length > 0) ? findHazardForObject(hits[0].object) : null;
    var fixedState = hazard ? hazard.fixed : null;
    if (hazard !== currentTarget || fixedState !== currentTargetFixed) {
      currentTarget = hazard;
      currentTargetFixed = fixedState;
      if (hazard && !hazard.fixed) {
        crosshairEl.classList.add("targeting");
        tipEl.classList.add("show");
        tipEl.textContent = hazard.found ? "Click to revisit" : "Click to flag hazard";
      } else {
        crosshairEl.classList.remove("targeting");
        tipEl.classList.remove("show");
      }
    }
  }

  // -------------------------------------------------------------------------
  // Click handling (PC)
  // -------------------------------------------------------------------------
  var foundCount = 0, fixedCount = 0, wrongClicks = 0, completed = false;

  function handleClick() {
    if (overlay.style.display !== "none") return;
    if (currentTarget) openHazardModal(currentTarget);
    else {
      crosshairEl.classList.add("wrong");
      setTimeout(function () { crosshairEl.classList.remove("wrong"); }, 250);
      wrongClicks++;
      updateProgressUI();
    }
  }

  // -------------------------------------------------------------------------
  // Modals (PC)
  // -------------------------------------------------------------------------
  var hzModal = document.getElementById("hz-modal");
  var hzmTitle = document.getElementById("hzm-title");
  var hzmSub = document.getElementById("hzm-subtitle");
  var hzmWhy = document.getElementById("hzm-why");
  var hzmFix = document.getElementById("hzm-fix");
  var hzmFixBtn = document.getElementById("hzm-fix-btn");
  var hzmCloseBtn = document.getElementById("hzm-close-btn");
  var doneModal = document.getElementById("done-modal");
  var activeHazard = null;

  function modalOpen() { return hzModal.classList.contains("show") || doneModal.classList.contains("show"); }
  function closeAllModals() { hzModal.classList.remove("show"); doneModal.classList.remove("show"); activeHazard = null; }

  function openHazardModal(h) {
    activeHazard = h;
    hzmTitle.textContent = h.title;
    hzmWhy.textContent = h.why;
    hzmFix.textContent = h.fix;
    if (h.fixed) {
      hzmSub.textContent = "Already made safe";
      hzmFixBtn.style.display = "none";
      hzmCloseBtn.textContent = "Close";
    } else if (completed) {
      hzmSub.textContent = "Missed hazard — review";
      hzmFixBtn.style.display = "none";
      hzmCloseBtn.textContent = "Close";
    } else {
      hzmSub.textContent = h.found ? "Hazard re-opened" : "Hazard found";
      hzmFixBtn.style.display = "inline-block";
      hzmFixBtn.textContent = "Make safe";
      hzmCloseBtn.textContent = "Later";
    }
    hzModal.classList.add("show");
    if (!h.found) { h.found = true; foundCount++; updateProgressUI(); renderHazardList(); }
  }
  hzmCloseBtn.addEventListener("click", function () { hzModal.classList.remove("show"); activeHazard = null; });
  hzmFixBtn.addEventListener("click", function () {
    if (!activeHazard || activeHazard.fixed || !labRoot) { hzModal.classList.remove("show"); return; }
    activeHazard.fixed = true;
    fixedCount++;
    try { activeHazard.runFix(labRoot); } catch (e) { console.error("[fix] failed for", activeHazard.title, e); }
    updateProgressUI();
    renderHazardList();
    hzModal.classList.remove("show");
    activeHazard = null;
    if (fixedCount === HAZARDS.length && !completed) onComplete();
  });

  // -------------------------------------------------------------------------
  // VR controllers (laser + contextual trigger)
  // -------------------------------------------------------------------------
  var vrRaycaster = new THREE.Raycaster();
  vrRaycaster.far = TELEPORT_MAX_DIST;
  var floorPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  var tempMatrix = new THREE.Matrix4();
  var tempVec = new THREE.Vector3();

  // Laser geometry — reuse one buffer; per-controller line lets us recolour individually
  function buildLaser() {
    var geo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, -RAYCAST_MAX_DIST)
    ]);
    var mat = new THREE.LineBasicMaterial({ color: COLOR_LASER_DEFAULT, linewidth: 2 });
    return new THREE.Line(geo, mat);
  }
  function buildTip() {
    return new THREE.Mesh(
      new THREE.SphereGeometry(0.025, 12, 8),
      new THREE.MeshBasicMaterial({ color: COLOR_LASER_DEFAULT })
    );
  }

  var controllers = [];
  for (var ci = 0; ci < 2; ci++) {
    var ctl = renderer.xr.getController(ci);
    rig.add(ctl);
    var laser = buildLaser(); laser.name = "laser"; ctl.add(laser);
    var tip = buildTip(); tip.name = "tip"; tip.position.z = -2; ctl.add(tip);
    ctl.visible = false;
    ctl.userData.lastHit = null;  // {hazard?, floorPoint?}
    controllers.push(ctl);
  }

  function setLaserAppearance(ctl, color, tipDistance) {
    var laser = ctl.getObjectByName("laser");
    var tip = ctl.getObjectByName("tip");
    if (laser && laser.material) laser.material.color.setHex(color);
    if (tip && tip.material) tip.material.color.setHex(color);
    if (tip && tipDistance != null) tip.position.z = -Math.max(0.1, Math.min(tipDistance, RAYCAST_MAX_DIST));
  }

  function castFromController(ctl) {
    tempMatrix.identity().extractRotation(ctl.matrixWorld);
    vrRaycaster.ray.origin.setFromMatrixPosition(ctl.matrixWorld);
    vrRaycaster.ray.direction.set(0, 0, -1).applyMatrix4(tempMatrix);

    // Hazards/scene first (limited by RAYCAST_MAX_DIST)
    vrRaycaster.far = RAYCAST_MAX_DIST;
    if (labRoot) {
      var hits = vrRaycaster.intersectObjects(labRoot.children, true);
      if (hits.length > 0) {
        var hazard = findHazardForObject(hits[0].object);
        return { hazard: hazard, sceneHit: hits[0], distance: hits[0].distance };
      }
    }
    // Then floor plane (longer range for teleport)
    vrRaycaster.far = TELEPORT_MAX_DIST;
    var floorHit = new THREE.Vector3();
    if (vrRaycaster.ray.intersectPlane(floorPlane, floorHit)) {
      var distance = vrRaycaster.ray.origin.distanceTo(floorHit);
      if (distance <= TELEPORT_MAX_DIST) {
        var inside = inAnyRoom(floorHit.x, -floorHit.z);
        return { floorPoint: inside ? floorHit : null, floorPointRaw: floorHit, distance: distance };
      }
    }
    return { distance: RAYCAST_MAX_DIST };
  }

  function updateVRTargeting() {
    for (var i = 0; i < controllers.length; i++) {
      var ctl = controllers[i];
      var hit = castFromController(ctl);
      ctl.userData.lastHit = hit;
      if (hit.hazard && !hit.hazard.fixed) {
        setLaserAppearance(ctl, COLOR_LASER_HAZARD, hit.distance);
      } else if (hit.floorPoint) {
        setLaserAppearance(ctl, COLOR_LASER_FLOOR, hit.distance);
      } else {
        setLaserAppearance(ctl, COLOR_LASER_DEFAULT, RAYCAST_MAX_DIST);
      }
    }
  }

  function flagAndFixVR(h) {
    if (!h.found) { h.found = true; foundCount++; }
    if (!h.fixed && labRoot) {
      h.fixed = true; fixedCount++;
      try { h.runFix(labRoot); } catch (e) { console.error(e); }
      if (fixedCount === HAZARDS.length && !completed) onComplete();
    }
    updateProgressUI();
    renderHazardList();
  }

  function teleportTo(point) {
    // Account for current head offset within the rig so the user lands where they aimed
    var head = renderer.xr.getCamera();
    var headLocal = head.position.clone();
    rig.position.x = point.x - headLocal.x;
    rig.position.z = point.z - headLocal.z;
  }

  function onControllerSelectStart(ctl) {
    if (overlay.style.display !== "none") { dismissOverlay(); return; }
    var hit = ctl.userData.lastHit || castFromController(ctl);
    if (hit.hazard && !hit.hazard.fixed) {
      flagAndFixVR(hit.hazard);
    } else if (hit.floorPoint) {
      teleportTo(hit.floorPoint);
    } else if (hit.hazard && hit.hazard.fixed) {
      // already fixed — flash to confirm but no-op
    } else {
      wrongClicks++;
      updateProgressUI();
    }
  }
  controllers[0].addEventListener("selectstart", function () { onControllerSelectStart(controllers[0]); });
  controllers[1].addEventListener("selectstart", function () { onControllerSelectStart(controllers[1]); });

  // Show/hide PC HUD when entering/leaving VR
  renderer.xr.addEventListener("sessionstart", function () {
    inVRMode = true;
    if (document.pointerLockElement) document.exitPointerLock();
    controllers.forEach(function (c) { c.visible = true; });
    document.getElementById("crosshair").style.display = "none";
    document.getElementById("target-tip").style.display = "none";
    document.getElementById("hud").style.display = "none";
  });
  renderer.xr.addEventListener("sessionend", function () {
    inVRMode = false;
    controllers.forEach(function (c) { c.visible = false; });
    document.getElementById("crosshair").style.display = "";
    document.getElementById("target-tip").style.display = "";
    document.getElementById("hud").style.display = "";
  });

  // -------------------------------------------------------------------------
  // Hazard list panel
  // -------------------------------------------------------------------------
  var hazList = document.getElementById("haz-list");
  var hpFixed = document.getElementById("hp-fixed");
  var hpFound = document.getElementById("hp-found");
  var hpWrong = document.getElementById("hp-wrong");

  function renderHazardList() {
    hazList.innerHTML = "";
    HAZARDS.forEach(function (h) {
      var li = document.createElement("li");
      var box = document.createElement("span"); box.className = "box";
      var label = document.createElement("span");
      if (h.fixed) { li.classList.add("fixed"); box.textContent = "✓"; label.textContent = h.title; }
      else if (h.found) { li.classList.add("found"); box.textContent = "•"; label.textContent = h.title; }
      else if (completed) { li.classList.add("missed"); box.textContent = "!"; label.textContent = h.title; }
      else { box.textContent = "?"; label.textContent = "Hazard #" + h.id + " — find it"; label.style.color = "#7a7e85"; }
      li.appendChild(box); li.appendChild(label);
      hazList.appendChild(li);
    });
  }
  function updateProgressUI() {
    hpFixed.textContent = fixedCount;
    hpFound.textContent = foundCount;
    hpWrong.textContent = wrongClicks;
  }

  // -------------------------------------------------------------------------
  // Submit / Completion
  // -------------------------------------------------------------------------
  document.getElementById("haz-submit").addEventListener("click", function () { if (!completed) onComplete(); });

  function onComplete() {
    completed = true;
    var elapsed = Math.max(0, Math.round((performance.now() - startTime) / 1000));
    var mm = Math.floor(elapsed / 60), ss = elapsed % 60;
    var notFound = HAZARDS.filter(function (h) { return !h.found; });
    var foundUnfixed = HAZARDS.filter(function (h) { return h.found && !h.fixed; });
    var stats = document.getElementById("done-stats");
    stats.innerHTML =
      '<div class="stat-row"><span>Hazards fixed</span><b>' + fixedCount + ' / ' + HAZARDS.length + '</b></div>' +
      '<div class="stat-row"><span>Found but not fixed</span><b>' + foundUnfixed.length + '</b></div>' +
      '<div class="stat-row"><span>Missed</span><b>' + notFound.length + '</b></div>' +
      '<div class="stat-row"><span>Wrong flags</span><b>' + wrongClicks + '</b></div>' +
      '<div class="stat-row"><span>Time</span><b>' + (mm + 'm ' + ss + 's') + '</b></div>';
    var note = document.getElementById("done-note");
    if (notFound.length > 0) {
      note.textContent = "Missed hazards are highlighted in red — walk over and click each one to learn what it was.";
      notFound.forEach(function (h) { setMissedHighlight(labRoot, h.prefix); });
    } else if (foundUnfixed.length > 0) {
      note.textContent = "All hazards spotted — but " + foundUnfixed.length + " still need to be made safe.";
    } else {
      note.textContent = "All seven hazards spotted and made safe. Well done.";
    }
    renderHazardList();
    doneModal.classList.add("show");
  }
  document.getElementById("done-restart-btn").addEventListener("click", function () { location.reload(); });
  document.getElementById("done-review-btn").addEventListener("click", function () { doneModal.classList.remove("show"); });

  // -------------------------------------------------------------------------
  // Animation loop (single loop drives PC + VR via setAnimationLoop)
  // -------------------------------------------------------------------------
  var tmpForward = new THREE.Vector3();
  var tmpRight = new THREE.Vector3();
  var clock = new THREE.Clock();

  // Debug hook (harmless in production; used by automated visual checks).
  // Blender coords: bx east, by north. yawDeg 0 = north, 90 = west, -90 = east.
  window.__setView = function (bx, by, yawDeg, pitchDeg) {
    rig.position.set(bx, 0, -by);
    yaw = (yawDeg || 0) * Math.PI / 180;
    pitch = (pitchDeg || 0) * Math.PI / 180;
    camera.rotation.set(pitch, yaw, 0, "YXZ");
  };

  function tick() {
    var dt = Math.min(clock.getDelta(), 0.05);
    var now = performance.now();
    updateTweens(now);

    if (inVRMode) {
      updateVRTargeting();
      // Room HUD doesn't render in VR but keep state in sync if needed later
    } else if (overlay.style.display === "none" && !modalOpen()) {
      var fwd = 0, side = 0;
      if (keys.w) fwd += 1;
      if (keys.s) fwd -= 1;
      if (keys.d) side += 1;
      if (keys.a) side -= 1;
      if (fwd !== 0 || side !== 0) {
        camera.getWorldDirection(tmpForward);
        tmpForward.y = 0; tmpForward.normalize();
        tmpRight.crossVectors(tmpForward, camera.up).normalize();
        var speed = WALK_SPEED * (keys.shift ? SPRINT_MULT : 1);
        var dx = (tmpForward.x * fwd + tmpRight.x * side) * speed * dt;
        var dz = (tmpForward.z * fwd + tmpRight.z * side) * speed * dt;
        var px = rig.position.x, pz = rig.position.z;
        var clamped = clampToRooms(px, pz, px + dx, pz + dz);
        rig.position.x = clamped[0];
        rig.position.z = clamped[1];
      }
      var which = inAnyRoom(rig.position.x, -rig.position.z);
      hudRoom.textContent = which ? ROOMS[which].name : "—";
      updateTargeting();
    }

    renderer.render(scene, camera);
  }
  renderer.setAnimationLoop(tick);
})();
