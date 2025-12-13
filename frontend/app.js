

const API_BASE_URL = "https://pixel-bria.onrender.com"; 

const statusEl = document.getElementById("status");
const previewPseudoEl = document.getElementById("preview-pseudo");
const previewPerfectEl = document.getElementById("preview-perfect");
const previewNobgEl = document.getElementById("preview-nobg");
const previewGrid = document.getElementById("preview-grid");
const promptEl = document.getElementById("prompt");
const seedEl = document.getElementById("seed");
const gridEl = document.querySelector(".grid");
const promptPanelEl = document.querySelector(".prompt-panel");

let lastImageName = null;
let lastEditableName = null;
let lastNobgName = null;
let currentStyle = "16bit";
let currentStructuredPrompt = null;

// Store image URLs for download
const imageUrls = {
  pseudo: null,
  perfect: null,
  nobg: null,
  svg: null
};

const previewState = {
  pseudo: { scale: 1, img: null, isDragging: false, lastX: 0, lastY: 0, dragSetup: false },
  perfect: { scale: 1, img: null, isDragging: false, lastX: 0, lastY: 0, dragSetup: false },
  nobg: { scale: 1, img: null, isDragging: false, lastX: 0, lastY: 0, dragSetup: false },
};

// Grid overlay threshold - show grid when scale >= this value
const GRID_THRESHOLD = 8;

function setStatus(text, isError = false) {
  statusEl.textContent = text || "";
  statusEl.style.color = isError ? "#ff7b7b" : "var(--muted)";
}

// ========================================
// Loading State Management
// ========================================

function showLoading(cardType, message = "Processing...") {
  const cardMap = {
    pseudo: ".pseudo-card",
    perfect: ".perfect-card",
    nobg: ".nobg-card"
  };
  
  const card = document.querySelector(cardMap[cardType]);
  if (!card) return;
  
  card.classList.add("loading");
}

function hideLoading(cardType) {
  const cardMap = {
    pseudo: ".pseudo-card",
    perfect: ".perfect-card",
    nobg: ".nobg-card"
  };
  
  const card = document.querySelector(cardMap[cardType]);
  if (!card) return;
  
  card.classList.remove("loading");
}

// ========================================
// Structured Prompt Display
// ========================================

function countWords(obj) {
  const text = JSON.stringify(obj);
  return text.split(/\s+/).filter(w => w.length > 0).length;
}

