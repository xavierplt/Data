/* Boussole IESF — animations : courbes de niveau, boussole, apparitions au défilement,
   compteurs, tracé du chemin, thème. Tout se désactive avec prefers-reduced-motion. */
(() => {
  "use strict";

  const root = document.documentElement;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canIO = "IntersectionObserver" in window;
  const animate = !reduce && canIO;
  if (animate) root.classList.add("anim");
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const easeOut = (k) => 1 - Math.pow(1 - k, 3);

  // ------------------------------------------------------------------ thème
  const THEME_KEY = "boussole-theme";
  try { const t = localStorage.getItem(THEME_KEY); if (t === "light" || t === "dark") root.dataset.theme = t; } catch { /* stockage indisponible */ }
  const isDark = () => (root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
  function syncToggle() {
    document.querySelectorAll("[data-theme-toggle]").forEach((b) => {
      b.dataset.mode = isDark() ? "dark" : "light";
      b.setAttribute("aria-label", isDark() ? "Passer en thème clair" : "Passer en thème sombre");
    });
  }
  document.addEventListener("click", (e) => {
    if (!e.target.closest("[data-theme-toggle]")) return;
    const next = isDark() ? "light" : "dark";
    root.dataset.theme = next;
    try { localStorage.setItem(THEME_KEY, next); } catch { /* idem */ }
    syncToggle();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", syncToggle);

  // ------------------------------------------------------------------ bruit 3D (valeurs lissées)
  const perm = new Uint8Array(512);
  {
    const p = [...Array(256).keys()];
    let s = 1337;
    for (let i = 255; i > 0; i--) { s = (s * 16807) % 2147483647; const j = s % (i + 1); [p[i], p[j]] = [p[j], p[i]]; }
    for (let i = 0; i < 512; i++) perm[i] = p[i & 255];
  }
  const h3 = (i, j, k) => perm[(perm[(perm[i & 255] + j) & 255] + k) & 255] / 255;
  const fade = (t) => t * t * (3 - 2 * t);
  function vnoise(x, y, z) {
    const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
    const xf = fade(x - xi), yf = fade(y - yi), zf = fade(z - zi);
    const l = (a, b, t) => a + (b - a) * t;
    const c00 = l(h3(xi, yi, zi), h3(xi + 1, yi, zi), xf), c10 = l(h3(xi, yi + 1, zi), h3(xi + 1, yi + 1, zi), xf);
    const c01 = l(h3(xi, yi, zi + 1), h3(xi + 1, yi, zi + 1), xf), c11 = l(h3(xi, yi + 1, zi + 1), h3(xi + 1, yi + 1, zi + 1), xf);
    return l(l(c00, c10, yf), l(c01, c11, yf), zf);
  }

  // ------------------------------------------------------------------ courbes de niveau (marching squares)
  const pointer = { x: -9999, y: -9999, active: false };
  window.addEventListener("pointermove", (e) => { pointer.x = e.clientX; pointer.y = e.clientY; pointer.active = true; }, { passive: true });
  document.addEventListener("pointerleave", () => (pointer.active = false));

  const STYLES = {
    hero: { minor: "rgba(150,190,228,0.13)", major: "rgba(160,200,240,0.32)", glow: [236, 140, 72], cell: 13, scale: 0.0032, speed: 0.0022, interactive: true },
    cta: { minor: "rgba(150,190,228,0.12)", major: "rgba(160,200,240,0.26)", glow: [236, 140, 72], cell: 14, scale: 0.0036, speed: 0.0018, interactive: true },
    soft: { themed: true, cell: 16, scale: 0.0026, speed: 0.0012, interactive: false },
  };
  const instances = new Set();

  function contours(canvas) {
    if (canvas.dataset.ready) return;
    canvas.dataset.ready = "1";
    const st = STYLES[canvas.dataset.contours] || STYLES.hero;
    const ctx = canvas.getContext("2d");
    const seed = Math.random() * 50;
    let t = 0, w = 0, h = 0, dpr = 1, visible = false, frame = 0;
    const bump = { x: 0, y: 0, s: 0 };
    let grid = new Float32Array(0);

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth; h = canvas.clientHeight;
      if (!w || !h) return false;
      if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
        canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      }
      return true;
    }

    function draw() {
      if (!resize()) return;
      const cell = st.cell, cols = Math.ceil(w / cell) + 1, rows = Math.ceil(h / cell) + 1;
      if (grid.length !== cols * rows) grid = new Float32Array(cols * rows);
      const rect = canvas.getBoundingClientRect();
      if (st.interactive) {
        const inside = pointer.active && pointer.x > rect.left && pointer.x < rect.right && pointer.y > rect.top && pointer.y < rect.bottom;
        const tx = pointer.x - rect.left, ty = pointer.y - rect.top;
        if (bump.s < 0.01) { bump.x = tx; bump.y = ty; }
        bump.x += (tx - bump.x) * 0.08; bump.y += (ty - bump.y) * 0.08;
        bump.s += ((inside ? 1 : 0) - bump.s) * 0.05;
      }
      const r2 = 170 * 170;
      for (let j = 0; j < rows; j++) {
        for (let i = 0; i < cols; i++) {
          const x = i * cell, y = j * cell;
          let v = vnoise(x * st.scale + seed, y * st.scale, t) * 0.68 + vnoise(x * st.scale * 2.3 + 7, y * st.scale * 2.3 + 3, t * 1.6) * 0.32;
          if (bump.s > 0.01) { const dx = x - bump.x, dy = y - bump.y; v += 0.2 * bump.s * Math.exp(-(dx * dx + dy * dy) / r2); }
          grid[j * cols + i] = v;
        }
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      let minor = st.minor, major = st.major;
      if (st.themed) {
        const cs = getComputedStyle(canvas);
        minor = cs.getPropertyValue("--contour").trim() || "rgba(18,112,176,.08)";
        major = cs.getPropertyValue("--contour-2").trim() || "rgba(18,112,176,.16)";
      }
      const glowStroke = (base, alpha) => {
        if (!st.glow || bump.s < 0.02) return base;
        const g = ctx.createRadialGradient(bump.x, bump.y, 0, bump.x, bump.y, 240);
        const [r, gg, b] = st.glow;
        g.addColorStop(0, `rgba(${r},${gg},${b},${alpha * bump.s})`);
        g.addColorStop(1, base);
        return g;
      };
      const step = 0.042;
      let n = 0;
      for (let L = 0.08; L < 1.12; L += step, n++) {
        const isMajor = n % 4 === 0;
        ctx.beginPath();
        for (let j = 0; j < rows - 1; j++) {
          for (let i = 0; i < cols - 1; i++) {
            const a = grid[j * cols + i] - L, b = grid[j * cols + i + 1] - L;
            const c = grid[(j + 1) * cols + i + 1] - L, d = grid[(j + 1) * cols + i] - L;
            const idx = (a > 0 ? 8 : 0) | (b > 0 ? 4 : 0) | (c > 0 ? 2 : 0) | (d > 0 ? 1 : 0);
            if (idx === 0 || idx === 15) continue;
            const x = i * cell, y = j * cell;
            const T = () => [x + cell * (a / (a - b)), y];
            const R = () => [x + cell, y + cell * (b / (b - c))];
            const B = () => [x + cell * (d / (d - c)), y + cell];
            const Lf = () => [x, y + cell * (a / (a - d))];
            const seg = (p, q) => { ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]); };
            switch (idx) {
              case 1: case 14: seg(Lf(), B()); break;
              case 2: case 13: seg(B(), R()); break;
              case 3: case 12: seg(Lf(), R()); break;
              case 4: case 11: seg(T(), R()); break;
              case 6: case 9: seg(T(), B()); break;
              case 7: case 8: seg(T(), Lf()); break;
              case 5: seg(T(), R()); seg(Lf(), B()); break;
              case 10: seg(T(), Lf()); seg(B(), R()); break;
            }
          }
        }
        ctx.lineWidth = isMajor ? 1.1 : 0.7;
        ctx.strokeStyle = isMajor ? glowStroke(major, 0.85) : glowStroke(minor, 0.5);
        ctx.stroke();
      }
    }

    function loop() {
      if (!visible || !animate) return;
      frame++;
      if (frame % 2 === 0) { t += st.speed * 2; draw(); }
      requestAnimationFrame(loop);
    }

    const inst = {
      redraw: draw,
      setVisible(v) { const was = visible; visible = v; if (v && !was) { draw(); if (animate) requestAnimationFrame(loop); } },
    };
    instances.add(inst);
    if (canIO) new IntersectionObserver(([en]) => inst.setVisible(en.isIntersecting)).observe(canvas);
    else { visible = true; draw(); }
    return inst;
  }
  let resizeT;
  window.addEventListener("resize", () => { clearTimeout(resizeT); resizeT = setTimeout(() => instances.forEach((i) => i.redraw()), 120); });

  // ------------------------------------------------------------------ boussole
  const compass = document.querySelector("[data-compass]");
  let needle = null;
  if (compass) {
    const ns = "http://www.w3.org/2000/svg";
    let s = `<g class="rose">
      <circle r="192" class="ring"/><circle r="170" class="ring thin"/><circle r="118" class="ring thin"/>`;
    for (let d = 0; d < 360; d += 5) {
      const len = d % 30 === 0 ? 14 : 6, a = (d * Math.PI) / 180;
      const x1 = Math.sin(a) * 170, y1 = -Math.cos(a) * 170, x2 = Math.sin(a) * (170 + len), y2 = -Math.cos(a) * (170 + len);
      s += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" class="${d % 30 === 0 ? "tick major" : "tick"}"/>`;
      if (d % 30 === 0 && d % 90 !== 0) {
        s += `<text x="${(Math.sin(a) * 150).toFixed(1)}" y="${(-Math.cos(a) * 150 + 4).toFixed(1)}" class="deg">${d}</text>`;
      }
    }
    [["N", 0], ["E", 90], ["S", 180], ["O", 270]].forEach(([l, d]) => {
      const a = (d * Math.PI) / 180;
      s += `<text x="${(Math.sin(a) * 146).toFixed(1)}" y="${(-Math.cos(a) * 146 + 7).toFixed(1)}" class="card${l === "N" ? " north" : ""}">${l}</text>`;
    });
    s += `<path class="star" d="M0,-108 L14,-14 L108,0 L14,14 L0,108 L-14,14 L-108,0 L-14,-14 Z"/>
      <path class="star thin" d="M0,-70 L8,0 L0,70 L-8,0 Z" transform="rotate(45)"/></g>
      <g class="needle"><path class="n-north" d="M0,-96 L10,0 L-10,0 Z"/><path class="n-south" d="M0,96 L10,0 L-10,0 Z"/><circle r="6" class="hub"/></g>`;
    compass.innerHTML = s;
    needle = compass.querySelector(".needle");
    void ns;
  }
  let needleAngle = 0;
  function spinNeedle(ts) {
    if (!needle) return;
    const r = compass.getBoundingClientRect();
    let target;
    if (pointer.active && r.width) {
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      target = (Math.atan2(pointer.x - cx, -(pointer.y - cy)) * 180) / Math.PI;
    } else target = Math.sin(ts / 1400) * 18;
    let diff = ((target - needleAngle + 540) % 360) - 180;
    needleAngle += diff * 0.06;
    needle.setAttribute("transform", `rotate(${needleAngle.toFixed(2)})`);
  }

  // ------------------------------------------------------------------ titre découpé en mots
  function splitWords(el) {
    if (el.dataset.splitDone) return;
    el.dataset.splitDone = "1";
    const words = el.textContent.trim().split(/ +/);
    el.setAttribute("aria-label", el.textContent.trim());
    el.innerHTML = words.map((w, i) => `<span class="w" aria-hidden="true"><span style="--i:${i}">${w}</span></span>`).join(" ");
  }
  if (animate) document.querySelectorAll("[data-split]").forEach(splitWords);

  // ------------------------------------------------------------------ apparitions, barres, compteurs, courbe
  const AUTO = [
    ".report-head", ".block", ".summary-card", ".toc", ".how-steps li", ".objective", ".kpi", ".plan li", ".role",
    ".lever", ".bar-row", ".dot-row", ".stat", ".journey-head > *", ".how > .eyebrow", ".how > .section-title",
    ".cta-inner > *", ".prose > *", ".trail", ".ruler", ".verdict", "table.data tbody tr", ".legend",
  ].join(",");
  const GROW = ".bar-t > span, .lever-track > span, .score > span, .trail-bar > span, .dot";
  const COUNT = ".kpi-v, .trail-sal, .stat-v";

  function countUp(el) {
    if (el.dataset.counted) return;
    el.dataset.counted = "1";
    const txt = el.textContent;
    const m = txt.match(/^(.*?)(\d(?:[\d\s\u00a0\u202f]*\d)?(?:,\d+)?)(.*)$/s);
    if (!m) return;
    const [, pre, numStr, post] = m;
    const dec = (numStr.split(",")[1] || "").length;
    const target = parseFloat(numStr.replace(/[\s\u00a0\u202f]/g, "").replace(",", "."));
    if (!isFinite(target)) return;
    const fmt = new Intl.NumberFormat("fr-FR", { minimumFractionDigits: dec, maximumFractionDigits: dec });
    const t0 = performance.now(), dur = 1200;
    const tick = (now) => {
      const k = clamp((now - t0) / dur, 0, 1);
      el.textContent = k < 1 ? pre + fmt.format(target * easeOut(k)) + post : txt;
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function drawChart(el) {
    const rect = el.querySelector(".plot-reveal");
    const svg = el.querySelector("svg");
    if (!rect || !svg || el.dataset.drawn === "1") return;
    el.dataset.drawn = "1";
    const W = svg.viewBox.baseVal.width;
    const t0 = performance.now(), dur = 1600;
    const tick = (now) => {
      const k = clamp((now - t0) / dur, 0, 1);
      // Le graphique peut avoir été redessiné entre-temps : on cible toujours le rect courant.
      const r = el.querySelector(".plot-reveal");
      if (r) r.setAttribute("width", (W * easeOut(k)).toFixed(1));
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    void rect;
  }

  const io = canIO ? new IntersectionObserver((entries) => {
    for (const en of entries) {
      if (!en.isIntersecting) continue;
      const el = en.target;
      io.unobserve(el);
      el.classList.add("is-in");
      if (el.classList.contains("chart-draw")) drawChart(el);
      if (el.matches(COUNT)) countUp(el);
    }
  }, { rootMargin: "0px 0px -6% 0px", threshold: 0.08 }) : null;

  function stagger(els) {
    const byParent = new Map();
    els.forEach((el) => {
      const p = el.parentElement;
      if (!byParent.has(p)) byParent.set(p, []);
      byParent.get(p).push(el);
    });
    byParent.forEach((list) => list.forEach((el, i) => el.style.setProperty("--d", `${Math.min(i, 9) * 70}ms`)));
  }

  function refresh(scope = document) {
    // En-tête du bilan : panneau « nuit » avec ses propres courbes de niveau.
    scope.querySelectorAll(".report-head").forEach((head) => {
      if (!head.querySelector("canvas")) {
        const c = document.createElement("canvas");
        c.className = "contours";
        c.dataset.contours = "cta";
        c.setAttribute("aria-hidden", "true");
        head.prepend(c);
      }
    });
    scope.querySelectorAll("canvas[data-contours]").forEach(contours);
    if (!io) return;
    const fresh = [...scope.querySelectorAll(AUTO)].filter((el) => !el.classList.contains("is-in") && !el.classList.contains("reveal"));
    fresh.forEach((el) => { el.classList.add("reveal"); io.observe(el); });
    stagger(fresh);
    const grows = [...scope.querySelectorAll(GROW)].filter((el) => !el.classList.contains("grow"));
    grows.forEach((el) => { el.classList.add("grow"); io.observe(el); });
    stagger(grows);
    scope.querySelectorAll(COUNT).forEach((el) => { if (!el.dataset.counted && !el.dataset.watch) { el.dataset.watch = "1"; io.observe(el); } });
    scope.querySelectorAll(".chart-draw").forEach((el) => { if (el.dataset.drawn !== "1") io.observe(el); });
    onScroll();
  }

  // ------------------------------------------------------------------ défilement
  const bar = document.getElementById("scroll-progress");
  const topbar = document.getElementById("topbar");
  const heroBand = document.querySelector(".hero-band");
  const journey = document.querySelector(".journey");
  const jPath = journey?.querySelector(".journey-path");
  const walker = journey?.querySelector(".walker");
  const stations = journey ? [...journey.querySelectorAll(".journey-stations span")] : [];
  let ticking = false;

  function onScroll() {
    ticking = false;
    const y = window.scrollY, max = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.transform = `scaleX(${max > 0 ? clamp(y / max, 0, 1) : 0})`;
    const home = document.body.dataset.view === "home";
    topbar?.classList.toggle("is-scrolled", y > 8);
    topbar?.classList.toggle("over-hero", home && heroBand && y < heroBand.offsetHeight - 72);
    if (!home) return;
    if (compass && animate) compass.style.setProperty("--spin", `${(y * 0.08).toFixed(2)}deg`);
    if (heroBand && animate) heroBand.style.setProperty("--py", `${(y * 0.25).toFixed(1)}px`);

    if (journey && journey.offsetParent !== null) {
      const r = journey.getBoundingClientRect();
      const p = animate ? clamp((innerHeight * 0.78 - r.top) / (r.height * 0.75), 0, 1) : 1;
      journey.style.setProperty("--p", p.toFixed(4));
      if (jPath) jPath.style.strokeDashoffset = (1 - p).toFixed(4);
      const cards = journey.querySelectorAll(".stage-card");
      cards.forEach((c, i) => c.classList.toggle("is-on", p >= (i + 0.25) / 5.25));
      stations.forEach((s, i) => s.classList.toggle("is-on", p >= (i + 0.25) / 5.25));
      if (walker && jPath && jPath.getTotalLength) {
        const svg = jPath.ownerSVGElement, box = svg.getBoundingClientRect();
        const L = jPath.getTotalLength();
        const pt = jPath.getPointAtLength(L * clamp(p, 0.001, 1));
        walker.style.transform = `translate(${((pt.x / 1000) * box.width).toFixed(1)}px, ${((pt.y / 120) * box.height).toFixed(1)}px)`;
      }
    }
  }
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  window.addEventListener("resize", () => requestAnimationFrame(onScroll));

  // Légère parallaxe de la carte du hero et rotation de l'aiguille.
  const trail = document.querySelector(".hero .trail");
  function ambient(ts) {
    spinNeedle(ts);
    if (trail && pointer.active && document.body.dataset.view === "home" && window.scrollY < 900) {
      const dx = (pointer.x / innerWidth - 0.5) * 2, dy = (pointer.y / innerHeight - 0.5) * 2;
      trail.style.setProperty("--tx", `${(dx * -6).toFixed(2)}px`);
      trail.style.setProperty("--ty", `${(dy * -6).toFixed(2)}px`);
    }
    requestAnimationFrame(ambient);
  }
  if (animate) requestAnimationFrame(ambient);

  syncToggle();
  window.BoussoleMotion = { refresh };
})();
