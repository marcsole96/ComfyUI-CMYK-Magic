# CMYK Magic: a visual guide

Every image on this page was made by running the node's own engine over one
source frame, changing one thing at a time. They go through the same
`resolve_settings` and `run_resolved` the node and its live preview use, so
nothing here can drift away from what you actually get.

Regenerate the whole set against your own image:

```bash
python docs/generate_docs_images.py path/to/your_image.png
```

The source frame:

![source](images/source.jpg)

---

## Presets

Twelve of the 37. The important thing to understand is that a preset is not a
slider arrangement: it writes **every** setting at once, including the ink set,
the paper colour, the per-ink screen angles and the plate rendering mode. So
loading one and then reading the visible widgets tells you most of the story but
not all of it. Tick **Per-ink angle / freq** in the panel if you want the rest
of it on screen.

![presets](images/presets.jpg)

Picking a preset loads it and stays selected; touching any setting afterwards
flips the widget back to Custom, because what you have is no longer that preset.
Headless, a preset name in the widget just overrides everything directly.

## Patterns

Twelve of the 17 screens, all at the same scale so the only difference is the
pattern itself.

![patterns](images/patterns.jpg)

They fall into families. **Dot screens** (print dots, negative dots, elliptical
chain dot, square dots) are the classic halftone. **Hatching** (lines, broken
lines, cross lines, waves, broken waves, cross waves) replaces dots with
strokes; the wave variants are concentric contour flows, fingerprint-like,
rather than periodic wiggles, and the broken ones chop into stitch dashes that
merge back into continuous lines in the dark areas. **Radial** (fan dots,
negative fan, concentric rings, spiral) throws the lattice away from a centre
point. Then two odd ones out: **mezzotint** is stochastic grain with no lattice
at all, and **solid** turns the screen off entirely for flat ink fields, which
is the one to use when you need type to stay sharp.

---

## The sliders

### `scale`
Default **60**. Pattern size, and the first thing to reach for. 20 is fine
press, 350 is pop-art the size of your thumb.

![scale](images/scale.jpg)

### `roughness`
Default **20**. Distresses the screen from a clean press run to worn analog.

![roughness](images/roughness.jpg)

### `ink_multiply`
Default **60**. What happens where two inks overlap. At 0 the top ink is opaque
paint and hides what is under it; at 100 it is pure multiply and every overlap
darkens. Real ink sits in between, which is why the default does too.

![ink_multiply](images/ink_multiply.jpg)

### `dot_gain`
Default **35**. Ink spreads on absorbent paper, so a called tint prints heavier
than the film says. 0 is a calibrated press where a 20 percent call inks exactly
20 percent. 100 is newsprint letterpress, where that 20 percent grows to about
36, which is the historical comic figure.

![dot_gain](images/dot_gain.jpg)

### `ink_fade`
Default **10**. Worn, mottled ink density, as though the press was running low.

![ink_fade](images/ink_fade.jpg)

### `plate_drift`
Default **1.5**. Per-ink misregistration in pixels. The plates do not line up,
exactly like cheap colour printing, and a little of this is most of what makes
the look read as printed rather than filtered. Shown cropped, because a couple
of pixels of drift is invisible at page width.

![plate_drift](images/plate_drift.jpg)

### `contrast`
Default **0**. A pre-grade applied *before* separation, so it changes which inks
get called for rather than just adjusting the final picture. `brightness` works
the same way.

![contrast](images/contrast.jpg)

### `offset_angles`
Default **60**. The screen-angle step between successive inks. Real presses
offset their plates like this so the screens do not stack up into a moire, and
setting it to 0 shows you exactly why they bother.

![offset_angles](images/offset_angles.jpg)

### `rotate`
Default **0**. Rotates the whole screen set at once, keeping the relative angles
between the inks intact.

![rotate](images/rotate.jpg)

---

## `plate_render` and `tint_quantize`

These two are what separate a generic halftone filter from something that looks
like a comic actually printed in 1955.

### `plate_render`

![plate_render](images/plate_render.jpg)

`uniform` screens every plate the same way. `benday` makes each plate carry
several screens at once, the way a real Ben-Day plate did: light tints come out
as dots, deeper tints as a line or hatch sheet, and 100 percent as an unscreened
solid fill. Pair it with a tint quantize setting so the bands land on the
percentages a colourist could actually call for.

### `tint_quantize`

![tint_quantize](images/tint_quantize.jpg)

Snaps every plate to the tint percentages that were available to call for.
`25/50` is what both Craftint and the Silver Age acetate system offered: four
levels across three primaries, which is exactly where the classic 64-colour
comic palette comes from. `25/50/75` adds the call that arrived in the early
1980s. The result is flat stepped fields with no gradients, which is the single
biggest tell of the era.

---

## Randomisation

There are five separate ways to let the node surprise you, and they are all
driven by the **seed**. That matters more than it sounds: every random choice is
deterministic for a given seed, so a look you stumble into is never lost. Fix
the seed and it comes back exactly.

The usual way to work is to set the seed's `control_after_generate` to
**randomize**, let it roll until something is right, then set it back to
**fixed** to keep it.

### 1. Shuffle: a shortlist of presets

![shuffle](images/random_shuffle.jpg)

Click **🎲 Shuffle** in the presets section and the gallery switches from
"click to apply" to "click to select". Tick the presets you like, and one is
drawn from that shortlist on every run. **All** and **None** fill and empty the
list. Click Shuffle again to go back to applying presets normally.

The shortlist is sorted internally before the draw, so the result depends on
*which* presets are in it, not the order you happened to tick them. And the
shortlist is read before any preset is applied, so drawing a preset never wipes
out the list that chose it.

### 2. `pattern = random`

![random pattern](images/random_pattern.jpg)

The last entry in the pattern dropdown. Draws a fresh screen from the seed each
run. `solid` is deliberately excluded from the pool, because a flat ink field
turning up unannounced reads as a bug rather than variety.

### 3. Random per run: Inks, Paper, Ink pat.

![random inks](images/random_inks.jpg)

Three checkboxes under the palette swatches.

- **Inks** draws a whole ink set from the built-in palettes. Because it takes a
  real palette rather than arbitrary RGB, a rolled result is always
  print-plausible.
- **Paper** rolls the background. With **Inks** also ticked it takes the drawn
  palette's own paper colour, so the set stays coherent; on its own it picks
  from a list of paper tones.
- **Ink pat.** gives each ink its own screen, with roughly a 55 percent chance
  per ink of getting one rather than following the global pattern.

### 4. Per-ink dice

Each ink row has two small dice buttons, **c** and **p**, for colour and
pattern. These roll *only that ink*. Everything unmarked stays exactly where you
put it, which is the point: you can lock your yellow, magenta and black and roll
only the fourth ink, instead of re-rolling the whole set and losing the part you
liked.

### 5. Per-slider dice

Every slider has a dice icon beside it. Turn it on and that setting is rolled
inside a low/high range you set, on every run.

These are applied last, after any preset has been loaded, so a diced slider
overrides what the preset asked for. If you dice nothing, no draws are consumed
at all, which is what keeps a seed reproducing the same look after you add a
diced slider elsewhere.

---

## Regenerating these images

```bash
# everything, against your own image
python docs/generate_docs_images.py my_image.png

# one at a time while you tune
python docs/generate_docs_images.py my_image.png --only patterns

# list the image names
python docs/generate_docs_images.py --list
```

The script needs ComfyUI importable, because the engine asks
`comfy.model_management` which device to use. It passes `--cpu`, so it will not
fight a running ComfyUI for the GPU. Point `--comfy` at your ComfyUI root if it
is not in the default place.
