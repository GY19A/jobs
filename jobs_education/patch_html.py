import os
import shutil

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

src_html = os.path.join(script_dir, '..', 'site', 'index.html')
dst_html = os.path.join(script_dir, 'site', 'index.html')
src_data = os.path.join(script_dir, '..', 'site', 'data.json')
dst_data = os.path.join(script_dir, 'site', 'data.json')

# Restore perfectly original data and HTML
shutil.copy2(src_data, dst_data)
shutil.copy2(src_html, dst_html)

with open(dst_html, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add the new button to the Toggle list (keeping Treemap as active default)
html = html.replace(
'''  <div class="view-toggle">
    <button class="active" onclick="setView('treemap')">Treemap</button>
    <button onclick="setView('scatter')">Exposure vs Outlook</button>
  </div>''',
'''  <div class="view-toggle">
    <button onclick="setView('treemap')">Treemap</button>
    <button onclick="setView('scatter')">Exposure vs Outlook</button>
    <button class="active" onclick="setView('paradox')">Education Paradox</button>
  </div>'''
)

# Set Education Paradox as the default view
html = html.replace(
  'let currentView = "treemap";',
  'let currentView = "paradox";'
)

# 2. Add Paradox Logic before Column View section
paradox_logic = '''
// ── PARADOX VIEW ────────────────────────────────────────────────────────

let pdxRects = [];

function layoutParadox() {
  const sidebarW = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sidebar-w'));
  const w = (window.innerWidth - sidebarW);
  const h = window.innerHeight;

  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";

  const pad = { top: 20, bottom: 40, left: 15, right: 15 };
  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;
  const colGap = 10;

  // Fully expanded education tiers ordered from lowest to highest
  const eduGroups = [
    { label: "No credential", match: "No formal educational credential" },
    { label: "High school", match: "High school diploma or equivalent" },
    { label: "Postsec cert", match: "Postsecondary nondegree award" },
    { label: "Some college", match: "Some college, no degree" },
    { label: "Associate's", match: "Associate's degree" },
    { label: "Bachelor's", match: "Bachelor's degree" },
    { label: "Master's", match: "Master's degree" },
    { label: "Doctoral/Prof", match: "Doctoral or professional degree" }
  ];
  
  const numCols = eduGroups.length;
  const byEdu = {};
  eduGroups.forEach((g, idx) => byEdu[idx] = []);
  
  for (const d of data) {
    if (d.exposure == null || d.education == null) continue;
    
    // Find matching group index
    let gIndex = -1;
    for (let i = 0; i < eduGroups.length; i++) {
        if (d.education === eduGroups[i].match) {
            gIndex = i; break;
        }
    }
    
    if (gIndex !== -1) {
        byEdu[gIndex].push(d);
    }
  }

  const colJobsSums = eduGroups.map((g, i) => byEdu[i].reduce((s, d) => s + (d.jobs || 0), 0));
  const maxJobsInTier = Math.max(...colJobsSums);

  const totalGap = colGap * (numCols - 1);
  const colW = (plotW - totalGap) / numCols;

  pdxRects = [];
  let cx = pad.left;

  for (let i = 0; i < numCols; i++) {
    const items = byEdu[i];
    items.sort((a, b) => (a.exposure || 0) - (b.exposure || 0));

    let currentJobs = 0;
    for (const d of items) {
      const jobs = d.jobs || 0;
      const colJobs = colJobsSums[i];
      const itemH = colJobs > 0 ? (jobs / colJobs) * plotH : 0;
      if (itemH < 0.2) { currentJobs += jobs; continue; }
      
      const cy = pad.top + plotH - ((currentJobs + jobs) / colJobs) * plotH;
      pdxRects.push({ ...d, rx: cx, ry: cy, rw: colW, rh: itemH });
      currentJobs += jobs;
    }
    cx += colW + colGap;
  }
  pdxRects._meta = { eduGroups, pad, colJobsSums, colW, colGap };
}

function drawParadox() {
  const w = canvas.width;
  const h = canvas.height;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = "#0a0a0f";
  ctx.fillRect(0, 0, w / dpr, h / dpr);

  const meta = pdxRects._meta;
  if (!meta) return;



  ctx.font = "500 11px -apple-system, system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "bottom";

  let cx = meta.pad.left;
  for (let i = 0; i < meta.eduGroups.length; i++) {
    const isSmall = meta.colW < 60;
    
    ctx.fillStyle = "rgba(255,255,255,0.9)";
    if (isSmall) {
        // Simple label if space is tight
        ctx.fillText(meta.eduGroups[i].label, cx + meta.colW / 2, canvas.height/dpr - 15);
    } else {
        ctx.fillText(meta.eduGroups[i].label, cx + meta.colW / 2, canvas.height/dpr - 15);
        ctx.font = "400 9px -apple-system, system-ui, sans-serif";
        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.fillText(`${formatNumber(meta.colJobsSums[i])}`, cx + meta.colW / 2, canvas.height/dpr - 4);
        ctx.font = "500 11px -apple-system, system-ui, sans-serif";
    }

    cx += meta.colW + meta.colGap;
  }

  const gap = 0.5;
  for (const r of pdxRects) {
    const isHovered = r === hovered;
    const rx = r.rx;
    const ry = r.ry + gap;
    const rw = r.rw;
    const rh = r.rh - gap * 2;
    if (rw <= 0 || rh <= 0) continue;

    const fillAlpha = isHovered ? 0.9 : 0.7;
    ctx.fillStyle = exposureColorCSS(r.exposure, fillAlpha);
    ctx.fillRect(rx, ry, rw, rh);

    if (isHovered) {
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.strokeRect(rx, ry, rw, rh);
    }
    
    if (rw > 35 && rh > 14) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(rx + 2, ry + 2, rw - 4, rh - 4);
      ctx.clip();
      
      const maxW = rw - 8;
      let fontSize = Math.min(11, Math.max(7, Math.min(rw / 8, rh / 2.5)));
      ctx.fillStyle = isHovered ? "#fff" : "rgba(255,255,255,0.85)";
      ctx.textBaseline = "middle";
      ctx.textAlign = "center";

      // Shrink font until text fits, down to minimum 7px
      let text = r.title;
      ctx.font = `500 ${fontSize}px -apple-system, system-ui, sans-serif`;
      while (fontSize > 7 && ctx.measureText(text).width > maxW) {
        fontSize -= 0.5;
        ctx.font = `500 ${fontSize}px -apple-system, system-ui, sans-serif`;
      }

      // If still too wide, truncate with ellipsis
      if (ctx.measureText(text).width > maxW) {
        while (text.length > 1 && ctx.measureText(text + "…").width > maxW) {
          text = text.slice(0, -1);
        }
        text = text + "…";
      }

      ctx.fillText(text, rx + rw/2, ry + rh/2);
      ctx.restore();
    }
  }
}

function hitTestParadox(mx, my) {
  const sidebarW = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sidebar-w'));
  const cx = mx - sidebarW;
  const cy = my;
  for (let i = pdxRects.length - 1; i >= 0; i--) {
    const r = pdxRects[i];
    if (cx >= r.rx && cx < r.rx + r.rw && cy >= r.ry && cy < r.ry + r.rh) {
      return r;
    }
  }
  return null;
}

// ── Column view (exposure x outlook) ────────────────────────────────────
'''
html = html.replace('''// ── Column view (exposure x outlook) ────────────────────────────────────''', paradox_logic)

# 3. Handle Events
events_old = '''canvas.addEventListener("mousemove", (e) => {
  const hit = currentView === "treemap" ? hitTest(e.clientX, e.clientY) : hitTestColumns(e.clientX, e.clientY);
  if (hit !== hovered) {
    hovered = hit;
    currentView === "treemap" ? draw() : drawColumns();
  }
  if (hovered) {
    showTooltip(hovered, e.clientX, e.clientY);
    canvas.style.cursor = "pointer";
  } else {
    hideTooltip();
    canvas.style.cursor = "default";
  }
});

canvas.addEventListener("click", (e) => {
  const hit = currentView === "treemap" ? hitTest(e.clientX, e.clientY) : hitTestColumns(e.clientX, e.clientY);
  if (hit && hit.url) {
    window.open(hit.url, "_blank");
  }
});

canvas.addEventListener("mouseleave", () => {
  hovered = null;
  hideTooltip();
  currentView === "treemap" ? draw() : drawColumns();
});

function resize() {
  dpr = window.devicePixelRatio || 1;
  if (currentView === "treemap") {
    layout();
    draw();
  } else {
    layoutColumns();
    drawColumns();
  }
}'''

events_new = '''function getHitTarget(e) {
  if (currentView === "treemap") return hitTest(e.clientX, e.clientY);
  if (currentView === "scatter") return hitTestColumns(e.clientX, e.clientY);
  return hitTestParadox(e.clientX, e.clientY);
}

function redrawCurrentView() {
  if (currentView === "treemap") draw();
  else if (currentView === "scatter") drawColumns();
  else drawParadox();
}

canvas.addEventListener("mousemove", (e) => {
  const hit = getHitTarget(e);
  if (hit !== hovered) {
    hovered = hit;
    redrawCurrentView();
  }
  if (hovered) {
    showTooltip(hovered, e.clientX, e.clientY);
    canvas.style.cursor = "pointer";
  } else {
    hideTooltip();
    canvas.style.cursor = "default";
  }
});

canvas.addEventListener("click", (e) => {
  const hit = getHitTarget(e);
  if (hit && hit.url) {
    window.open(hit.url, "_blank");
  }
});

canvas.addEventListener("mouseleave", () => {
  hovered = null;
  hideTooltip();
  redrawCurrentView();
});

function resize() {
  dpr = window.devicePixelRatio || 1;
  if (currentView === "treemap") { layout(); draw(); }
  else if (currentView === "scatter") { layoutColumns(); drawColumns(); }
  else { layoutParadox(); drawParadox(); }
}'''

html = html.replace(events_old, events_new)
html = html.replace('fetch("data.json")', 'fetch("data.json?v=" + Date.now())')

with open(dst_html, 'w', encoding='utf-8') as f:
    f.write(html)
print("Patch successfully applied!")
