"""CMYK Magic engine: Retratone-style custom-ink halftone separation.

Pipeline: grade -> separate the image into per-ink coverage plates (color-match
solves per-pixel for the best mix of the chosen inks; tint maps inks across the
luminance axis like a gradient map) -> screen each plate with a print pattern at
its own angle -> composite the plates in print order with a normal<->multiply
ink blend over the background -> dust & scratches.

Everything is procedural pure-torch, seeded, and resolution-aware.
"""

import math

import torch
import torch.nn.functional as F

import comfy.model_management

PATTERN_IDS = [
    "print_dots", "negative_dots", "elliptical", "square_dots", "bayer",
    "lines", "broken_lines", "cross_lines",
    "waves", "broken_waves", "cross_waves",
    "fan_dots", "negative_fan", "concentric", "spiral", "mezzotint", "solid",
]

# Ordered dither needs a near-hard threshold: its 64 levels sit 1/64 apart, so
# the normal anti-alias width would smear them back into a gradient.
HARD_PATTERNS = {"bayer"}

# Ben-Day plates carried several screens at once: light tints as dots, deep
# tints as a line/hatch sheet, full strength as an unscreened solid fill.
# This maps a plate's base pattern to the sheet used for its dark band.
SHADOW_PATTERN = {
    "print_dots": "lines", "negative_dots": "lines",
    "elliptical": "lines", "square_dots": "lines", "bayer": "cross_lines",
    "concentric": "lines", "spiral": "lines", "mezzotint": "cross_lines",
    "fan_dots": "lines", "negative_fan": "lines",
    "lines": "cross_lines", "broken_lines": "cross_lines",
    "cross_lines": "cross_lines",
    "waves": "cross_waves", "broken_waves": "cross_waves",
    "cross_waves": "cross_waves",
}


# --------------------------------------------------------------------- helpers

def make_generator(seed, device):
    seed = int(seed) & 0xffffffffffffffff
    try:
        gen = torch.Generator(device=device)
    except Exception:
        gen = torch.Generator()
    try:
        gen.manual_seed(seed)
    except RuntimeError:
        gen.manual_seed(seed % (2 ** 63))
    return gen


def _rand(shape, gen, device):
    return torch.rand(shape, generator=gen, device=gen.device, dtype=torch.float32).to(device)