function escapeHtml(str) {
  if (typeof str !== 'string') return str;
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function formatValue(val) {
  if (Array.isArray(val)) {
    return val.map(v => typeof v === 'object' ? JSON.stringify(v) : v).join(', ');
  }
  if (typeof val === 'object' && val !== null) {
    return JSON.stringify(val);
  }
  return String(val);
}

function renderField(label, value) {
  if (value === undefined || value === null || value === '') return '';
  return `<div class="sp-field"><span class="sp-field-label">${escapeHtml(label)}:</span><span class="sp-field-value">${escapeHtml(formatValue(value))}</span></div>`;
}

function renderObject(obj, index) {
  let html = `<div class="sp-object"><div class="sp-object-title">Object ${index + 1}</div>`;
  for (const [key, value] of Object.entries(obj)) {
    html += renderField(key, value);
  }
  html += '</div>';
  return html;
}

function displayStructuredPrompt(sp) {
  if (!sp) {
    document.getElementById('structured-prompt-section').style.display = 'none';
    return;
  }

  currentStructuredPrompt = sp;
  const section = document.getElementById('structured-prompt-section');
  section.style.display = 'block';
  // Start collapsed by default
  section.classList.add('collapsed');

  // Word count
  const wordCount = countWords(sp);
  document.getElementById('sp-word-count').textContent = `${wordCount} Words`;

  // General section
  const generalFields = ['short_description', 'style_medium', 'artistic_style', 'context', 'background_setting'];
  let generalHtml = '';
  let generalCount = 0;
  for (const field of generalFields) {
    if (sp[field]) {
      generalHtml += renderField(field.replace(/_/g, ' '), sp[field]);
      generalCount++;
    }
  }
  document.getElementById('sp-general').innerHTML = generalHtml || '<div class="sp-field">No general data</div>';
  document.getElementById('sp-count-general').textContent = generalCount;

  // Objects section
  const objects = sp.objects || [];
  let objectsHtml = '';
  for (let i = 0; i < objects.length; i++) {
    objectsHtml += renderObject(objects[i], i);
  }
  document.getElementById('sp-objects').innerHTML = objectsHtml || '<div class="sp-field">No objects</div>';
  document.getElementById('sp-count-objects').textContent = `{ } ${objects.length}`;

  // Lighting section
  const lighting = sp.lighting || {};
  let lightingHtml = '';
  let lightingCount = 0;
  for (const [key, value] of Object.entries(lighting)) {
    lightingHtml += renderField(key, value);
    lightingCount++;
  }
  document.getElementById('sp-lighting').innerHTML = lightingHtml || '<div class="sp-field">No lighting data</div>';
  document.getElementById('sp-count-lighting').textContent = `{ } ${lightingCount}`;

  // Aesthetics section
  const aesthetics = sp.aesthetics || {};
  const photoChars = sp.photographic_characteristics || {};
  let aestheticsHtml = '';
  let aestheticsCount = 0;
  for (const [key, value] of Object.entries(aesthetics)) {
    aestheticsHtml += renderField(key, value);
    aestheticsCount++;
  }
  for (const [key, value] of Object.entries(photoChars)) {
    aestheticsHtml += renderField(key, value);
    aestheticsCount++;
  }
  document.getElementById('sp-aesthetics').innerHTML = aestheticsHtml || '<div class="sp-field">No aesthetics data</div>';
  document.getElementById('sp-count-aesthetics').textContent = `{ } ${aestheticsCount}`;

  // JSON code view
  const jsonPre = document.getElementById('sp-json');
  jsonPre.innerHTML = syntaxHighlightJson(JSON.stringify(sp, null, 2));
}

function syntaxHighlightJson(json) {
  return json
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?)/g, (match) => {
      if (match.endsWith(':')) {
        return `<span class="json-key">${escapeHtml(match)}</span>`;
      }
      return `<span class="json-string">${escapeHtml(match)}</span>`;
    })
    .replace(/\b(\d+)\b/g, '<span class="json-number">$1</span>')
    .replace(/[{}\[\]]/g, '<span class="json-bracket">$&</span>');
}

// Structured prompt toggle handlers
// Header click to expand/collapse the entire section
document.getElementById('sp-header-toggle')?.addEventListener('click', (e) => {
  // Don't collapse if clicking on action buttons
  if (e.target.closest('.sp-actions')) return;
  
  const section = document.getElementById('structured-prompt-section');
  section.classList.toggle('collapsed');
});

document.getElementById('sp-toggle-code')?.addEventListener('click', (e) => {
  e.stopPropagation(); // Prevent header toggle
  const btn = document.getElementById('sp-toggle-code');
  const tree = document.getElementById('sp-tree');
  const code = document.getElementById('sp-code');
  
  if (code.style.display === 'none') {
    code.style.display = 'block';
    tree.style.display = 'none';
    btn.classList.add('active');
  } else {
    code.style.display = 'none';
    tree.style.display = 'block';
    btn.classList.remove('active');
  }
});

document.getElementById('sp-copy')?.addEventListener('click', (e) => {
  e.stopPropagation(); // Prevent header toggle
  if (currentStructuredPrompt) {
    navigator.clipboard.writeText(JSON.stringify(currentStructuredPrompt, null, 2));
    const btn = document.getElementById('sp-copy');
    const original = btn.textContent;
    btn.textContent = '✓';
    setTimeout(() => btn.textContent = original, 1500);
  }
});

