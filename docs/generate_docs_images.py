"""
Regenerate the documentation images in docs/images.

Runs the CMYK Magic engine over one source image, changing one thing at a time,
and writes a labelled comparison strip or grid per topic. The engine is called
through the same `resolve_settings` / `run_resolved` pair the node and the live
preview use, so these images cannot drift from what the node actually produces.

Defaults are read straight off the node's INPUT_TYPES, so a strip always sweeps
around the real defaults rather than a copy that goes stale.

    python docs/generate_docs_images.py path/to/source.png

Options:
    --out DIR       where to write (default: docs/images)
    --only NAME     regenerate a single image, e.g. --only patterns
    --width N       per-panel width in pixels (default: 300)
    --comfy PATH    ComfyUI root, if it is not the usual place
    --ext jpg|png   output format (default: jpg)
    --list          print the image names and exit
"""

import argparse
import importlib.util
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)


def load_package(comfy_root):
    """Import the node package. It needs ComfyUI importable, because the engine
    asks comfy.model_management which device to use; --cpu keeps it off a GPU
    that a running ComfyUI may already be holding."""
    sys.argv = [sys.argv[0], "--cpu"]
    if comfy_root and comfy_root not in sys.path:
        sys.path.insert(0, comfy_root)
    spec = importlib.util.spec_from_file_location(
        "cmykpkg", os.path.join(PKG_ROOT, "__init__.py"),
        submodule_search_locations=[PKG_ROOT])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cmykpkg"] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# Image helpers
# --------------------------------------------------------------------------

def load_image(path, max_side):
    import torch
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        s = max_side / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None, ...]


def to_pil(tensor):
    arr = (tensor[0].detach().cpu().clamp(0, 1).numpy() * 255).astype(np.uint8)
    return Image.fromarray(arr)


def center_crop(im, frac):
    w, h = im.size
    cw, ch = round(w * frac), round(h * frac)
    return im.crop(((w - cw) // 2, (h - ch) // 2, (w - cw) // 2 + cw, (h - ch) // 2 + ch))


def _font(size):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def make_grid(panels, title, subtitle, panel_width, cols=None):
    """panels: list of (label, PIL.Image). Lays them out in a labelled grid."""
    n = len(panels)
    cols = cols or n
    rows = (n + cols - 1) // cols
    ph = round(panels[0][1].height * panel_width / panels[0][1].width)

    pad, label_h, title_h, line_h = 12, 30, 40, 23
    width = cols * panel_width + (cols + 1) * pad

    sub_font = _font(17)
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    sub_lines = wrap_text(subtitle, sub_font, width - 2 * pad, measure) if subtitle else []
    sub_h = len(sub_lines) * line_h + (6 if sub_lines else 0)

    height = title_h + sub_h + rows * (label_h + ph) + (rows + 1) * pad

    canvas = Image.new("RGB", (width, height), (18, 18, 20))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, pad), title, fill=(238, 238, 243), font=_font(25))
    for i, line in enumerate(sub_lines):
        draw.text((pad, pad + title_h - 8 + i * line_h), line,
                  fill=(140, 145, 158), font=sub_font)

    top0 = title_h + sub_h + pad
    for i, (label, im) in enumerate(panels):
        r, c = divmod(i, cols)
        x = pad + c * (panel_width + pad)
        y = top0 + r * (label_h + ph)
        draw.text((x + (panel_width - draw.textlength(label, font=_font(19))) / 2,
                   y + 3), label, fill=(185, 190, 200), font=_font(19))
        canvas.paste(im.resize((panel_width, ph), Image.LANCZOS), (x, y + label_h))

    return canvas


