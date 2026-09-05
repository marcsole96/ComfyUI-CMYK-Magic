import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

let DATA_CACHE = null;
async function fetchData() {
    if (!DATA_CACHE) {
        try {
            const res = await api.fetchApi("/cmyk_magic/presets");
            DATA_CACHE = await res.json();
        } catch (e) {
            console.warn("CMYK Magic: metadata fetch failed", e);
            DATA_CACHE = { presets: {}, palettes: {}, help: {}, preset_desc: {} };
        }
    }
    return DATA_CACHE;
}

// ---------------------------------------------------------------- pattern art

const PATTERN_IDS = [
    "print_dots", "negative_dots", "elliptical", "square_dots", "bayer",
    "lines", "broken_lines", "cross_lines",
    "waves", "broken_waves", "cross_waves",
    "fan_dots", "negative_fan", "concentric", "spiral", "mezzotint", "solid",
];
const PATTERN_LABELS = {
    print_dots: "Dots", negative_dots: "Neg Dots", elliptical: "Chain",
    square_dots: "Square", bayer: "Dither", lines: "Lines",
    broken_lines: "Broken Ln", cross_lines: "Cross Ln", waves: "Waves",
    broken_waves: "Broken Wv", cross_waves: "Cross Wv", fan_dots: "Fan Dots",
    negative_fan: "Neg Fan", concentric: "Rings", spiral: "Spiral",
    mezzotint: "Mezzo", solid: "Solid", random: "Random",
};
const GRID_IDS = [...PATTERN_IDS, "random"];

const PAPER = "#ddd5c2", INK = "#292430";

function drawStripes(ctx, w, h, angle, dash, wavy) {
    ctx.save();
    ctx.translate(w / 2, h / 2);
    ctx.rotate((angle * Math.PI) / 180);
    ctx.strokeStyle = INK;
    ctx.lineWidth = 2.4;
    if (dash) ctx.setLineDash([5, 3]);
    const R = Math.max(w, h);
    for (let y = -R; y <= R; y += 6) {
        ctx.beginPath();
        if (wavy) {
            for (let x = -R; x <= R; x += 2) {
                const yy = y + Math.sin(x * 0.45) * 2.2;
                x === -R ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy);
            }
        } else {
            ctx.moveTo(-R, y);
            ctx.lineTo(R, y);
        }
        ctx.stroke();
    }
    ctx.restore();
}