// Category expand/collapse
document.querySelectorAll('.sp-category-header').forEach(header => {
  header.addEventListener('click', () => {
    const category = header.closest('.sp-category');
    category.classList.toggle('expanded');
  });
});

function updateZoomSlider(key) {
  const slider = document.getElementById(`zoom-slider-${key}`);
  const state = previewState[key];
  if (slider) {
    slider.value = state.scale;
  }
}

function updateGridOverlay(key) {
  const state = previewState[key];
  const overlay = document.getElementById(`grid-overlay-${key}`);
  const img = state.img;
  
  if (!overlay || !img) return;
  
  // Show grid when zoomed in enough to see individual pixels (8x or higher)
  if (state.scale >= GRID_THRESHOLD && img.naturalWidth && img.naturalHeight) {
    const displayW = img.naturalWidth * state.scale;
    const displayH = img.naturalHeight * state.scale;
    
    overlay.width = displayW;
    overlay.height = displayH;
    overlay.style.width = `${displayW}px`;
    overlay.style.height = `${displayH}px`;
    
    // Position overlay exactly over the image
    overlay.style.left = `${img.offsetLeft}px`;
    overlay.style.top = `${img.offsetTop}px`;
    
    const ctx = overlay.getContext("2d");
    ctx.clearRect(0, 0, displayW, displayH);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
    ctx.lineWidth = 1;
    
    // Draw vertical lines
    for (let x = 0; x <= img.naturalWidth; x++) {
      ctx.beginPath();
      ctx.moveTo(x * state.scale + 0.5, 0);
      ctx.lineTo(x * state.scale + 0.5, displayH);
      ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = 0; y <= img.naturalHeight; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * state.scale + 0.5);
      ctx.lineTo(displayW, y * state.scale + 0.5);
      ctx.stroke();
    }
    
    overlay.classList.add("visible");
  } else if (overlay) {
    overlay.classList.remove("visible");
  }
}

function applyScale(key) {
  const state = previewState[key];
  const img = state.img;
  if (!img || !img.naturalWidth || !img.naturalHeight) return;
  
  // Get max scale from the slider
  const slider = document.getElementById(`zoom-slider-${key}`);
  const maxScale = slider ? parseFloat(slider.max) : 32;
  
  const scale = Math.max(0.25, Math.min(maxScale, Math.round(state.scale * 4) / 4)); // snap to quarter steps, clamp
  state.scale = scale;
  
  const wrapper = img.parentElement;
  const container = wrapper ? wrapper.parentElement : null;
  if (!container) return;
  
  const newW = img.naturalWidth * scale;
  const newH = img.naturalHeight * scale;
  const viewW = container.clientWidth;
  const viewH = container.clientHeight;
  
  // Store previous scroll ratios for zoom centering
  const prevScrollX = container.scrollLeft;
  const prevScrollY = container.scrollTop;
  const prevImgW = parseFloat(img.style.width) || img.naturalWidth;
  const prevImgH = parseFloat(img.style.height) || img.naturalHeight;
  const centerRatioX = prevImgW > viewW ? (prevScrollX + viewW / 2) / prevImgW : 0.5;
  const centerRatioY = prevImgH > viewH ? (prevScrollY + viewH / 2) / prevImgH : 0.5;

  // Set image size
  img.style.width = `${newW}px`;
  img.style.height = `${newH}px`;
  
  // Size wrapper: if image smaller than viewport, center it; otherwise match image size
  const wrapperW = Math.max(newW, viewW);
  const wrapperH = Math.max(newH, viewH);
  wrapper.style.width = `${wrapperW}px`;
  wrapper.style.height = `${wrapperH}px`;
  
  // Center image within wrapper using padding when smaller than viewport
  if (newW < viewW) {
    img.style.marginLeft = `${(viewW - newW) / 2}px`;
  } else {
    img.style.marginLeft = '0';
  }
  if (newH < viewH) {
    img.style.marginTop = `${(viewH - newH) / 2}px`;
  } else {
    img.style.marginTop = '0';
  }

  // Scroll to maintain center position
  requestAnimationFrame(() => {
    if (newW > viewW) {
      container.scrollLeft = Math.max(0, Math.min(centerRatioX * newW - viewW / 2, newW - viewW));
    } else {
      container.scrollLeft = 0;
    }
    if (newH > viewH) {
      container.scrollTop = Math.max(0, Math.min(centerRatioY * newH - viewH / 2, newH - viewH));
    } else {
      container.scrollTop = 0;
    }
  });
  
  updateZoomSlider(key);
  updateGridOverlay(key);
}