def ink_name(rgb):
    """A rough colour name for a plate label. Print inks cluster tightly enough
    around the process hues that this reads correctly in practice."""
    r, g, b = [c / 255.0 if c > 1 else c for c in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if lum < 0.22:
        return "black"
    if mx - mn < 0.12:
        return "grey" if lum < 0.85 else "white"
    if mx == r:
        h = (60 * ((g - b) / (mx - mn))) % 360
    elif mx == g:
        h = 60 * (2 + (b - r) / (mx - mn))
    else:
        h = 60 * (4 + (r - g) / (mx - mn))
    for lo, hi, name in ((20, 45, "orange"), (45, 70, "yellow"), (70, 160, "green"),
                         (160, 200, "cyan"), (200, 260, "blue"),
                         (260, 345, "magenta")):
        if lo <= h < hi:
            return name
    return "red"


def save(im, out_dir, stem, ext):
    path = os.path.join(out_dir, f"{stem}.{ext}")
    if ext == "jpg":
        im.save(path, "JPEG", quality=92, subsampling=0, optimize=True)
    else:
        im.save(path, "PNG")
    print(f"wrote {os.path.basename(path)}")
    return path


# --------------------------------------------------------------------------
# What to render
# --------------------------------------------------------------------------

# Documentation images get a coarser screen than you would normally print at.
# The default scale of 60 is fine press: at README width those dots are a pixel
# or two and the whole point of the node becomes invisible.
SHOW_SCALE = 320

# The pattern grid is the exception. A slider sweep only has to show the slider
# moving, so a coarse screen suits it, but the pattern grid has to show what
# each screen actually looks like: at 320 the dots grow so large that the shape
# of the pattern swamps the picture and the finer screens stop being
# distinguishable from one another.
PATTERN_SCALE = 120

# A dozen of the 37 presets, chosen to span the families rather than to be a
# catalogue: newsprint, the three comic eras, poster stock, and the odd ones.
PRESETS_SHOWN = [
    "Vintage Poster", "Comic CMYK", "Golden Age Comic", "DC Golden Age",
    "Silver Age", "Bronze Age 70s", "Sunday Funnies", "Newspaper",
    "Blueprint", "Mezzotint Plate", "Hypnotic Spiral", "8-Bit Dither",
]

# Twelve of the 17 patterns, one from each family.
PATTERNS_SHOWN = [
    "print_dots", "negative_dots", "elliptical", "square_dots",
    "lines", "cross_lines", "waves", "broken_waves",
    "fan_dots", "concentric", "spiral", "mezzotint",
]

# stem, title, subtitle, companion settings, swept key, values
SWEEPS = [
    dict(stem="scale", title="scale",
         sub="Halftone pattern size. Low is fine press, high is giant pop-art. Default 60.",
         base={}, key="scale", values=[30, 90, 200, 400]),

    dict(stem="roughness", title="roughness",
         sub="Distresses the screen from a clean press run to worn analog. Default 20.",
         base=dict(scale=SHOW_SCALE), key="roughness", values=[0, 30, 65, 100]),

    dict(stem="ink_multiply", title="ink_multiply",
         sub="0 is opaque paint that hides what is under it, 100 is pure multiply where every overlap darkens. Real ink sits in between. Default 60.",
         base=dict(scale=SHOW_SCALE), key="ink_multiply", values=[0, 40, 70, 100]),

    dict(stem="dot_gain", title="dot_gain",
         sub="Ink spread on absorbent stock: a called tint prints heavier than the film says. 0 is a calibrated press, 100 is newsprint letterpress. Default 35.",
         base=dict(scale=SHOW_SCALE), key="dot_gain", values=[0, 35, 70, 100]),

    dict(stem="ink_fade", title="ink_fade",
         sub="Worn, mottled ink density, as if the press was running low. Default 10.",
         base=dict(scale=SHOW_SCALE), key="ink_fade", values=[0, 30, 60, 100]),

    dict(stem="plate_drift", title="plate_drift",
         sub="Per-ink misregistration in pixels: the plates do not line up, exactly like cheap colour printing. Default 1.5.",
         base=dict(scale=SHOW_SCALE), key="plate_drift", values=[0, 3, 10, 25], crop=0.45),

    dict(stem="contrast", title="contrast",
         sub="Pre-grade applied before separation, so it changes which inks get called for rather than just the final look. Default 0.",
         base=dict(scale=SHOW_SCALE), key="contrast", values=[-60, -20, 20, 60]),

    dict(stem="offset_angles", title="offset_angles",
         sub="Screen-angle step between successive inks. Real presses use offsets like this to stop the plates forming a moire. Default 60.",
         base=dict(scale=SHOW_SCALE), key="offset_angles", values=[0, 15, 45, 90], crop=0.45),

    dict(stem="rotate", title="rotate",
         sub="Rotates the whole screen set at once, keeping the relative angles between inks. Default 0.",
         base=dict(scale=SHOW_SCALE), key="rotate", values=[0, 15, 30, 45], crop=0.45),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?")
    ap.add_argument("--out", default=os.path.join(HERE, "images"))
    ap.add_argument("--only")
    ap.add_argument("--width", type=int, default=380)
    ap.add_argument("--max-side", type=int, default=768)
    ap.add_argument("--ext", choices=["jpg", "png"], default="jpg")
    ap.add_argument("--comfy", default=r"D:\AIstuff\ComfyUI_v2\ComfyUI",
                    help="ComfyUI root (needed for comfy.model_management)")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    names = ["source", "presets", "patterns"] + [s["stem"] for s in SWEEPS] + \
            ["plate_render", "tint_quantize", "benday_plates", "benday_rosette",
             "benday_eras", "random_shuffle", "random_pattern", "random_inks"]
    if args.list:
        for n in names:
            print(" ", n)
        return 0

    if not args.source:
        ap.error("a source image is required (or pass --list)")
    if not os.path.isfile(args.source):
        ap.error(f"source image not found: {args.source}")

    load_package(args.comfy)
    cm = importlib.import_module("cmykpkg.cmyk_magic")
    resolve_settings, run_resolved = cm.resolve_settings, cm.run_resolved

    # Defaults straight from the node, so these strips can never document
    # values the node no longer has.
    spec = cm.CMYKMagic.INPUT_TYPES()["required"]
    DEFAULTS = {k: v[1]["default"] for k, v in spec.items()
                if isinstance(v, tuple) and len(v) > 1 and isinstance(v[1], dict)
                and "default" in v[1]}
    DEFAULTS.setdefault("seed", 1996)

    os.makedirs(args.out, exist_ok=True)
    image = load_image(args.source, args.max_side)
    print(f"source: {args.source} -> {tuple(image.shape[1:3])}")

    def run_full(**over):
        """Returns (composite, plates, resolved). `plates` is one image per ink,
        each on white, which is the node's own separation output."""
        params = dict(DEFAULTS)
        params.update(over)
        resolved = resolve_settings(params)
        result, plates = run_resolved(image, resolved)
        return result, plates, resolved

    def run(**over):
        return to_pil(run_full(**over)[0])

    want = lambda n: (not args.only) or args.only == n

    if want("source"):
        save(to_pil(image), args.out, "source", args.ext)

    if want("presets"):
        panels = [(n, run(preset=n)) for n in PRESETS_SHOWN]
        save(make_grid(panels, "presets",
                       f"Twelve of the {len(cm.MAGIC_PRESETS)} built-in presets. A preset writes every setting at once, including the ink set, the paper colour and the per-ink screen angles, not just the sliders you can see.",
                       args.width, cols=3), args.out, "presets", args.ext)

    if want("patterns"):
        panels = [(n, run(pattern=n, scale=PATTERN_SCALE)) for n in PATTERNS_SHOWN]
        save(make_grid(panels, "pattern",
                       "Twelve of the 17 screen patterns, all at the same scale so the only difference is the pattern. Rendered finer than the slider sweeps on purpose: the point here is the character of each screen, and at a coarse scale the dot size swamps it. Dot screens, hatching, radial, and mezzotint's stochastic grain, which has no lattice at all.",
                       args.width, cols=3), args.out, "patterns", args.ext)

    for s in SWEEPS:
        if not want(s["stem"]):
            continue
        panels = []
        for v in s["values"]:
            im = run(**dict(s["base"], **{s["key"]: v}))
            if s.get("crop"):
                im = center_crop(im, s["crop"])
            panels.append((f"{s['key']} = {v:g}", im))
        save(make_grid(panels, s["title"], s["sub"], args.width),
             args.out, s["stem"], args.ext)

    if want("plate_render"):
        panels = [(v, run(plate_render=v, scale=SHOW_SCALE, tint_quantize="25/50"))
                  for v in ("uniform", "benday")]
        save(make_grid(panels, "plate_render",
                       "uniform screens every plate the same way. benday makes each plate carry several screens at once like a real Ben-Day plate: light tints as dots, deep tints as a line sheet, 100 percent as unscreened solid. Shown with tint_quantize at 25/50.",
                       args.width * 2, cols=2), args.out, "plate_render", args.ext)

    if want("tint_quantize"):
        vals = ["off", "25/50", "25/50/75", "10/20/50/70"]
        panels = [(v, run(tint_quantize=v, scale=SHOW_SCALE)) for v in vals]
        save(make_grid(panels, "tint_quantize",
                       "Snaps every plate to the tint percentages a colourist could actually call for. 25/50 is the Craftint and Silver Age acetate system, four levels across three primaries, which is where the classic 64-colour comic palette comes from. Flat stepped fields, no gradients.",
                       args.width), args.out, "tint_quantize", args.ext)

    # ---- the randomisation controls ---------------------------------
    import json

    if want("random_shuffle"):
        shortlist = ["Comic CMYK", "Newspaper", "Blueprint", "Hypnotic Spiral"]
        cfg = json.loads(cm._DEFAULT_CFG)
        cfg["randomize"] = {"presets": shortlist}
        panels = [(f"seed {sd}", run(ink_config=json.dumps(cfg), seed=sd))
                  for sd in (1, 2, 3, 4)]
        save(make_grid(panels, "Shuffle: a shortlist of presets",
                       "With Shuffle on you tick several presets and one is drawn per run. Here the shortlist is Comic CMYK, Newspaper, Blueprint and Hypnotic Spiral, rendered at four seeds. The draw is seeded, so any result comes back by fixing the seed.",
                       args.width), args.out, "random_shuffle", args.ext)

    if want("random_pattern"):
        panels = [(f"seed {sd}", run(pattern="random", scale=SHOW_SCALE, seed=sd))
                  for sd in (1, 2, 3, 4)]
        save(make_grid(panels, "pattern = random",
                       "Setting the pattern widget to random draws a fresh screen from the seed each run. solid is excluded from the pool, because a flat ink field reads as a bug rather than variety.",
                       args.width), args.out, "random_pattern", args.ext)

    if want("random_inks"):
        cfg = json.loads(cm._DEFAULT_CFG)
        cfg["randomize"] = {"palette": True, "background": True}
        panels = [(f"seed {sd}", run(ink_config=json.dumps(cfg), scale=SHOW_SCALE, seed=sd))
                  for sd in (1, 2, 3, 4)]
        save(make_grid(panels, "Random per run: Inks + Paper",
                       f"Ticking Inks draws a whole ink set from the {len(cm.PALETTES)} built-in palettes; ticking Paper takes that palette's paper colour with it. Because the draw is a real palette rather than arbitrary RGB, a rolled result is always print-plausible.",
                       args.width), args.out, "random_inks", args.ext)

    # ---- why this reproduces the real Ben-Day process ---------------
    if want("benday_plates"):
        composite, plates, resolved = run_full(preset="Golden Age Comic")
        panels = []
        for i, ink in enumerate(resolved["inks"]):
            ang = ink.get("angle")
            label = ink_name(ink["rgb"]) + (f"  {ang:g}°" if ang else "")
            panels.append((label, to_pil(plates[i:i + 1])))
        panels.append(("composite", to_pil(composite)))
        save(make_grid(panels, "One plate per ink",
                       "The node's second output is the separation itself: every ink on its own plate, screened at its own angle, exactly as it would go to press. This is Golden Age Comic, whose four plates carry the Craftint angle set. Stack them in print order and you get the panel on the right.",
                       args.width, cols=len(panels)),
             args.out, "benday_plates", args.ext)

    if want("benday_rosette"):
        panels = []
        for v, note in ((0, "0, every plate aligned"), (15, "15"),
                        (30, "30"), (60, "60, the default")):
            # No preset here on purpose: most presets pin an absolute angle per
            # ink, and a per-ink angle overrides offset_angles completely, so a
            # preset would show no difference across this sweep at all.
            panels.append((f"offset_angles = {note}",
                           # A rosette is an interference pattern between dot
                           # grids, so it needs many dots in frame. This is the
                           # one strip that wants a finer screen, not a coarser
                           # one.
                           center_crop(run(offset_angles=v, scale=90,
                                           plate_drift=0, dot_gain=20), 0.4)))
        save(make_grid(panels, "Why the screen angles matter",
                       "Give every plate the same angle and the dots stack on top of each other into a coarse, blotchy moire. Offset them and the overlaps scatter into the rosette that real four-colour printing produces. This is the whole reason presses bothered with angle sets. Rendered with the default ink set, because a preset that pins an absolute angle per ink ignores this control entirely. Native-resolution crop.",
                       args.width), args.out, "benday_rosette", args.ext)

    if want("benday_eras"):
        eras = [
            ("Craftint Golden Age", "1938-55: Y75 M45 C105, 25% dots and 50% diagonal lines"),
            ("DC Golden Age", "as DC printed to 1969: no yellow tints, 32 colours"),
            ("Silver Age", "acetate method: Y90 M75 C105 K45, 50% as negative dots"),
            ("Bronze Age 70s", "cheap 70s camera: every plate at one angle, no rosette"),
        ]
        panels = [(name, run(preset=name)) for name, _ in eras]
        sub = ("Four presets modelling four real printing eras, each with the screen "
               "angles, tint calls and plate rendering that era actually used. "
               + "  ".join(f"{n}: {d}." for n, d in eras))
        save(make_grid(panels, "Four real printing eras", sub, args.width, cols=2),
             args.out, "benday_eras", args.ext)

    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