function drawDots(ctx, w, h, invert) {
    ctx.fillStyle = invert ? INK : PAPER;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = invert ? PAPER : INK;
    ctx.save();
    ctx.translate(w / 2, h / 2);
    ctx.rotate(0.26);
    for (let y = -h; y <= h; y += 7) {
        for (let x = -w; x <= w; x += 7) {
            ctx.beginPath();
            ctx.arc(x, y, 2.1, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    ctx.restore();
}

function drawFan(ctx, w, h, invert) {
    ctx.fillStyle = invert ? INK : PAPER;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = invert ? PAPER : INK;
    const cx = w / 2, cy = h * 1.9;
    for (let r = 8; r < h * 2.2; r += 6.5) {
        const step = 6.5 / r;
        for (let t = -Math.PI; t < 0; t += step) {
            const x = cx + r * Math.cos(t), y = cy + r * Math.sin(t);
            if (x < -3 || x > w + 3 || y < -3 || y > h + 3) continue;
            ctx.beginPath();
            ctx.arc(x, y, 1.9, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

/** Lattice of shapes on a rotated grid — dots, ellipses or squares. */
function drawLattice(ctx, w, h, shape) {
    ctx.fillStyle = PAPER;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = INK;
    ctx.save();
    ctx.translate(w / 2, h / 2);
    ctx.rotate(0.26);
    for (let y = -h; y <= h; y += 7) {
        for (let x = -w; x <= w; x += 7) {
            ctx.beginPath();
            if (shape === "ellipse") ctx.ellipse(x, y, 3.1, 1.6, 0, 0, Math.PI * 2);
            else if (shape === "square") ctx.rect(x - 2, y - 2, 4, 4);
            else ctx.arc(x, y, 2.1, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    ctx.restore();
}

function drawRings(ctx, w, h, spiral) {
    ctx.fillStyle = PAPER;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = INK;
    ctx.lineWidth = 1.6;
    const cx = w / 2, cy = h / 2, max = Math.hypot(w, h) / 2;
    if (spiral) {
        ctx.beginPath();
        for (let a = 0; a < Math.PI * 14; a += 0.12) {
            const r = (a / (Math.PI * 2)) * 4.5;
            const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
            a === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
    } else {
        for (let r = 3; r < max; r += 4.5) {
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
}

function drawMezzo(ctx, w, h) {
    ctx.fillStyle = PAPER;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = INK;
    let seed = 7;
    const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
    for (let i = 0; i < 260; i++) {
        ctx.beginPath();
        ctx.arc(rnd() * w, rnd() * h, 0.6 + rnd() * 1.5, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawDither(ctx, w, h) {
    ctx.fillStyle = PAPER;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = INK;
    const B = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
    const c = 3.4;
    for (let y = 0; y < h / c; y++) {
        for (let x = 0; x < w / c; x++) {
            // density ramps left to right so the dither reads as a gradient
            if (B[y % 4][x % 4] < 15 * (1 - (x * c) / w) + 0.5) {
                ctx.fillRect(x * c, y * c, c - 0.7, c - 0.7);
            }
        }
    }
}

function drawPreview(cv, id) {
    const ctx = cv.getContext("2d");
    const w = cv.width, h = cv.height;
    ctx.fillStyle = PAPER;
    ctx.fillRect(0, 0, w, h);
    switch (id) {
        case "print_dots": drawDots(ctx, w, h, false); break;
        case "negative_dots": drawDots(ctx, w, h, true); break;
        case "elliptical": drawLattice(ctx, w, h, "ellipse"); break;
        case "square_dots": drawLattice(ctx, w, h, "square"); break;
        case "bayer": drawDither(ctx, w, h); break;
        case "concentric": drawRings(ctx, w, h, false); break;
        case "spiral": drawRings(ctx, w, h, true); break;
        case "mezzotint": drawMezzo(ctx, w, h); break;
        case "lines": drawStripes(ctx, w, h, -30, false, false); break;
        case "broken_lines": drawStripes(ctx, w, h, -30, true, false); break;
        case "cross_lines":
            drawStripes(ctx, w, h, -35, false, false);
            drawStripes(ctx, w, h, 35, false, false);
            break;
        case "waves": drawStripes(ctx, w, h, -15, false, true); break;
        case "broken_waves": drawStripes(ctx, w, h, -15, true, true); break;
        case "cross_waves":
            drawStripes(ctx, w, h, -25, false, true);
            drawStripes(ctx, w, h, 55, false, true);
            break;
        case "fan_dots": drawFan(ctx, w, h, false); break;
        case "negative_fan": drawFan(ctx, w, h, true); break;
        case "solid":
            ctx.fillStyle = INK;
            ctx.fillRect(5, 5, w - 10, h - 10);
            break;
        case "random": {
            ctx.fillStyle = INK;
            const s = Math.min(w, h) - 10;
            const x0 = (w - s) / 2, y0 = (h - s) / 2;
            ctx.beginPath();
            ctx.roundRect(x0, y0, s, s, 5);
            ctx.fill();
            ctx.fillStyle = PAPER;
            for (const [px, py] of [[0.25, 0.25], [0.75, 0.25], [0.5, 0.5],
                                    [0.25, 0.75], [0.75, 0.75]]) {
                ctx.beginPath();
                ctx.arc(x0 + px * s, y0 + py * s, 2.2, 0, Math.PI * 2);
                ctx.fill();
            }
            break;
        }
    }
}

/** Overlapping C/M/Y discs — the rosette a four-colour press makes. */
function drawRosette(cv) {
    const ctx = cv.getContext("2d");
    const w = cv.width, h = cv.height, r = Math.min(w, h) * 0.30;
    ctx.clearRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";
    ctx.globalAlpha = 0.55;          // an identity mark, not decoration
    const discs = [["#2a6f8c", -0.55, 0.32], ["#8c2a5c", 0.55, 0.32], ["#8c7a2a", 0, -0.62]];
    for (const [col, dx, dy] of discs) {
        ctx.fillStyle = col;
        ctx.beginPath();
        ctx.arc(w / 2 + dx * r, h / 2 + dy * r, r, 0, Math.PI * 2);
        ctx.fill();
    }
}

// ------------------------------------------------------------------- helpers

function el(tag, style = {}, props = {}) {
    const e = document.createElement(tag);
    Object.assign(e.style, style);
    Object.assign(e, props);
    return e;
}

function hideWidget(w) {
    if (!w) return;
    // Canvas (LiteGraph) renderer: zero-height widget with a "hidden" type.
    w.computeSize = () => [0, -4];
    w.type = "hidden";
    w.hidden = true;
    // Vue nodes renderer: it never looks at w.type or w.hidden. It merges the
    // widget's `options` and asks isWidgetVisible(options), so the flag has to
    // live on options or the widget renders anyway.
    w.options = w.options || {};
    w.options.hidden = true;
}

function hexLum(hex) {
    const s = hex.replace("#", "");
    const r = parseInt(s.slice(0, 2), 16), g = parseInt(s.slice(2, 4), 16),
          b = parseInt(s.slice(4, 6), 16);
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

const DEFAULT_STATE = {
    mode: "color_match",
    background: "#f4efe6",
    opaque_bottom: false,
    inks: [
        { color: "#e8c547", on: true },
        { color: "#d1495b", on: true },
        { color: "#30638e", on: true },
        { color: "#1b1b25", on: true },
    ],
};

/** Mean hue of a palette's inks, so the list can be ordered by colour. */
function paletteHue(p) {
    let x = 0, y = 0;
    for (const hex of p.inks || []) {
        const t = hex.replace("#", "");
        const r = parseInt(t.slice(0, 2), 16) / 255,
              g = parseInt(t.slice(2, 4), 16) / 255,
              b = parseInt(t.slice(4, 6), 16) / 255;
        const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
        if (d < 0.05) continue;                       // greys carry no hue
        let h = 0;
        if (mx === r) h = ((g - b) / d + 6) % 6;
        else if (mx === g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h *= Math.PI / 3;
        x += Math.cos(h); y += Math.sin(h);
    }
    if (!x && !y) return 99;                          // all-grey palettes last
    const a = Math.atan2(y, x);
    return a < 0 ? a + Math.PI * 2 : a;
}

function parseState(text) {
    try {
        const s = JSON.parse(text);
        if (s && Array.isArray(s.inks)) return s;
    } catch (e) { /* fall through */ }
    return JSON.parse(JSON.stringify(DEFAULT_STATE));
}

// ------------------------------------------------------------------ theming

// Take the host's own widget colours where it exposes them, so the panel
// matches whatever theme the user runs instead of inventing a scheme.
const LG = globalThis.LiteGraph || {};
const PANEL_BG = "#303030";
const WELL_BG = LG.WIDGET_BGCOLOR || "#222";      // preview / help wells
const ROW_BG = "#2b2b2b";                         // ink rows
const ROW_BG2 = "#262626";                        // per-ink advanced strip
const BTN_BG = LG.WIDGET_BGCOLOR || "#222";
const BORDER = "#4e4e4e";
const BORDER_DIM = "#3f3f3f";
const BTN_BORDER = "#555";
const TEXT = LG.WIDGET_TEXT_COLOR || "#DDD";
const TEXT_DIM = LG.WIDGET_SECONDARY_TEXT_COLOR || "#999";
const TEXT_DIM2 = "#888";
const ACCENT = "#909090";        // carets, slider tracks, selected outlines
const ACTIVE_BG = "#4a4a4a";     // active button fill
const ACTIVE_FG = "#FFF";
const SEL_BG = "#3a3a3a";        // selected thumbnail backdrop

const S = {
    panel: { background: PANEL_BG, border: "1px solid #35314a", borderRadius: "8px",
             padding: "8px", fontFamily: "sans-serif", fontSize: "11px",
             color: TEXT, display: "flex", gap: "8px", alignItems: "stretch",
             boxSizing: "border-box", height: "100%" },
    btn: { background: BTN_BG, border: "1px solid #45405e", borderRadius: "5px",
           color: TEXT, padding: "3px 8px", cursor: "pointer", fontSize: "11px" },
    row: { display: "flex", alignItems: "center", gap: "6px" },
};

function buildPanel(node) {
    const cfgW = node.widgets.find((w) => w.name === "ink_config");
    const patW = node.widgets.find((w) => w.name === "pattern");
    const presetW = node.widgets.find((w) => w.name === "preset");
    if (!cfgW || !patW) return;
    hideWidget(cfgW);
    hideWidget(patW);
    hideWidget(presetW);

    let META = { presets: {}, palettes: {}, help: {}, preset_desc: {} };
    let state = parseState(cfgW.value);
    const syncers = [];
    let markPreset = () => {};

    // Picking a preset loads its values into the widgets and STAYS selected;
    // any manual tweak afterwards flips it back to "Custom" so the headless
    // preset-override path never fights user edits.
    const markCustom = () => {
        if (presetW && presetW.value !== "Custom") {
            presetW.value = "Custom";
            markPreset();
        }
    };
    if (presetW) {
        const origPresetCb = presetW.callback;
        presetW.callback = function (value, ...rest) {
            origPresetCb?.call(this, value, ...rest);
            if (!value || value === "Custom") return;
            fetchData().then((data) => {
                const p = (data.presets || {})[value];
                if (!p) return;
                for (const key of ["scale", "roughness", "brightness", "contrast",
                                   "ink_multiply", "ink_fade", "dot_gain",
                                   "plate_drift", "offset_angles", "rotate",
                                   "plate_render", "tint_quantize"]) {
                    const w = node.widgets.find((x) => x.name === key);
                    if (w && p[key] !== undefined) w.value = p[key];
                }
                patW.value = p.pattern;
                cfgW.value = JSON.stringify(p.ink_config);
                node._cmykRefresh?.();
                markPreset();
                app.graph?.setDirtyCanvas(true, true);
            });
        };
    }

    const root = el("div", S.panel);

    // =====================================================  LEFT: preview
    const left = el("div", { width: "204px", flexShrink: "0", display: "flex",
                             flexDirection: "column", gap: "6px" });

    const titleRow = el("div", { ...S.row, gap: "5px" });
    const rosette = el("canvas", { width: "18px", height: "18px" });
    rosette.width = 18; rosette.height = 18;
    drawRosette(rosette);
    titleRow.appendChild(rosette);
    titleRow.appendChild(el("span", { fontSize: "11px", fontWeight: "600",
                                      letterSpacing: "0.04em", color: TEXT },
                            { textContent: "CMYK MAGIC" }));
    left.appendChild(titleRow);

    const previewWrap = el("div", { position: "relative", borderRadius: "6px",
                                    overflow: "hidden", background: WELL_BG,
                                    border: "1px solid #35314a", minHeight: "150px" });
    const previewImg = el("img", { width: "100%", display: "block" });
    const previewNote = el("div", { position: "absolute", left: "5px", bottom: "4px",
                                    fontSize: "9px", color: TEXT,
                                    background: "rgba(0,0,0,0.7)", padding: "1px 5px",
                                    borderRadius: "3px", pointerEvents: "none" },
                           { textContent: "preview" });
    const previewBusy = el("div", { position: "absolute", right: "5px", top: "4px",
                                    fontSize: "9px", color: "#111",
                                    background: "#bbb", padding: "1px 5px",
                                    borderRadius: "3px", opacity: "0",
                                    transition: "opacity .12s", pointerEvents: "none" },
                           { textContent: "rendering" });
    previewWrap.appendChild(previewImg);
    previewWrap.appendChild(previewNote);
    previewWrap.appendChild(previewBusy);
    left.appendChild(previewWrap);

    // help strip: replaces the tooltips that native widgets used to provide
    const helpBox = el("div", { flex: "1", minHeight: "86px", background: WELL_BG,
                                border: "1px solid #2f2b42", borderRadius: "6px",
                                padding: "6px 7px", fontSize: "10px", lineHeight: "1.45",
                                color: TEXT_DIM, overflow: "hidden" });
    const helpTitle = el("div", { color: TEXT_DIM, fontSize: "9px",
                                  letterSpacing: "0.08em", textTransform: "uppercase",
                                  marginBottom: "3px" }, { textContent: "help" });
    const helpBody = el("div", {}, { textContent: "Hover any control for what it does." });
    helpBox.appendChild(helpTitle);
    helpBox.appendChild(helpBody);
    left.appendChild(helpBox);
    root.appendChild(left);

    const setHelp = (label, key) => {
        const text = META.help?.[key];
        helpTitle.textContent = label;
        helpBody.textContent = text || "—";
    };
    const clearHelp = () => {
        helpTitle.textContent = "help";
        helpBody.textContent = META.help?.default || "Hover any control for what it does.";
    };
    /** Wire an element to the help strip (and keep a native title as backup). */
    const helpOn = (elem, label, key) => {
        elem.addEventListener("mouseenter", () => setHelp(label, key));
        elem.addEventListener("mouseleave", clearHelp);
        return elem;
    };
    helpOn(previewWrap, "preview", "preview");

    // ==================================================  RIGHT: controls
    const right = el("div", { flex: "1", minWidth: "0", display: "flex",
                              flexDirection: "column", gap: "7px",
                              overflowY: "auto", overflowX: "hidden",
                              paddingRight: "2px" });
    root.appendChild(right);

    node.properties = node.properties || {};
    const uiState = node.properties.cmykUI = node.properties.cmykUI || { open: {} };

    // A wheel over a DOM widget otherwise reaches the canvas and zooms the
    // graph, which makes an internal scroll area unusable.
    right.addEventListener("wheel", (e) => e.stopPropagation(), { passive: true });

    // Collapsing sections should actually shrink the node, so the panel is
    // only as tall as what you have open — capped, then it scrolls.
    let fitTimer = null;
    // Measure the children, not the scroll box: scrollHeight can never report
    // less than the container we are sizing, so reading it would pin the node
    // at its maximum for ever.
    const contentHeight = () => {
        let h = 0, n = 0;
        for (const c of right.children) {
            const box = c.offsetHeight;
            if (!box) continue;
            h += box;
            n += 1;
        }
        return h + Math.max(0, n - 1) * 7;
    };
    const LEFT_MIN = 264;      // title + preview + help strip
    const MIN_W = 760;
    const MIN_H = 1200;        // the panel is tall; start with room for it
    if (!uiState.width) uiState.width = 820;
    // Remember a manual resize on both axes, so re-fitting never claws back a
    // size you chose. `selfResize` keeps our own setSize from being mistaken
    // for one of yours, which would otherwise latch the node at that size.
    let selfResize = false;
    const origResize = node.onResize;
    node.onResize = function (size) {
        origResize?.apply(this, arguments);
        if (selfResize || !size) return;
        if (size[0]) uiState.width = Math.max(MIN_W, size[0]);
        if (size[1]) uiState.height = size[1];
    };
    const fitHeight = () => {
        clearTimeout(fitTimer);
        fitTimer = setTimeout(() => {
            // CHROME is everything ComfyUI draws around our widget: title bar,
            // the image/plates slots and the two native seed rows. Undercount
            // it and the panel clips, which is the one failure that matters.
            const CHROME = 170;
            const needed = Math.max(contentHeight(), LEFT_MIN) + CHROME;
            // MIN_H is the starting height, not a hard floor: once you have
            // resized the node by hand, your height wins and we only ever grow
            // past it to stop content clipping.
            const floor = uiState.height || MIN_H;
            const wanted = Math.min(1600, Math.max(needed, floor));
            const w = Math.max(MIN_W, uiState.width || node.size[0]);
            if (Math.abs(node.size[1] - wanted) > 3 || Math.abs(node.size[0] - w) > 4) {
                selfResize = true;
                node.setSize([w, wanted]);
                selfResize = false;
                app.graph?.setDirtyCanvas(true, true);
            }
        }, 40);
    };

    /** Collapsible section; open/closed persists with the workflow. */
    const mkSection = (parent, title, defaultOpen = true) => {
        if (uiState.open[title] === undefined) uiState.open[title] = defaultOpen;
        const head = el("div", { ...S.row, gap: "5px", cursor: "pointer",
                                 borderBottom: "1px solid #2f2b42", paddingBottom: "3px",
                                 marginTop: "3px" });
        const caret = el("span", { color: TEXT_DIM2, fontSize: "8px", width: "8px" });
        const label = el("span", { color: TEXT_DIM, fontSize: "10px",
                                   letterSpacing: "0.09em",
                                   textTransform: "uppercase", flex: "1" },
                         { textContent: title });
        head.appendChild(caret);
        head.appendChild(label);
        const body = el("div", { display: "flex", flexDirection: "column", gap: "5px",
                                 paddingTop: "2px" });
        const paint = () => {
            const open = uiState.open[title];
            caret.textContent = open ? "▼" : "▶";
            body.style.display = open ? "flex" : "none";
        };
        head.onclick = () => {
            uiState.open[title] = !uiState.open[title];
            paint();
            fitHeight();
        };
        paint();
        parent.appendChild(head);
        parent.appendChild(body);
        return body;
    };

    // ---- preview request loop (one in flight, coalescing) ----------------
    let inFlight = false, dirty = false, timer = null, lastUrl = null;
    const sendPreview = async () => {
        inFlight = true;
        previewBusy.style.opacity = "1";
        const body = { node_id: String(node.id) };
        for (const w of node.widgets || []) {
            if (w.name && w.name !== "cmyk_ui") body[w.name] = w.value;
        }
        body.preset = "Custom";        // widgets already hold the resolved values
        try {
            const res = await api.fetchApi("/cmyk_magic/preview", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            if (res.ok) {
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                previewImg.src = url;
                if (lastUrl) URL.revokeObjectURL(lastUrl);
                lastUrl = url;
                const from = res.headers.get("X-Preview-Source") === "input"
                    ? "your image" : "test card";
                const drawn = res.headers.get("X-Preset");
                const shuffling = (state.randomize?.presets || []).length > 0;
                previewNote.textContent = (shuffling && drawn && drawn !== "Custom")
                    ? `${from} \u00b7 ${drawn}` : from;
            } else {
                previewNote.textContent = "preview unavailable";
            }
        } catch (e) {
            previewNote.textContent = "preview unavailable";
        } finally {
            inFlight = false;
            previewBusy.style.opacity = "0";
            if (dirty) { dirty = false; sendPreview(); }
        }
    };
    const schedulePreview = () => {
        if (inFlight) { dirty = true; return; }
        clearTimeout(timer);
        timer = setTimeout(sendPreview, 140);
    };
    node._cmykPreview = schedulePreview;

    const sync = () => {
        cfgW.value = JSON.stringify(state);
        markCustom();
        schedulePreview();
        app.graph?.setDirtyCanvas(true, false);
    };

    // Presets and patterns run the full width; the ink list and the two
    // slider groups then sit side by side, which is what stops the panel
    // becoming one long strip.
    const lower = el("div", { display: "flex", gap: "12px", alignItems: "flex-start" });
    const lowerL = el("div", { flex: "1", minWidth: "0", display: "flex",
                               flexDirection: "column" });
    const lowerR = el("div", { flex: "1", minWidth: "0", display: "flex",
                               flexDirection: "column" });
    lower.appendChild(lowerL);
    lower.appendChild(lowerR);

    const presetBody = mkSection(right, "Presets", true);
    const patternBody = mkSection(right, "Pattern", true);
    right.appendChild(lower);
    const inkBody = mkSection(lowerL, "Colour & inks", true);
    const screenBody = mkSection(lowerR, "Screen", true);
    const inkPressBody = mkSection(lowerR, "Ink & press", true);

    // ============================================== section: preset gallery
    // Shortlist: tick several presets and one is drawn per run. The list
    // lives in ink_config, so it saves with the workflow and reaches the
    // preview through the same payload as everything else.
    const shortlist = () => (state.randomize && state.randomize.presets) || [];
    const setShortlist = (arr) => {
        state.randomize = state.randomize || {};
        state.randomize.presets = arr;
        if (!arr.length) delete state.randomize.presets;
    };
    const shufRow = el("div", { ...S.row, gap: "5px", marginBottom: "2px" });
    const shufBtn = el("button", { ...S.btn, padding: "2px 7px", fontSize: "9px" },
                       { textContent: "\u{1F3B2} Shuffle" });
    const shufCount = el("span", { flex: "1", fontSize: "9px", color: TEXT_DIM2 });
    const allBtn = el("button", { ...S.btn, padding: "2px 6px", fontSize: "9px" },
                      { textContent: "All" });
    const noneBtn = el("button", { ...S.btn, padding: "2px 6px", fontSize: "9px" },
                       { textContent: "None" });
    shufRow.appendChild(shufBtn);
    shufRow.appendChild(shufCount);
    shufRow.appendChild(allBtn);
    shufRow.appendChild(noneBtn);
    presetBody.appendChild(shufRow);
    helpOn(shufBtn, "shuffle presets", "shuffle");
    helpOn(allBtn, "select all", "shuffle_all");
    helpOn(noneBtn, "select none", "shuffle_none");

    // Two rows scrolling sideways: browsing presets must not push the rest
    // of the panel down the canvas.
    const presetGrid = el("div", { display: "grid", gridTemplateRows: "repeat(2, auto)",
                                   gridAutoFlow: "column", gridAutoColumns: "102px",
                                   gap: "4px", overflowX: "auto", overflowY: "hidden",
                                   paddingBottom: "4px" });
    presetGrid.addEventListener("wheel", (e) => {
        if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
            presetGrid.scrollLeft += e.deltaY;
            e.preventDefault();
        }
    }, { passive: false });
    presetBody.appendChild(presetGrid);
    const presetCells = {}, presetBadges = {};
    markPreset = () => {
        const picked = shortlist();
        const selecting = !!uiState.shuffle;
        shufBtn.style.background = selecting ? ACTIVE_BG : BTN_BG;
        shufBtn.style.borderColor = selecting ? ACCENT : BTN_BORDER;
        shufBtn.style.color = selecting ? ACTIVE_FG : TEXT_DIM;
        shufCount.textContent = picked.length
            ? `${picked.length} in shuffle \u2014 one drawn each run`
            : (selecting ? "click presets to add them" : "click a preset to apply it");
        for (const name of Object.keys(presetCells)) {
            const active = presetW && presetW.value === name;
            const inList = picked.indexOf(name) >= 0;
            presetCells[name].style.borderColor =
                inList ? ACCENT : (active ? ACCENT : "transparent");
            presetCells[name].style.background =
                (inList || active) ? SEL_BG : "transparent";
            presetBadges[name].style.display = inList ? "block" : "none";
        }
    };
    shufBtn.onclick = () => { uiState.shuffle = !uiState.shuffle; markPreset(); };
    allBtn.onclick = () => {
        setShortlist(Object.keys(META.presets || {}));
        markPreset(); sync();
    };
    noneBtn.onclick = () => { setShortlist([]); markPreset(); sync(); };
    const buildPresetGallery = () => {
        presetGrid.innerHTML = "";
        for (const name of Object.keys(META.presets || {})) {
            const cell = el("div", { cursor: "pointer", borderRadius: "4px", padding: "2px",
                                     border: "2px solid transparent", textAlign: "center",
                                     position: "relative" });
            const badge = el("div", { position: "absolute", top: "3px", left: "3px",
                                      fontSize: "9px", lineHeight: "11px",
                                      background: ACTIVE_BG, color: ACTIVE_FG,
                                      borderRadius: "3px", padding: "0 3px",
                                      display: "none", pointerEvents: "none" },
                             { textContent: "\u2713" });
            cell.appendChild(badge);
            presetBadges[name] = badge;
            const img = el("img", { width: "100%", display: "block", borderRadius: "3px",
                                    background: WELL_BG, minHeight: "26px" },
                           { loading: "lazy",
                             src: api.apiURL("/cmyk_magic/preset_thumb?name=" +
                                             encodeURIComponent(name)) });
            const cap = el("div", { fontSize: "8px", marginTop: "1px", color: TEXT_DIM2,
                                    whiteSpace: "nowrap", overflow: "hidden",
                                    textOverflow: "ellipsis" }, { textContent: name });
            img.addEventListener("load", () => fitHeight(), { once: true });
            cell.appendChild(img);
            cell.appendChild(cap);
            cell.title = (META.preset_desc || {})[name] || name;
            cell.addEventListener("mouseenter", () => {
                helpTitle.textContent = name;
                helpBody.textContent = uiState.shuffle
                    ? (META.help?.shuffle_pick || "")
                    : ((META.preset_desc || {})[name] || "");
            });
            cell.addEventListener("mouseleave", clearHelp);
            cell.onclick = () => {
                if (uiState.shuffle) {          // selecting, not applying
                    const list = shortlist().slice();
                    const at = list.indexOf(name);
                    if (at >= 0) list.splice(at, 1); else list.push(name);
                    setShortlist(list);
                    markPreset();
                    sync();
                    return;
                }
                if (!presetW) return;
                presetW.value = name;
                presetW.callback?.call(presetW, name);
                markPreset();
            };
            presetCells[name] = cell;
            presetGrid.appendChild(cell);
        }
        markPreset();
    };

    // ===================================================== section: pattern
    const grid = el("div", { display: "grid", gridTemplateColumns: "repeat(6, 1fr)",
                             gap: "3px" });
    const cells = {};
    for (const id of GRID_IDS) {
        const cell = el("div", { cursor: "pointer", textAlign: "center", borderRadius: "3px",
                                 padding: "1px", border: "2px solid transparent" });
        const cv = el("canvas", { width: "100%", maxWidth: "54px", margin: "0 auto",
                                  borderRadius: "2px", display: "block" });
        cv.width = 44; cv.height = 24;
        drawPreview(cv, id);
        cell.appendChild(cv);
        cell.appendChild(el("div", { fontSize: "7px", color: TEXT_DIM2,
                                     whiteSpace: "nowrap", overflow: "hidden",
                                     textOverflow: "ellipsis" },
                            { textContent: PATTERN_LABELS[id] }));
        cell.onclick = () => { patW.value = id; markPattern(); sync(); };
        helpOn(cell, PATTERN_LABELS[id], "pat:" + id);
        cells[id] = cell;
        grid.appendChild(cell);
    }
    const markPattern = () => {
        for (const id of GRID_IDS) {
            const on = id === patW.value;
            cells[id].style.border = on ? `2px solid ${ACCENT}` : "2px solid transparent";
            cells[id].style.background = on ? SEL_BG : "transparent";
        }
    };
    patternBody.appendChild(grid);

    // ============================================ sliders & segment helpers
    const bindSlider = (parent, hue, name, label) => {
        const w = node.widgets.find((x) => x.name === name);
        if (!w) return;
        hideWidget(w);
        const o = w.options || {};
        const min = o.min ?? 0, max = o.max ?? 100, step = o.step ?? 1;

        const row = el("div", { ...S.row, gap: "5px" });
        const lab = el("span", { width: "62px", color: TEXT_DIM, fontSize: "10px",
                                 flexShrink: "0", cursor: "help" },
                       { textContent: label });
        const range = el("input", { flex: "1", minWidth: "0", accentColor: hue,
                                    cursor: "pointer" },
                         { type: "range", min: String(min), max: String(max),
                           step: String(step), value: String(w.value) });
        const num = el("span", { width: "28px", textAlign: "right", fontSize: "10px",
                                 color: TEXT, flexShrink: "0" },
                       { textContent: String(Math.round(w.value)) });
        const dice = el("button", { ...S.btn, padding: "0px 4px", fontSize: "9px",
                                    lineHeight: "15px" },
                        { textContent: "\u{1F3B2}" });
        row.appendChild(lab); row.appendChild(range);
        row.appendChild(num); row.appendChild(dice);

        // second line, only while this setting is diced
        const rndRow = el("div", { ...S.row, gap: "4px", paddingLeft: "62px",
                                   fontSize: "9px", color: TEXT_DIM2 });
        const lo = el("input", { width: "42px", background: BTN_BG, color: TEXT,
                                 border: "1px solid #45405e", borderRadius: "4px",
                                 fontSize: "9px" },
                      { type: "number", step: String(step) });
        const hi = el("input", { width: "42px", background: BTN_BG, color: TEXT,
                                 border: "1px solid #45405e", borderRadius: "4px",
                                 fontSize: "9px" },
                      { type: "number", step: String(step) });
        rndRow.appendChild(el("span", {}, { textContent: "random" }));
        rndRow.appendChild(lo);
        rndRow.appendChild(el("span", {}, { textContent: "to" }));
        rndRow.appendChild(hi);

        const spec = () => (state.randomize?.sliders || {})[name];
        const paint = () => {
            const sp = spec();
            const on = Array.isArray(sp);
            dice.style.background = on ? ACTIVE_BG : BTN_BG;
            dice.style.borderColor = on ? ACCENT : BTN_BORDER;
            dice.style.opacity = on ? "1" : "0.55";
            rndRow.style.display = on ? "flex" : "none";
            range.disabled = !!on;
            range.style.opacity = on ? "0.35" : "1";
            num.textContent = on ? "\u{1F3B2}" : String(Math.round(w.value));
            if (on) { lo.value = String(sp[0]); hi.value = String(sp[1]); }
        };
        dice.onclick = () => {
            state.randomize = state.randomize || {};
            state.randomize.sliders = state.randomize.sliders || {};
            if (spec()) delete state.randomize.sliders[name];
            else state.randomize.sliders[name] = [min, max];
            paint();
            sync();
        };
        const writeRange = () => {
            const a = parseFloat(lo.value), b = parseFloat(hi.value);
            if (!Number.isFinite(a) || !Number.isFinite(b)) return;
            state.randomize.sliders[name] = [a, b];
            sync();
        };
        lo.oninput = writeRange;
        hi.oninput = writeRange;
        range.oninput = () => {
            const v = parseFloat(range.value);
            w.value = v;
            num.textContent = String(Math.round(v));
            markCustom();
            schedulePreview();
            app.graph?.setDirtyCanvas(true, false);
        };
        helpOn(lab, label, name);
        helpOn(range, label, name);
        helpOn(dice, label + " — dice", "dice");
        helpOn(rndRow, label + " — range", "dice_range");

        parent.appendChild(row);
        parent.appendChild(rndRow);
        syncers.push(() => { range.value = String(w.value); paint(); });
        paint();
    };

    const bindSegments = (parent, hue, name, label, choices) => {
        const w = node.widgets.find((x) => x.name === name);
        if (!w) return;
        hideWidget(w);
        const row = el("div", { ...S.row, gap: "3px", flexWrap: "wrap" });
        const lab = el("span", { width: "62px", color: TEXT_DIM, fontSize: "10px",
                                 flexShrink: "0", cursor: "help" },
                       { textContent: label });
        row.appendChild(helpOn(lab, label, name));
        const btns = {};
        const mark = () => {
            for (const val of Object.keys(btns)) {
                const on = String(w.value) === val;
                btns[val].style.background = on ? ACTIVE_BG : BTN_BG;
                btns[val].style.borderColor = on ? ACCENT : BTN_BORDER;
                btns[val].style.color = on ? ACTIVE_FG : TEXT_DIM;
            }
        };
        for (const pair of choices) {
            const b = el("button", { ...S.btn, padding: "2px 5px", fontSize: "9px" },
                         { textContent: pair[1] });
            b.onclick = () => {
                w.value = pair[0];
                mark();
                markCustom();
                schedulePreview();
                app.graph?.setDirtyCanvas(true, false);
            };
            helpOn(b, `${label}: ${pair[1]}`, `${name}:${pair[0]}`);
            btns[pair[0]] = b;
            row.appendChild(b);
        }
        mark();
        parent.appendChild(row);
        syncers.push(mark);
    };

    // ====================================================== section: screen
    bindSlider(screenBody, ACCENT, "scale", "scale");
    bindSlider(screenBody, ACCENT, "roughness", "roughness");
    bindSlider(screenBody, ACCENT, "offset_angles", "angle step");
    bindSlider(screenBody, ACCENT, "rotate", "rotate");
    bindSlider(screenBody, ACCENT, "plate_drift", "misregister");

    // =============================================== section: ink and press
    bindSlider(inkPressBody, ACCENT, "ink_multiply", "multiply");
    bindSlider(inkPressBody, ACCENT, "ink_fade", "ink fade");
    bindSlider(inkPressBody, ACCENT, "dot_gain", "dot gain");
    bindSlider(inkPressBody, ACCENT, "brightness", "brightness");
    bindSlider(inkPressBody, ACCENT, "contrast", "contrast");
    bindSegments(inkPressBody, ACCENT, "plate_render", "plate",
                 [["uniform", "Uniform"], ["benday", "Ben-Day"]]);
    bindSegments(inkPressBody, ACCENT, "tint_quantize", "tint calls",
                 [["off", "Off"], ["25/50", "25/50"], ["25/50/75", "25/50/75"],
                  ["20/50", "20/50"], ["10/20/50/70", "10/20/50/70"]]);

    // ============================================== section: colour & inks
    const modeRow = el("div", { ...S.row, gap: "4px" });
    const btnMatch = el("button", { ...S.btn, flex: "1", fontSize: "10px", padding: "2px" },
                        { textContent: "Color Match" });
    const btnTint = el("button", { ...S.btn, flex: "1", fontSize: "10px", padding: "2px" },
                       { textContent: "Tint" });
    const markMode = () => {
        for (const [b, on] of [[btnMatch, state.mode !== "tint"], [btnTint, state.mode === "tint"]]) {
            b.style.background = on ? ACTIVE_BG : BTN_BG;
            b.style.borderColor = on ? ACCENT : BTN_BORDER;
            b.style.color = on ? ACTIVE_FG : TEXT_DIM;
        }
    };
    btnMatch.onclick = () => { state.mode = "color_match"; markMode(); sync(); };
    btnTint.onclick = () => { state.mode = "tint"; markMode(); sync(); };
    helpOn(btnMatch, "Color Match", "color_match");
    helpOn(btnTint, "Tint", "tint");
    modeRow.appendChild(btnMatch); modeRow.appendChild(btnTint);
    inkBody.appendChild(modeRow);

    const bgRow = el("div", S.row);
    bgRow.appendChild(el("span", { flex: "1", color: TEXT_DIM, fontSize: "10px" },
                         { textContent: "Background / paper" }));
    const bgInput = el("input", { width: "40px", height: "20px", border: "none",
                                  background: "none", cursor: "pointer" },
                       { type: "color", value: state.background });
    bgInput.oninput = () => { state.background = bgInput.value; sync(); };
    bgRow.appendChild(bgInput);
    helpOn(bgRow, "background", "background");
    inkBody.appendChild(bgRow);

    // -- ink palette gallery (pure swatches, no server round trip)
    const palWrap = el("div", { display: "grid", gridTemplateColumns: "repeat(2, 1fr)",
                                gap: "4px", maxHeight: "150px", overflowY: "auto",
                                paddingRight: "2px" });
    const applyPalette = (p) => {
        if (!p) return;
        state.inks = p.inks.map((c) => ({ color: c, on: true }));
        state.background = p.background;
        bgInput.value = p.background;
        renderInks();
        sync();
    };
    const buildPalettes = () => {
        palWrap.innerHTML = "";
        // ordered by hue, so related schemes sit together
        const entries = Object.entries(META.palettes || {}).sort(
            (a, b) => paletteHue(a[1]) - paletteHue(b[1]));
        for (const [name, p] of entries) {
            const chip = el("div", { cursor: "pointer", borderRadius: "4px",
                                     border: "1px solid #2f2b42", overflow: "hidden" });
            const strip = el("div", { display: "flex", height: "22px",
                                      background: p.background });
            for (const c of p.inks) {
                strip.appendChild(el("div", { flex: "1", background: c }));
            }
            const cap = el("div", { fontSize: "8px", color: TEXT_DIM2, padding: "1px 3px",
                                    whiteSpace: "nowrap", overflow: "hidden",
                                    textOverflow: "ellipsis" }, { textContent: name });
            chip.appendChild(strip); chip.appendChild(cap);
            chip.onclick = () => applyPalette(p);
            chip.addEventListener("mouseenter", () => {
                helpTitle.textContent = name;
                helpBody.textContent = `${p.inks.length} inks on ${p.background}. `
                    + (META.help?.palette || "");
            });
            chip.addEventListener("mouseleave", clearHelp);
            palWrap.appendChild(chip);
        }
    };
    inkBody.appendChild(palWrap);

    // -- randomize-per-run flags
    const rndRow = el("div", { ...S.row, flexWrap: "wrap", gap: "7px" });
    rndRow.appendChild(el("span", { color: TEXT_DIM, fontSize: "9px" },
                          { textContent: "Random per run:" }));
    const rndBoxes = {};
    for (const [key, label, hk] of [["palette", "Inks", "rnd_palette"],
                                    ["background", "Paper", "rnd_background"],
                                    ["ink_patterns", "Ink pat.", "rnd_ink_patterns"]]) {
        const lbl = el("label", { display: "flex", alignItems: "center", gap: "3px",
                                  cursor: "pointer", fontSize: "9px" });
        const cb = el("input", { accentColor: ACCENT },
                      { type: "checkbox", checked: !!(state.randomize || {})[key] });
        cb.onchange = () => {
            state.randomize = state.randomize || {};
            state.randomize[key] = cb.checked;
            sync();
        };
        rndBoxes[key] = cb;
        lbl.appendChild(cb);
        lbl.appendChild(el("span", {}, { textContent: label }));
        helpOn(lbl, label, hk);
        rndRow.appendChild(lbl);
    }
    inkBody.appendChild(rndRow);

    // -- ink list
    const inkList = el("div", { display: "flex", flexDirection: "column", gap: "3px" });
    inkBody.appendChild(inkList);

    let showAdv = false;
    const renderInks = () => {
        inkList.innerHTML = "";
        state.inks.forEach((ink, i) => {
            const row = el("div", { ...S.row, gap: "4px", background: ROW_BG,
                                    borderRadius: "4px 4px 0 0", padding: "3px 4px" });
            const color = el("input", { width: "28px", height: "18px", border: "none",
                                        background: "none", cursor: "pointer" },
                             { type: "color", value: ink.color });
            color.oninput = () => { ink.color = color.value; sync(); };
            helpOn(color, `ink ${i + 1}`, "ink_color");

            const patSel = el("select", { background: BTN_BG, color: TEXT_DIM2,
                                          border: "1px solid #45405e", borderRadius: "4px",
                                          fontSize: "9px", maxWidth: "64px" });
            patSel.appendChild(el("option", {}, { value: "", textContent: "node pat." }));
            for (const id of PATTERN_IDS) {
                patSel.appendChild(el("option", {}, { value: id,
                                                      textContent: PATTERN_LABELS[id] }));
            }
            patSel.value = ink.pattern || "";
            patSel.onchange = () => {
                if (patSel.value) ink.pattern = patSel.value;
                else delete ink.pattern;
                sync();
            };
            helpOn(patSel, `ink ${i + 1} pattern`, "ink_pattern");

            const mkToggle = (text, key, label, hk) => {
                const b = el("button", { ...S.btn, padding: "0 4px", fontSize: "9px",
                                         lineHeight: "15px" }, { textContent: text });
                const paint = () => {
                    b.style.background = ink[key] ? ACTIVE_BG : BTN_BG;
                    b.style.borderColor = ink[key] ? ACCENT : BTN_BORDER;
                    b.style.color = ink[key] ? ACTIVE_FG : TEXT_DIM;
                };
                paint();
                b.onclick = () => {
                    if (ink[key]) delete ink[key]; else ink[key] = true;
                    paint(); sync();
                };
                helpOn(b, label, hk);
                return b;
            };
            const diceC = mkToggle("\u{1F3B2}c", "rnd_color", `ink ${i + 1} colour dice`,
                                   "ink_rnd_color");
            const diceP = mkToggle("\u{1F3B2}p", "rnd_pattern", `ink ${i + 1} pattern dice`,
                                   "ink_rnd_pattern");

            const eye = el("button", { ...S.btn, padding: "0 5px", fontSize: "9px",
                                       lineHeight: "15px",
                                       opacity: ink.on ? "1" : "0.35" },
                           { textContent: ink.on ? "\u{1F441}" : "✖" });
            eye.onclick = () => { ink.on = !ink.on; renderInks(); sync(); };
            helpOn(eye, `ink ${i + 1}`, "ink_eye");

            const up = el("button", { ...S.btn, padding: "0 4px", fontSize: "9px",
                                      lineHeight: "15px" }, { textContent: "▲" });
            up.onclick = () => {
                if (i > 0) { state.inks.splice(i - 1, 0, state.inks.splice(i, 1)[0]); renderInks(); sync(); }
            };
            const down = el("button", { ...S.btn, padding: "0 4px", fontSize: "9px",
                                        lineHeight: "15px" }, { textContent: "▼" });
            down.onclick = () => {
                if (i < state.inks.length - 1) {
                    state.inks.splice(i + 1, 0, state.inks.splice(i, 1)[0]); renderInks(); sync();
                }
            };
            helpOn(up, "print order", "ink_move");
            helpOn(down, "print order", "ink_move");

            const del = el("button", { ...S.btn, padding: "0 5px", fontSize: "9px",
                                       lineHeight: "15px", color: "#c88" },
                           { textContent: "✕" });
            del.onclick = () => { state.inks.splice(i, 1); renderInks(); sync(); };
            helpOn(del, `remove ink ${i + 1}`, "ink_delete");

            row.appendChild(color); row.appendChild(patSel);
            row.appendChild(diceC); row.appendChild(diceP);
            row.appendChild(el("span", { flex: "1" }, {}));
            row.appendChild(eye); row.appendChild(up);
            row.appendChild(down); row.appendChild(del);

            const wrap = el("div", { display: "flex", flexDirection: "column" });
            wrap.appendChild(row);
            if (showAdv) {
                const adv = el("div", { ...S.row, background: ROW_BG2, gap: "4px",
                                        borderRadius: "0 0 4px 4px", padding: "2px 5px",
                                        fontSize: "9px", color: TEXT_DIM2 });
                const num = (label, key, placeholder, step, hk) => {
                    const sp = el("span", {}, { textContent: label });
                    const inp = el("input", { width: "38px", background: BTN_BG,
                                              color: TEXT, border: "1px solid #45405e",
                                              borderRadius: "4px", fontSize: "9px" },
                                   { type: "number", step: String(step), placeholder,
                                     value: ink[key] === undefined ? "" : String(ink[key]) });
                    inp.oninput = () => {
                        const v = parseFloat(inp.value);
                        if (Number.isFinite(v)) ink[key] = v; else delete ink[key];
                        sync();
                    };
                    helpOn(sp, label, hk); helpOn(inp, label, hk);
                    adv.appendChild(sp); adv.appendChild(inp);
                };
                num("angle", "angle", "auto", 1, "ink_angle");
                num("freq", "freq", "1", 0.05, "ink_freq");
                const so = el("button", { ...S.btn, padding: "0 5px", fontSize: "9px",
                                          lineHeight: "15px", marginLeft: "auto",
                                          background: ink.solid_only ? ACTIVE_BG : BTN_BG,
                                          borderColor: ink.solid_only ? ACCENT : BTN_BORDER,
                                          color: ink.solid_only ? ACTIVE_FG : TEXT_DIM },
                              { textContent: "solid only" });
                so.onclick = () => {
                    if (ink.solid_only) delete ink.solid_only; else ink.solid_only = true;
                    renderInks(); sync();
                };
                helpOn(so, "solid only", "ink_solid_only");
                adv.appendChild(so);
                wrap.appendChild(adv);
            }
            inkList.appendChild(wrap);
        });
        fitHeight?.();
    };

    const toolRow = el("div", { ...S.row, gap: "4px", flexWrap: "wrap" });
    const addBtn = el("button", { ...S.btn, fontSize: "9px", padding: "2px 6px" },
                      { textContent: "+ Ink" });
    addBtn.onclick = () => {
        if (state.inks.length >= 8) return;
        state.inks.push({ color: "#666666", on: true });
        renderInks(); sync();
    };
    helpOn(addBtn, "add ink", "add_ink");
    const sortBtn = el("button", { ...S.btn, fontSize: "9px", padding: "2px 6px" },
                       { textContent: "Auto Sort" });
    sortBtn.onclick = () => {
        state.inks.sort((a, b) => hexLum(b.color) - hexLum(a.color));
        renderInks(); sync();
    };
    helpOn(sortBtn, "auto sort", "auto_sort");
    const advLbl = el("label", { ...S.row, gap: "3px", cursor: "pointer", fontSize: "9px" });
    const advCb = el("input", { accentColor: ACCENT }, { type: "checkbox", checked: showAdv });
    advCb.onchange = () => { showAdv = advCb.checked; renderInks(); };
    advLbl.appendChild(advCb);
    advLbl.appendChild(el("span", {}, { textContent: "angle / freq" }));
    helpOn(advLbl, "per-ink fields", "adv_toggle");
    const opaqueLbl = el("label", { ...S.row, gap: "3px", cursor: "pointer", fontSize: "9px" });
    const opaqueCb = el("input", { accentColor: ACCENT },
                        { type: "checkbox", checked: !!state.opaque_bottom });
    opaqueCb.onchange = () => { state.opaque_bottom = opaqueCb.checked; sync(); };
    opaqueLbl.appendChild(opaqueCb);
    opaqueLbl.appendChild(el("span", {}, { textContent: "opaque bottom" }));
    helpOn(opaqueLbl, "opaque bottom ink", "opaque_bottom");
    toolRow.appendChild(addBtn); toolRow.appendChild(sortBtn);
    toolRow.appendChild(advLbl); toolRow.appendChild(opaqueLbl);
    inkBody.appendChild(toolRow);

    // ------------------------------------------------ seed to the very end
    try {
        const tail = [];
        for (const nm of ["seed", "control_after_generate"]) {
            const idx = node.widgets.findIndex((x) => x.name === nm);
            if (idx >= 0) tail.push(node.widgets.splice(idx, 1)[0]);
        }
        for (const w of tail) node.widgets.push(w);
    } catch (e) { /* frontend may manage order itself; harmless */ }

    const seedW = node.widgets.find((x) => x.name === "seed");
    if (seedW) {
        const origSeedCb = seedW.callback;
        seedW.callback = function (...a) { origSeedCb?.apply(this, a); schedulePreview(); };
    }

    // ---------------------------------------------------------- lifecycle
    const refresh = () => {
        state = parseState(cfgW.value);
        bgInput.value = state.background;
        opaqueCb.checked = !!state.opaque_bottom;
        for (const key of Object.keys(rndBoxes)) {
            rndBoxes[key].checked = !!(state.randomize || {})[key];
        }
        markMode(); markPattern(); renderInks();
        for (const f of syncers) f();
        markPreset();
        schedulePreview();
    };
    node._cmykRefresh = refresh;

    markMode();
    markPattern();
    renderInks();
    clearHelp();

    fetchData().then((data) => {
        META = data;
        buildPresetGallery();
        buildPalettes();
        clearHelp();
        fitHeight();
    });

    node.addDOMWidget("cmyk_ui", "div", root, { serialize: false });
    node.setSize([Math.max(MIN_W, uiState.width),
                  Math.max(uiState.height || 0, MIN_H)]);
    fitHeight();
    schedulePreview();
}

app.registerExtension({
    name: "printlook.cmyk_magic",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CMYKMagic") return;
        const onCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onCreated?.apply(this, arguments);
            buildPanel(this);
        };
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            onConfigure?.apply(this, arguments);
            this._cmykRefresh?.();
        };
    },
});