function setupDragNavigation(container, key) {
  const state = previewState[key];
  if (state.dragSetup) return;
  state.dragSetup = true;
  
  container.addEventListener("mousedown", (e) => {
    if (e.target.tagName === "IMG" || e.target.tagName === "CANVAS" || e.target.classList.contains("img-wrapper") || e.target === container) {
      state.isDragging = true;
      state.lastX = e.clientX;
      state.lastY = e.clientY;
      container.style.cursor = "grabbing";
      e.preventDefault();
    }
  });
  
  container.addEventListener("mousemove", (e) => {
    if (state.isDragging) {
      const dx = e.clientX - state.lastX;
      const dy = e.clientY - state.lastY;
      container.scrollLeft -= dx;
      container.scrollTop -= dy;
      state.lastX = e.clientX;
      state.lastY = e.clientY;
    }
  });
  
  container.addEventListener("mouseup", () => {
    state.isDragging = false;
    container.style.cursor = "grab";
  });
  
  container.addEventListener("mouseleave", () => {
    state.isDragging = false;
    container.style.cursor = "grab";
  });
  
  // Ctrl+Scroll zoom with adaptive step
  container.addEventListener("wheel", (e) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -1 : 1;
      // Adaptive zoom step: larger steps at higher zoom levels
      let zoomStep;
      if (state.scale >= 16) {
        zoomStep = 4;
      } else if (state.scale >= 8) {
        zoomStep = 2;
      } else if (state.scale >= 2) {
        zoomStep = 0.5;
      } else {
        zoomStep = 0.25;
      }
      state.scale = Math.min(64, Math.max(0.25, state.scale + delta * zoomStep));
      applyScale(key);
    }
  }, { passive: false });
}

function showPreview(container, url, label, key) {
  // Clear container completely
  container.innerHTML = "";
  
  // Create wrapper for proper centering and scrolling
  const wrapper = document.createElement("div");
  wrapper.className = "img-wrapper";
  
  // Create grid overlay
  const overlay = document.createElement("canvas");
  overlay.className = "pixel-grid-overlay";
  overlay.id = `grid-overlay-${key}`;
  
  const img = document.createElement("img");
  img.alt = label || "preview";
  img.onload = () => {
    previewState[key].img = img;
    // Start pseudo at 0.25x, perfect at 1x
    previewState[key].scale = (key === "pseudo") ? 0.25 : 1;
    updateZoomSlider(key);
    applyScale(key);
    setupDragNavigation(container, key);
  };
  img.src = url;
  previewState[key].img = img;
  
  wrapper.appendChild(img);
  wrapper.appendChild(overlay);
  container.appendChild(wrapper);
}

async function postJson(path, body) {
  const url = API_BASE_URL ? `${API_BASE_URL}${path}` : path;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg);
  }
  return res.json();
}

document.getElementById("style-chips").addEventListener("click", (e) => {
  if (e.target.dataset.style) {
    document.querySelectorAll("#style-chips button").forEach((btn) => btn.classList.remove("active"));
    e.target.classList.add("active");
    currentStyle = e.target.dataset.style;
  }
});

