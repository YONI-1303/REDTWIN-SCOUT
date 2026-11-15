import streamlit.components.v1 as components

SHAPE_WAVES_HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
html, body {
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: transparent;
}
canvas {
    display: block;
    width: 100%;
    height: 100%;
}
</style>
</head>
<body>
<canvas id="shape-waves"></canvas>
<script>
(() => {
  const canvas = document.getElementById("shape-waves");
  const ctx = canvas.getContext("2d", {
    alpha: true,
    desynchronized: true
  });

  let host;
  let hostDoc;
  let frame;

  try {
    host = window.parent;
    hostDoc = host.document;
    frame = window.frameElement;

    if (frame) {
      frame.id = "redtwin-shape-waves-frame";
      const set = (key, value) =>
        frame.style.setProperty(key, value, "important");

      set("position", "fixed");
      set("inset", "0");
      set("width", "100vw");
      set("height", "100vh");
      set("max-width", "none");
      set("border", "0");
      set("z-index", "0");
      set("pointer-events", "none");
      set("background", "transparent");
      set("margin", "0");
    }
  } catch (error) {
    console.warn("Shape Waves parent integration unavailable:", error);
    return;
  }

  const styleId = "redtwin-shape-waves-host-style";
  if (!hostDoc.getElementById(styleId)) {
    const style = hostDoc.createElement("style");
    style.id = styleId;
    style.textContent = `
      html, body { background: #090B16 !important; }
      .stApp, [data-testid="stAppViewContainer"],
      [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        background: transparent !important;
      }
      [data-testid="stSidebar"] {
        position: relative !important;
        z-index: 5 !important;
        background: rgba(9,11,22,.78) !important;
        backdrop-filter: blur(18px);
      }
      [data-testid="stHeader"] {
        position: relative !important;
        z-index: 6 !important;
        background: rgba(9,11,22,.20) !important;
        backdrop-filter: blur(12px);
      }
      [data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > div:not(:first-child) {
        position: relative !important;
        z-index: 1 !important;
      }
    `;
    hostDoc.head.appendChild(style);
  }

  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const mix = (a, b, t) => a + (b - a) * t;

  const violet = [105, 78, 190];
  const lavender = [190, 174, 255];
  const cyan = [103, 211, 226];
  const white = [239, 236, 255];

  const pointer = { x: -1000, y: -1000, energy: 0, last: 0 };
  const ripples = [];

  let width = 1;
  let height = 1;
  let dpr = 1;
  let time = 0;
  let lastFrame = 0;
  let animationFrame = 0;
  let reducedMotion = host.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  const cellSize = 25;

  function resize() {
    width = Math.max(1, host.innerWidth);
    height = Math.max(1, host.innerHeight);
    dpr = Math.min(host.devicePixelRatio || 1, 1.35);

    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = "100%";
    canvas.style.height = "100%";

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw(performance.now());
  }

  function hash(col, row) {
    const value = Math.sin(col * 127.1 + row * 311.7) * 43758.5453;
    return value - Math.floor(value);
  }

  function polygon(x, y, size, kind, color, alpha, intensity) {
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 0.65;

    if (intensity > 0.62) {
      ctx.shadowColor = "rgba(151,124,255,.55)";
      ctx.shadowBlur = 7 * intensity;
    } else {
      ctx.shadowBlur = 0;
    }

    ctx.beginPath();

    if (kind === 0) {
      ctx.rect(x - size / 2, y - size / 2, size, size);
    } else if (kind === 1) {
      ctx.arc(x, y, size / 2, 0, Math.PI * 2);
    } else {
      ctx.moveTo(x, y - size * 0.62);
      ctx.lineTo(x + size * 0.58, y + size * 0.42);
      ctx.lineTo(x - size * 0.58, y + size * 0.42);
      ctx.closePath();
    }

    ctx.fill();
    ctx.globalAlpha = alpha * 0.55;
    ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
  }

  function draw(now) {
    ctx.clearRect(0, 0, width, height);

    const t = time;
    const columns = Math.ceil(width / cellSize) + 1;
    const rows = Math.ceil(height / cellSize) + 1;

    pointer.energy *= reducedMotion ? 0.90 : 0.965;

    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < columns; col++) {
        const x = col * cellSize + cellSize / 2;
        const y = row * cellSize + cellSize / 2;

        const waveA = Math.sin(
          x * 0.008 + y * 0.003 - t * 0.72
        );
        const waveB = Math.sin(
          y * 0.009 - x * 0.003 + t * 0.47
        );
        const waveC = Math.cos(
          (x + y) * 0.006 - t * 0.29
        );

        const field = 0.5 + 0.5 * (
          waveA * 0.49 + waveB * 0.33 + waveC * 0.18
        );

        const dx = x - pointer.x;
        const dy = y - pointer.y;
        const distanceSquared = dx * dx + dy * dy;
        const radius = cellSize * 5.3;

        const magnet =
          Math.exp(-distanceSquared / (radius * radius)) *
          pointer.energy;

        let splash = 0;

        for (const ripple of ripples) {
          const age = (now - ripple.started) / 1000;
          const distance = Math.hypot(x - ripple.x, y - ripple.y);

          const ring = Math.sin((distance - age * 190) * 0.035);
          const falloff =
            Math.exp(-distance / 340) *
            Math.exp(-age / 1.75);

          splash += ring * falloff * ripple.strength;
        }

        const intensity = clamp(
          0.08 + field * 0.57 +
          magnet * 0.58 + Math.max(0, splash) * 0.75,
          0.06,
          1
        );

        const blend = clamp(field * 0.78 + magnet * 0.32, 0, 1);
        let r = mix(violet[0], lavender[0], blend);
        let g = mix(violet[1], lavender[1], blend);
        let b = mix(violet[2], lavender[2], blend);

        const highlight = clamp(magnet * 0.8 + Math.max(0, splash) * 0.25, 0, 1);
        r = mix(r, mix(cyan[0], white[0], highlight), highlight);
        g = mix(g, mix(cyan[1], white[1], highlight), highlight);
        b = mix(b, mix(cyan[2], white[2], highlight), highlight);

        const color = `rgb(${r | 0},${g | 0},${b | 0})`;
        const size = cellSize * (0.12 + intensity * 0.31);
        const alpha = 0.07 + intensity * 0.54;
        const kind = Math.floor(hash(col, row) * 3);

        polygon(x, y, size, kind, color, alpha, intensity);
      }
    }

    for (let i = ripples.length - 1; i >= 0; i--) {
      if (now - ripples[i].started > 2300) {
        ripples.splice(i, 1);
      }
    }
  }

  function tick(now) {
    animationFrame = 0;

    if (hostDoc.hidden) return;

    if (!reducedMotion) {
      if (lastFrame && now - lastFrame < 1000 / 30) {
        animationFrame = requestAnimationFrame(tick);
        return;
      }

      const delta = lastFrame
        ? Math.min((now - lastFrame) / 1000, 0.05)
        : 0.016;

      time += delta * 0.8;
      lastFrame = now;
    }

    draw(now);

    if (!reducedMotion) {
      animationFrame = requestAnimationFrame(tick);
    }
  }

  function wake() {
    if (!animationFrame && !reducedMotion && !hostDoc.hidden) {
      animationFrame = requestAnimationFrame(tick);
    }
  }

  function onPointerMove(event) {
    pointer.x = event.clientX;
    pointer.y = event.clientY;
    pointer.energy = 1;
    pointer.last = Date.now();

    if (reducedMotion) draw(performance.now());
  }

  function onPointerDown(event) {
    if (reducedMotion) return;

    ripples.push({
      x: event.clientX,
      y: event.clientY,
      started: performance.now(),
      strength: 1
    });

    if (ripples.length > 5) ripples.shift();
    wake();
  }

  function onVisibility() {
    if (hostDoc.hidden) {
      if (animationFrame) cancelAnimationFrame(animationFrame);
      animationFrame = 0;
      lastFrame = 0;
    } else {
      wake();
    }
  }

  host.addEventListener("pointermove", onPointerMove, { passive: true });
  host.addEventListener("pointerdown", onPointerDown, { passive: true });
  host.addEventListener("resize", resize, { passive: true });
  hostDoc.addEventListener("visibilitychange", onVisibility);

  host.matchMedia("(prefers-reduced-motion: reduce)")
    .addEventListener("change", event => {
      reducedMotion = event.matches;
      lastFrame = 0;
      if (reducedMotion && animationFrame) {
        cancelAnimationFrame(animationFrame);
        animationFrame = 0;
        draw(performance.now());
      } else {
        wake();
      }
    });

  resize();

  if (!reducedMotion) {
    wake();
  }
})();
</script>
</body>
</html>
"""

def inject_shape_waves_background():
    components.html(
        SHAPE_WAVES_HTML,
        width=1,
        height=1,
        scrolling=False
    )