def smoothstep(edge0, edge1, x):
    t = ((x - edge0) / (edge1 - edge0)).clamp(0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _grid(h, w, device):
    yy, xx = torch.meshgrid(
        torch.arange(h, device=device, dtype=torch.float32),
        torch.arange(w, device=device, dtype=torch.float32),
        indexing="ij",
    )
    return yy, xx


def _hw1(field):
    return field[None, :, :, None]


def fractal_noise(h, w, base_cell_px, octaves, persistence, gen, device):
    acc = torch.zeros((h, w), device=device, dtype=torch.float32)
    amp = 1.0
    total = 0.0
    base_cell = max(float(base_cell_px), 2.0)
    for i in range(octaves):
        cell = max(2.0, base_cell / (2 ** i))
        gh = min(h, int(h / cell) + 2)
        gw = min(w, int(w / cell) + 2)
        grid = _rand((1, 1, gh, gw), gen, device)
        layer = F.interpolate(grid, size=(h, w), mode="bicubic", align_corners=False)[0, 0]
        acc = acc + amp * layer.clamp(0.0, 1.0)
        total += amp
        amp *= persistence
    acc = acc / total
    lo, hi = acc.min(), acc.max()
    return ((acc - lo) / (hi - lo + 1e-8)).clamp(0.0, 1.0)


def gaussian_blur_bhwc(img, sigma):
    sigma = float(sigma)
    if sigma <= 0.05:
        return img
    radius = max(1, int(math.ceil(sigma * 3.0)))
    radius = min(radius, 63)
    x = torch.arange(-radius, radius + 1, device=img.device, dtype=img.dtype)
    k = torch.exp(-(x * x) / (2.0 * sigma * sigma))
    k = k / k.sum()
    b, h, w, c = img.shape
    t = img.permute(0, 3, 1, 2)
    kx = k.view(1, 1, 1, -1).repeat(c, 1, 1, 1)
    ky = k.view(1, 1, -1, 1).repeat(c, 1, 1, 1)
    pad_w = min(radius, w - 1)
    pad_h = min(radius, h - 1)
    t = F.pad(t, (pad_w, pad_w, 0, 0), mode="reflect")
    if pad_w < radius:
        t = F.pad(t, (radius - pad_w, radius - pad_w, 0, 0), mode="replicate")
    t = F.conv2d(t, kx, groups=c)
    t = F.pad(t, (0, 0, pad_h, pad_h), mode="reflect")
    if pad_h < radius:
        t = F.pad(t, (0, 0, radius - pad_h, radius - pad_h), mode="replicate")
    t = F.conv2d(t, ky, groups=c)
    return t.permute(0, 2, 3, 1)


def _lum_img(img):
    r, g, b = img[..., 0:1], img[..., 1:2], img[..., 2:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _lum_rgb(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


# -------------------------------------------------------------------- patterns

def _uv_noise(u, v, cell_u, cell_v, gen, device, octaves=2):
    """Value noise sampled in (u, v) screen coordinates with independent
    feature sizes per axis — the anisotropy that keeps distress aligned with
    the stroke direction instead of tangling it."""
    out = torch.zeros_like(u)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        g = _rand((1, 1, 96, 96), gen, device)
        cu = max(cell_u / (2 ** o), 1.0)
        cv = max(cell_v / (2 ** o), 1.0)
        # Centered, mirrored (triangle-wave) tiling: coordinates sit mid-grid
        # so typical images never cross a fold, and any fold is a smooth
        # mirror rather than a texel jump. Bicubic interpolation matters:
        # bilinear value noise is piecewise-linear, which turns wave rows
        # into straight segments with corner kinks instead of smooth curves.
        tu = torch.remainder(u / cu + 48.0, 192.0)
        tv = torch.remainder(v / cv + 48.0, 192.0)
        pu = ((96.0 - (tu - 96.0).abs()) / 96.0) * 2.0 - 1.0
        pv = ((96.0 - (tv - 96.0).abs()) / 96.0) * 2.0 - 1.0
        coords = torch.stack([pu, pv], dim=-1)[None]
        s = F.grid_sample(g, coords, mode="bicubic",
                          padding_mode="reflection", align_corners=False)[0, 0]
        out = out + amp * s.clamp(0.0, 1.0)
        total += amp
        amp *= 0.55
    out = out / total
    lo, hi = out.min(), out.max()
    return ((out - lo) / (hi - lo + 1e-8)).clamp(0.0, 1.0)


def _dot_screen(u, v, pitch, metric, norm):
    """Euclidean-style halftone dot of any shape: ink grows from the lattice
    points up to 50%, and beyond 50% the *paper* grows from the cell corners.

    That symmetry is what a real contact screen does, and why Silver Age comics
    show 'negative dots' in their darker tints: one screen, one position, only
    the exposure changed, so the light tint's positive dots sit exactly in the
    dark tint's grid. Measuring distance to the nearest centre only would leave
    four-cusped gaps above 50%, which reads digital.

    `metric` gives the distance from a lattice point (its shape is the dot's
    shape); `norm` is that metric's value at the cell corner."""
    fu, fv = u / pitch, v / pitch
    du, dv = fu - torch.round(fu), fv - torch.round(fv)
    d_dot = metric(du, dv)
    gu, gv = fu + 0.5, fv + 0.5
    hu, hv = gu - torch.round(gu), gv - torch.round(gv)
    d_hole = metric(hu, hv)
    s_dot = 0.5 + 0.5 * (1.0 - d_dot / norm).clamp(0.0, 1.0)
    s_hole = 0.5 - 0.5 * (1.0 - d_hole / norm).clamp(0.0, 1.0)
    return torch.where(d_dot <= d_hole, s_dot, s_hole)


def _round_dots(u, v, pitch):
    """Classic round halftone dot."""
    return _dot_screen(u, v, pitch, lambda a, b: a * a + b * b, 0.5)


def _elliptical_dots(u, v, pitch):
    """Chain dot: an elliptical screen. The dots touch along their long axis
    well before they touch across it, so mid tones link into chains instead of
    every dot joining its neighbours at once — the reason presses adopted it,
    since that simultaneous join produces a visible jump in tone at 50%."""
    return _dot_screen(u, v, pitch, lambda a, b: a * a + (b * b) / 0.42, 0.845)


def _square_dots(u, v, pitch):
    """Square dot screen: hard-edged tiles that mesh into a checkerboard at
    50%. Coarse, mechanical, and unmistakably screened."""
    return _dot_screen(u, v, pitch,
                       lambda a, b: torch.maximum(a.abs(), b.abs()), 0.5)


_BAYER8 = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]


def _bayer(u, v, pitch, device):
    """8x8 ordered dither: the threshold map early computers used to fake
    greys from pure black and white."""
    m = torch.tensor(_BAYER8, device=device, dtype=torch.float32)
    m = (m + 0.5) / 64.0
    cell = max(1.0, pitch / 2.6)
    iu = torch.remainder(torch.floor(u / cell), 8).long()
    iv = torch.remainder(torch.floor(v / cell), 8).long()
    return m[iu, iv]


def _line(u, pitch):
    return 0.5 + 0.5 * torch.cos(2.0 * math.pi * u / pitch)


def _flow(u, v, pitch, gen, device):
    """Wave rows as concentric curved contours: the row phase is a height
    field (directional ramp + large isotropic noise), so its level sets bend
    around the noise hills like fingerprint whorls. Small or elongated
    displacement only wiggles straight rows — the noise term must rival the
    ramp to make rows actually curve and swirl."""
    fl = _uv_noise(u, v, pitch * 18.0, pitch * 18.0, gen, device, octaves=2)
    return u + (fl - 0.5) * pitch * 11.0


def _chop(uw, v, pitch):
    """Diagonal dash chop for broken patterns: a second coarse line screen
    crossing the stroke, so lines break into aligned stitch-like dashes
    (dense areas stay continuous, light areas thin to sparse ticks)."""
    c = v + 0.35 * uw
    return _line(c, pitch * 2.3)


def screen_field(name, h, w, pitch, angle_deg, phase, roughness, gen, device):
    """Threshold field [H, W] in 0..1; higher values ink up first as coverage
    grows. roughness (0..1) distresses the pattern *along its own axes* —
    stroke direction survives, edges and spacing get organic."""
    yy, xx = _grid(h, w, device)

    if name in ("fan_dots", "negative_fan"):
        # Concentric arcs of dots radiating from a center below the canvas.
        cx, cy = w * 0.5 + phase[0], h * 1.45 + phase[1]
        dx, dy = xx - cx, yy - cy
        r = torch.sqrt(dx * dx + dy * dy) + 1e-4
        theta = torch.atan2(dy, dx)
        u, v = r, theta * r
    elif name in ("concentric", "spiral"):
        # Rings centred on the frame. The spiral is the same ring screen with
        # the radius advanced by one pitch per turn, so the line never closes.
        cx, cy = w * 0.5 + phase[0], h * 0.5 + phase[1]
        dx, dy = xx - cx, yy - cy
        r = torch.sqrt(dx * dx + dy * dy) + 1e-4
        theta = torch.atan2(dy, dx)
        u = r + (theta / (2.0 * math.pi)) * pitch if name == "spiral" else r
        v = theta * r
    else:
        a = math.radians(angle_deg)
        u = xx * math.cos(a) + yy * math.sin(a) + phase[0]
        v = -xx * math.sin(a) + yy * math.cos(a) + phase[1]

    if roughness > 0:
        # Across-stroke wander (u) is elongated along the stroke (v) so lines
        # undulate without losing direction; a smaller along-stroke jitter
        # keeps dot lattices from looking machine-stamped.
        wob = _uv_noise(u, v, pitch * 3.0, pitch * 9.0, gen, device)
        u = u + (wob - 0.5) * pitch * 0.9 * roughness
        job = _uv_noise(v, u, pitch * 3.0, pitch * 9.0, gen, device)
        v = v + (job - 0.5) * pitch * 0.45 * roughness

    if name in ("print_dots", "negative_dots", "fan_dots", "negative_fan"):
        s = _round_dots(u, v, pitch)
    elif name == "elliptical":
        s = _elliptical_dots(u, v, pitch)
    elif name == "square_dots":
        s = _square_dots(u, v, pitch)
    elif name == "bayer":
        s = _bayer(u, v, pitch, device)
    elif name == "mezzotint":
        # Stochastic grain: no lattice at all, like an aquatint ground.
        s = _uv_noise(u, v, pitch * 1.15, pitch * 1.15, gen, device, octaves=3)
    elif name in ("concentric", "spiral"):
        s = _line(u, pitch)
    elif name == "lines":
        s = _line(u, pitch)
    elif name == "broken_lines":
        s = _line(u, pitch) - 0.42 * (1.0 - _chop(u, v, pitch))
    elif name == "cross_lines":
        s = torch.maximum(_line(u, pitch), _line(v, pitch))
    elif name == "waves":
        s = _line(_flow(u, v, pitch, gen, device), pitch)
    elif name == "broken_waves":
        uw = _flow(u, v, pitch, gen, device)
        s = _line(uw, pitch) - 0.42 * (1.0 - _chop(uw, v, pitch))
    elif name == "cross_waves":
        s1 = _line(_flow(u, v, pitch, gen, device), pitch)
        s2 = _line(_flow(v, u, pitch, gen, device), pitch)
        s = torch.maximum(s1, s2)
    else:
        raise ValueError(f"Unknown pattern: {name}")

    if roughness > 0:
        # Ragged ink edges: fine fiber chatter plus concentrated torn bites.
        # Gentle symmetric noise only shifts edges sub-pixel — real letterpress
        # loses ink in chunks, so the bites are thresholded patches strong
        # enough to eat visibly into the stroke.
        fine = fractal_noise(h, w, 2.0, 2, 0.6, gen, device)
        mid = fractal_noise(h, w, max(2.5, pitch * 0.7), 2, 0.6, gen, device)
        s = s + (fine - 0.5) * 0.35 * roughness
        s = s - smoothstep(0.62, 0.88, mid) * 0.75 * roughness
        s = s + 0.09 * roughness  # re-center tone lost to the bites

    if name in ("negative_dots", "negative_fan"):
        s = 1.0 - s
    return s.clamp(0.0, 1.0)


def screen_eps(pitch, hard=False):
    """Soft-edge width of the screen threshold, in field-value units."""
    if hard:
        return 0.012
    return max(2.25 / max(float(pitch), 1.5), 1e-3)


def screen_lut(s_field, pitch, bins=64, max_samples=1 << 16, hard=False):
    """Tone calibration for a screen field: the inked-area response of the
    actual soft threshold, sampled over candidate threshold values.

    Two things make the naive `threshold at 1-cov` wrong. Screen fields are
    not uniformly distributed (a round-dot field inks ~1.77x the requested
    area), and the anti-aliasing ramp adds area of its own — wide enough at
    small pitch that a *blank* plate still printed ~20% gray. Measuring the
    real response and inverting it fixes both, and pinning the ends beyond
    the field range guarantees 0 coverage inks nothing and 1 inks solid.
    """
    eps = screen_eps(pitch, hard)
    flat = s_field.flatten()
    if flat.numel() > max_samples:
        flat = flat[:: max(1, flat.numel() // max_samples)]
    lo = float(flat.min()) - eps
    hi = float(flat.max()) + eps
    ts = torch.linspace(hi, lo, bins + 1, device=s_field.device, dtype=torch.float32)
    areas = (((flat[None, :] - ts[:, None]) / eps + 0.5).clamp(0.0, 1.0)).mean(dim=1)
    areas = torch.cummax(areas, dim=0).values  # enforce monotonic for searchsorted
    return areas.contiguous(), ts


def apply_screen(cov, s_field, pitch, lut=None, hard=False):
    """Soft-threshold coverage against a screen. With a lut the inked area
    matches the requested coverage (calibrated press); without one it falls
    back to the raw 1-cov threshold."""
    eps = screen_eps(pitch, hard)
    if lut is None:
        thresh = 1.0 - cov
    else:
        areas, ts = lut
        c = cov.clamp(0.0, 1.0).reshape(-1).contiguous()
        i = torch.searchsorted(areas, c).clamp(1, areas.numel() - 1)
        a0, a1 = areas[i - 1], areas[i]
        w = ((c - a0) / (a1 - a0).clamp(min=1e-6)).clamp(0.0, 1.0)
        thresh = torch.lerp(ts[i - 1], ts[i], w).reshape(cov.shape)
    return ((s_field - thresh) / eps + 0.5).clamp(0.0, 1.0)


def apply_dot_gain(cov, gain):
    """Ink spread on absorbent stock: a called tint prints heavier than film.
    gain 1.0 grows a 20% call to ~36%, matching newsprint letterpress."""
    if gain <= 0:
        return cov
    return (cov + gain * cov * (1.0 - cov)).clamp(0.0, 1.0)


# ---------------------------------------------------------------- compositing

def _ink_over(cur, ink_rgb, cov, mult):
    """One translucent ink layer over cur. mult 0 = opaque (normal blend),
    1 = pure multiply; between = the 'plasticol' half-opaque ink look."""
    over_nrm = cur * (1.0 - cov) + ink_rgb * cov
    over_mul = cur * (1.0 - cov * (1.0 - ink_rgb))
    return over_nrm + (over_mul - over_nrm) * mult


def composite_stack(paper_rgb, ink_rgbs, covs, mults):
    cur = paper_rgb * covs[0].new_ones(covs[0].shape[:-1] + (3,))
    for ink_rgb, cov, mult in zip(ink_rgbs, covs, mults):
        cur = _ink_over(cur, ink_rgb, cov, mult)
    return cur


# ---------------------------------------------------------------- separations

def separate_color_match(target, paper_rgb, ink_rgbs, mults, sweeps=3):
    """Per-pixel per-ink coverage by coordinate descent. The composite is
    affine in each ink's coverage, so each update is an exact 1-D least-squares
    solve; sweeping in print order converges in a few passes."""
    zeros = target[..., :1] * 0.0
    ones = zeros + 1.0
    covs = [zeros.clone() for _ in ink_rgbs]
    for _ in range(sweeps):
        for i in range(len(ink_rgbs)):
            covs[i] = zeros
            base = composite_stack(paper_rgb, ink_rgbs, covs, mults)
            covs[i] = ones
            full = composite_stack(paper_rgb, ink_rgbs, covs, mults)
            bvec = full - base
            num = ((target - base) * bvec).sum(-1, keepdim=True)
            den = (bvec * bvec).sum(-1, keepdim=True)
            cov = (num / den.clamp(min=1e-6)).clamp(0.0, 1.0)
            covs[i] = torch.where(den < 1e-5, zeros, cov)
    return covs


def separate_tint(lum, paper_rgb, ink_rgbs, positions=None):
    """Gradient-map separation: each ink lives at its own luminance (or an
    explicit per-ink position 0..1), the paper acts as an ink-free node, and
    triangular basis functions hand coverage between neighboring nodes."""
    if positions is None:
        positions = [None] * len(ink_rgbs)
    nodes = []
    for i, (c, p) in enumerate(zip(ink_rgbs, positions)):
        nodes.append((float(p) if p is not None else _lum_rgb(c), i))
    nodes.append((_lum_rgb(paper_rgb), None))
    nodes.sort(key=lambda t: t[0])
    pos = []
    for p, _ in nodes:
        if pos and p <= pos[-1] + 1e-3:
            p = pos[-1] + 1e-3
        pos.append(p)
    covs = [None] * len(ink_rgbs)
    m = len(nodes)
    for k, (_, idx) in enumerate(nodes):
        if idx is None:
            continue
        if k > 0:
            rise = ((lum - pos[k - 1]) / (pos[k] - pos[k - 1])).clamp(0.0, 1.0)
        else:
            rise = torch.ones_like(lum)
        if k < m - 1:
            fall = ((pos[k + 1] - lum) / (pos[k + 1] - pos[k])).clamp(0.0, 1.0)
        else:
            fall = torch.ones_like(lum)
        covs[idx] = torch.minimum(rise, fall)
    return covs


# ------------------------------------------------------------------- main run

# Vintage comic Ben-Day tint levels: colorists could only call for these
# plate percentages, so every color is a combo from a ~64/128-color palette.
# Named for the tint percentages they contain, not for an era — the same set
# of calls spans several eras, so era names here were actively misleading.
# 25/50 is what Craftint AND the Silver Age acetate system both offered; the
# 75 call only arrived in the early 1980s.
TINT_LEVELS = {
    "25/50": (0.0, 0.25, 0.5, 1.0),
    "25/50/75": (0.0, 0.25, 0.5, 0.75, 1.0),
    "20/50": (0.0, 0.2, 0.5, 1.0),
    "10/20/50/70": (0.0, 0.1, 0.2, 0.5, 0.7, 1.0),
}
# Old names kept so saved workflows keep working.
TINT_LEVELS.update({
    "craftint": TINT_LEVELS["25/50"],
    "silver_age": TINT_LEVELS["25/50/75"],
    "comic_4": TINT_LEVELS["20/50"],
    "comic_6": TINT_LEVELS["10/20/50/70"],
})

# Inks flagged solid_only never print a tint — DC left yellow tints out of
# their comics until 1969, which is why their flesh is flat pink.
SOLID_ONLY_LEVELS = (0.0, 1.0)


def run_cmyk_magic(image, inks, background, mode, opaque_bottom,
                   pattern, scale, roughness, brightness, contrast,
                   ink_multiply, ink_fade, plate_drift,
                   offset_angles, rotate, seed, tint_quantize="off", dot_gain=0.0,
                   plate_render="uniform"):
    """image: [B, H, W, C] 0..1. inks: list of dicts in print order (first =
    bottom): {"rgb": (r, g, b), "pattern": optional per-ink pattern id,
    "pos": optional tint position 0..1, "angle": optional absolute screen
    angle in degrees}. tint_quantize snaps plate coverage to vintage Ben-Day
    levels. Returns (result, plates)."""
    device = comfy.model_management.get_torch_device()
    img = image.to(device=device, dtype=torch.float32).clamp(0.0, 1.0)

    alpha = None
    if img.shape[-1] > 3:
        alpha = img[..., 3:]
        img = img[..., :3]
    elif img.shape[-1] == 1:
        img = img.expand(-1, -1, -1, 3).contiguous()

    b, h, w, _ = img.shape
    unit = max(0.35, min(4.0, min(h, w) / 1024.0))
    gen = make_generator(seed, device)
    out_dev = comfy.model_management.intermediate_device()

    # grade
    if abs(brightness) > 1e-3:
        img = (img + brightness * 0.35).clamp(0.0, 1.0)
    if abs(contrast) > 1e-3:
        img = ((img - 0.5) * (1.0 + contrast * 0.9) + 0.5).clamp(0.0, 1.0)

    paper_rgb = torch.tensor(background, device=device, dtype=torch.float32)
    if not inks:
        flat = (paper_rgb * img.new_ones(img.shape)).clamp(0.0, 1.0)
        out = flat if alpha is None else torch.cat([flat, alpha], dim=-1)
        return out.to(out_dev), out.to(out_dev)

    ink_rgbs = [torch.tensor(i["rgb"], device=device, dtype=torch.float32) for i in inks]
    mults = [ink_multiply] * len(ink_rgbs)
    if opaque_bottom:
        mults[0] = 0.0

    # separate into continuous coverage plates
    if mode == "tint":
        covs = separate_tint(_lum_img(img), paper_rgb, ink_rgbs,
                             [i.get("pos") for i in inks])
    else:
        covs = separate_color_match(img, paper_rgb, ink_rgbs, mults)

    # Snap each plate to the fixed tint calls of vintage comic separation (no
    # continuous gradients existed — only coded percentage fields). An ink can
    # override the set to solids only.
    base_levels = TINT_LEVELS.get(tint_quantize)
    for i in range(len(covs)):
        lv = SOLID_ONLY_LEVELS if inks[i].get("solid_only") else base_levels
        if lv is None:
            continue
        levels = torch.tensor(lv, device=device, dtype=torch.float32)
        covs[i] = levels[(covs[i].unsqueeze(-1) - levels).abs().argmin(dim=-1)]

    pitch = max(2.0, 0.12 * scale * unit)
    sigma = pitch * 0.06
    if sigma > 0.3:
        covs = [gaussian_blur_bhwc(c, sigma) for c in covs]

    # screen each plate at its own angle, with drift and fade; an ink may
    # carry its own pattern for mixed-pattern looks
    halftones = []
    for i, cov in enumerate(covs):
        pat = inks[i].get("pattern") or pattern
        ink_angle = inks[i].get("angle")
        angle = rotate + (float(ink_angle) if ink_angle is not None
                          else 45.0 + offset_angles * i)
        if plate_drift > 0:
            phase = tuple(((torch.rand(2, generator=gen, device=gen.device) * 2 - 1)
                           * plate_drift * unit).tolist())
        else:
            phase = (0.0, 0.0)
        cov = apply_dot_gain(cov, dot_gain)
        # Line frequency per plate: cheap newsprint ran the heavy inks coarser
        # so their dots would not bleed into a blob.
        freq = float(inks[i].get("freq") or 1.0)
        plate_pitch = max(2.0, pitch / max(0.15, freq))

        def _screen(p, _pp=plate_pitch, _a=angle, _ph=phase, _c=None):
            # Every plate re-seeds the same generator: all inks share one
            # master flow/distress drawing (like plates pulled from the same
            # artwork), separated only by angle and drift.
            sgen = make_generator((int(seed) & 0xffffffffffffffff) ^ 0x5EED0F10, device)
            field = screen_field(p, h, w, _pp, _a, _ph, roughness, sgen, device)
            hard = p in HARD_PATTERNS
            return apply_screen(_c, _hw1(field), _pp,
                                lut=screen_lut(field, _pp, hard=hard), hard=hard)

        if pat == "solid":
            ht = smoothstep(0.45, 0.55, cov)
        elif plate_render == "benday":
            # One plate, several screens, masked by tint level — the engraver
            # exposing a plate through separate Rubylith masks per pattern.
            # Craftint's three calls: 25% prints as dots, 50% as the diagonal
            # line sheet, 100% as unscreened solid. The bands are placed so the
            # 50% call lands squarely in the line band.
            ht = _screen(pat, _c=cov)
            shadow = SHADOW_PATTERN.get(pat)
            w_solid = smoothstep(0.80, 0.95, cov)
            if shadow is not None:
                w_line = smoothstep(0.34, 0.44, cov) * (1.0 - w_solid)
                ht = torch.lerp(ht, _screen(shadow, _c=cov), w_line)
            ht = ht * (1.0 - w_solid) + w_solid
        else:
            ht = _screen(pat, _c=cov)
        if ink_fade > 0:
            # Coarse worn patches plus hard paper-tooth show-through: the
            # tooth term punches real holes in the ink (dry pigment on rough
            # stock), not just a uniform dimming.
            mottle = _hw1(fractal_noise(h, w, pitch * 6.0, 2, 0.6, gen, device))
            tooth = _hw1(fractal_noise(h, w, 2.5, 2, 0.6, gen, device))
            ht = ht * (1.0 - ink_fade * (0.25 + 0.6 * mottle))
            ht = (ht - ink_fade * 0.85 * smoothstep(0.6, 0.85, tooth)).clamp(min=0.0)
        halftones.append(ht)

    result = composite_stack(paper_rgb, ink_rgbs, halftones, mults).clamp(0.0, 1.0)

    # per-ink plates on white, like Convert to Layers (ink-major batch order)
    white = torch.ones_like(result)
    plates = torch.cat(
        [white * (1.0 - ht * (1.0 - c)) for c, ht in zip(ink_rgbs, halftones)], dim=0
    ).clamp(0.0, 1.0)

    if alpha is not None:
        result = torch.cat([result, alpha], dim=-1)
    return result.to(out_dev), plates.to(out_dev)