document.getElementById("btn-generate").addEventListener("click", async () => {
  const prompt = promptEl.value.trim();
  if (!prompt) {
    setStatus("Prompt is required.", true);
    return;
  }
  setStatus("Generating pseudo pixel art...");
  showLoading("pseudo", "Generating pixel art");
  try {
    const payload = {
      prompt,
      style: currentStyle,
    };
    const seed = seedEl.value.trim();
    if (seed) payload.seed = Number(seed);

    const data = await postJson("/api/generate", payload);
    hideLoading("pseudo");
    lastImageName = data.image_name;
    // Store image URL for download
    imageUrls.pseudo = data.image_url;
    imageUrls.perfect = null;
    imageUrls.nobg = null;
    imageUrls.svg = null;
    showPreview(previewPseudoEl, data.image_url, "Pseudo pixel art", "pseudo");
    previewPerfectEl.innerHTML = `<div class="empty"><div class="icon">[]</div><div class="title">Waiting for conversion</div><div class="text">Convert to real pixel art to compare side-by-side.</div></div>`;
    // Hide nobg card and reset grid
    const nobgCard = document.getElementById("nobg-card");
    const previewNobgEl = document.getElementById("preview-nobg");
    if (nobgCard) nobgCard.style.display = "none";
    if (previewNobgEl) previewNobgEl.innerHTML = "";
    document.getElementById("preview-grid").classList.remove("has-nobg");
    updateGridCollapse();
    // Display structured prompt
    displayStructuredPrompt(data.structured_prompt);
    setStatus("Generated. Now convert to perfect pixels.");
  } catch (err) {
    hideLoading("pseudo");
    console.error(err);
    setStatus(`Generate failed: ${err.message}`, true);
  }
});

document.getElementById("btn-convert").addEventListener("click", async () => {
  if (!lastImageName) {
    setStatus("Generate first.", true);
    return;
  }
  setStatus("Converting to perfect pixel art...");
  showLoading("perfect", "Converting to perfect pixels");
  try {
    const data = await postJson("/api/convert", {
      image_name: lastImageName,
      auto_detect: true,
    });
    hideLoading("perfect");
    if (data.editable_url) {
      lastEditableName = data.editable_png;
      imageUrls.perfect = data.editable_url;
      imageUrls.svg = data.svg_url || null;
      showPreview(previewPerfectEl, data.editable_url, "Perfect pixel art", "perfect");
    } else if (data.raster_url) {
      imageUrls.perfect = data.raster_url;
      imageUrls.svg = data.svg_url || null;
      showPreview(previewPerfectEl, data.raster_url, "Perfect pixel art", "perfect");
    } else {
      setStatus("Conversion returned no preview.", true);
      return;
    }
    setStatus(
      `Converted. Block size ${data.detected_block_size || "?"} px. You can remove background next.`
    );
  } catch (err) {
    hideLoading("perfect");
    console.error(err);
    setStatus(`Conversion failed: ${err.message}`, true);
  }
});

document.getElementById("btn-remove").addEventListener("click", async () => {
  const target = lastEditableName || lastImageName;
  if (!target) {
    setStatus("Generate first.", true);
    return;
  }
  setStatus("Removing background...");
  
  // Show the nobg card first so we can show loading on it
  const nobgCard = document.querySelector(".nobg-card");
  if (nobgCard) {
    nobgCard.style.display = "";
    nobgCard.classList.remove("collapsed");
    previewGrid.classList.add("has-nobg");
    updateGridCollapse();
  }
  
  showLoading("nobg", "Removing background");
  try {
    const data = await postJson("/api/remove-bg", {
      image_name: target,
    });
    hideLoading("nobg");
    
    showPreview(previewNobgEl, data.image_url, "No background", "nobg");
    imageUrls.nobg = data.image_url;
    setStatus("Background removed.");
  } catch (err) {
    hideLoading("nobg");
    console.error(err);
    setStatus(`Remove background failed: ${err.message}`, true);
  }
});

function setPromptCollapsed(collapsed) {
  if (!promptPanelEl) return;
  promptPanelEl.classList.toggle("collapsed", collapsed);
  if (gridEl) {
    gridEl.classList.toggle("prompt-collapsed", collapsed);
  }
}

function updateGridCollapse() {
  const pseudoCollapsed = document.querySelector(".pseudo-card")?.classList.contains("collapsed");
  const perfectCollapsed = document.querySelector(".perfect-card")?.classList.contains("collapsed");
  const nobgCard = document.querySelector(".nobg-card");
  const nobgVisible = nobgCard && nobgCard.style.display !== "none";
  const nobgCollapsed = nobgCard?.classList.contains("collapsed");
  
  // Remove all collapse classes
  previewGrid.classList.remove(
    "pseudo-collapsed", "perfect-collapsed", "nobg-collapsed", 
    "both-collapsed"
  );
  
  // Add appropriate collapse classes
  if (pseudoCollapsed) previewGrid.classList.add("pseudo-collapsed");
  if (perfectCollapsed) previewGrid.classList.add("perfect-collapsed");
  if (nobgVisible && nobgCollapsed) previewGrid.classList.add("nobg-collapsed");
  
  // Legacy: both-collapsed for 2-column mode
  if (!nobgVisible && pseudoCollapsed && perfectCollapsed) {
    previewGrid.classList.add("both-collapsed");
  }
}

document.querySelectorAll(".collapse").forEach((btn) => {
  btn.addEventListener("click", () => {
    const collapseType = btn.dataset.collapse;
    if (collapseType === "prompt") {
      const next = !promptPanelEl?.classList.contains("collapsed");
      setPromptCollapsed(!!next);
      return;
    }

    const card = btn.closest(".preview-card");
    if (!card) return;

    if (card.classList.contains("collapsed")) {
      card.classList.remove("collapsed");
      if (collapseType === "pseudo") btn.textContent = "Pseudo pixel art";
      else if (collapseType === "perfect") btn.textContent = "Perfect pixel art";
      else if (collapseType === "nobg") btn.textContent = "No background";
    } else {
      card.classList.add("collapsed");
      if (collapseType === "pseudo") btn.textContent = "Pseudo pixel art";
      else if (collapseType === "perfect") btn.textContent = "Perfect pixel art";
      else if (collapseType === "nobg") btn.textContent = "No background";
    }
    updateGridCollapse();
  });
});

// Click on collapsed label to expand
document.querySelectorAll(".collapsed-label").forEach((label) => {
  label.addEventListener("click", () => {
    const promptPanel = label.closest(".prompt-panel");
    if (promptPanel) {
      setPromptCollapsed(false);
      return;
    }

    const card = label.closest(".preview-card");
    if (card.classList.contains("collapsed")) {
      card.classList.remove("collapsed");
      const btn = card.querySelector(".collapse");
      if (btn) {
        const collapseType = btn.dataset.collapse;
        if (collapseType === "pseudo") btn.textContent = "Pseudo pixel art";
        else if (collapseType === "perfect") btn.textContent = "Perfect pixel art";
        else if (collapseType === "nobg") btn.textContent = "No background";
      }
      updateGridCollapse();
    }
  });
});

// Zoom slider controls - use 'change' and 'input' for better compatibility
document.querySelectorAll(".zoom-slider").forEach((slider) => {
  const handleSliderChange = () => {
    const target = slider.dataset.zoomTarget;
    if (!target) return;
    const state = previewState[target];
    if (!state) return;
    state.scale = parseFloat(slider.value);
    applyScale(target);
  };
  slider.addEventListener("input", handleSliderChange);
  slider.addEventListener("change", handleSliderChange);
});

// ========================================
// Save/Download Functions
// ========================================

async function downloadImage(url, filename) {
  if (!url) return false;
  try {
    const response = await fetch(url);
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
    return true;
  } catch (err) {
    console.error('Download failed:', err);
    return false;
  }
}

function getFilename(type) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const prompt = promptEl.value.trim().slice(0, 30).replace(/[^a-zA-Z0-9]/g, '_') || 'image';
  return `${prompt}_${type}_${timestamp}.png`;
}

// Save individual images
document.getElementById('save-pseudo')?.addEventListener('click', async () => {
  if (!imageUrls.pseudo) {
    setStatus('No pseudo image to save.', true);
    return;
  }
  setStatus('Saving pseudo image...');
  const success = await downloadImage(imageUrls.pseudo, getFilename('pseudo'));
  setStatus(success ? 'Pseudo image saved.' : 'Failed to save image.', !success);
});

document.getElementById('save-perfect')?.addEventListener('click', async () => {
  if (!imageUrls.perfect) {
    setStatus('No perfect image to save.', true);
    return;
  }
  setStatus('Saving perfect image...');
  const success = await downloadImage(imageUrls.perfect, getFilename('perfect'));
  setStatus(success ? 'Perfect image saved.' : 'Failed to save image.', !success);
});

document.getElementById('save-nobg')?.addEventListener('click', async () => {
  if (!imageUrls.nobg) {
    setStatus('No background-removed image to save.', true);
    return;
  }
  setStatus('Saving no-background image...');
  const success = await downloadImage(imageUrls.nobg, getFilename('nobg'));
  setStatus(success ? 'No-background image saved.' : 'Failed to save image.', !success);
});

// Save all images and JSON as a ZIP file
document.getElementById('save-all')?.addEventListener('click', async () => {
  const available = [];
  if (imageUrls.pseudo) available.push({ url: imageUrls.pseudo, type: 'pseudo', ext: 'png' });
  if (imageUrls.perfect) available.push({ url: imageUrls.perfect, type: 'perfect', ext: 'png' });
  if (imageUrls.nobg) available.push({ url: imageUrls.nobg, type: 'nobg', ext: 'png' });
  if (imageUrls.svg) available.push({ url: imageUrls.svg, type: 'vector', ext: 'svg' });
  
  const hasJson = currentStructuredPrompt !== null;
  
  if (available.length === 0 && !hasJson) {
    setStatus('No images or data to save.', true);
    return;
  }
  
  const totalItems = available.length + (hasJson ? 1 : 0);
  setStatus(`Preparing ZIP with ${totalItems} file(s)...`);
  
  try {
    const zip = new JSZip();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const promptSlug = promptEl.value.trim().slice(0, 30).replace(/[^a-zA-Z0-9]/g, '_') || 'pixelart';
    const folderName = `${promptSlug}_${timestamp}`;
    const folder = zip.folder(folderName);
    
    // Add images to ZIP
    for (const img of available) {
      try {
        setStatus(`Adding ${img.type} ${img.ext}...`);
        const response = await fetch(img.url);
        const blob = await response.blob();
        folder.file(`${img.type}.${img.ext}`, blob);
      } catch (err) {
        console.error(`Failed to add ${img.type}:`, err);
      }
    }
    
    // Add JSON file with structured prompt
    if (hasJson) {
      const jsonData = {
        prompt: promptEl.value.trim(),
        style: currentStyle,
        structured_prompt: currentStructuredPrompt,
        images: {
          pseudo: imageUrls.pseudo ? true : false,
          perfect: imageUrls.perfect ? true : false,
          nobg: imageUrls.nobg ? true : false
        },
        timestamp: new Date().toISOString()
      };
      folder.file('data.json', JSON.stringify(jsonData, null, 2));
    }
    
    setStatus('Creating ZIP file...');
    const zipBlob = await zip.generateAsync({ type: 'blob' });
    
    // Download the ZIP
    const zipUrl = URL.createObjectURL(zipBlob);
    const a = document.createElement('a');
    a.href = zipUrl;
    a.download = `${folderName}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(zipUrl);
    
    setStatus(`Saved ${totalItems} file(s) as ZIP.`);
  } catch (err) {
    console.error('ZIP creation failed:', err);
    setStatus('Failed to create ZIP file.', true);
  }
});
