"""Preset library for CMYK Magic.

Each preset is a full parameter set plus an ink_config. In the UI, picking a
preset loads its values into the node's widgets (then flips back to "Custom"
so everything stays tweakable); headless, a selected preset name overrides the
widgets directly.
"""


def _i(color, pattern=None, pos=None, angle=None, freq=None, solid_only=False):
    d = {"color": color, "on": True}
    if solid_only:
        d["solid_only"] = True
    if freq is not None:
        d["freq"] = freq
    if pattern:
        d["pattern"] = pattern
    if pos is not None:
        d["pos"] = pos
    if angle is not None:
        d["angle"] = angle
    return d


def _p(inks, pattern="print_dots", scale=60.0, roughness=20.0, brightness=0.0,
       contrast=0.0, ink_multiply=60.0, ink_fade=10.0, plate_drift=1.5,
       offset_angles=60.0, rotate=0.0, mode="color_match",
       background="#f4efe6", opaque_bottom=False, tint_quantize="off",
       dot_gain=35.0, plate_render="uniform"):
    return {
        "pattern": pattern, "scale": scale, "roughness": roughness,
        "brightness": brightness, "contrast": contrast,
        "ink_multiply": ink_multiply, "ink_fade": ink_fade,
        "plate_drift": plate_drift, "offset_angles": offset_angles,
        "rotate": rotate, "tint_quantize": tint_quantize, "dot_gain": dot_gain,
        "plate_render": plate_render,
        "ink_config": {"mode": mode, "background": background,
                       "opaque_bottom": opaque_bottom, "inks": list(inks)},
    }


MAGIC_PRESETS = {
    # ------------------------------------------------------------ poster inks
    # Hatch-style presets keep offset_angles small: all plates stroke in
    # nearly the same direction, like hand-pulled prints. Wide offsets turn
    # hatching into a woven tangle (keep those for dot rosettes only).
    "Vintage Poster": _p(
        [_i("#d96f3a"), _i("#2e7f78"), _i("#22201f")],
        pattern="broken_waves", scale=150, roughness=40, ink_fade=20,
        plate_drift=2.0, ink_multiply=65, background="#ece3cd", contrast=10,
        offset_angles=8, rotate=-15, dot_gain=45),
    "Rose Matinee": _p(
        [_i("#b95d7e"), _i("#8a3d4e"), _i("#2f3a33")],
        pattern="waves", scale=95, roughness=30, ink_fade=12,
        ink_multiply=75, background="#eee3c0", offset_angles=6, rotate=-30),
    "Surf Poster": _p(
        [_i("#3a7bd0"), _i("#d05f28"), _i("#26301f")],
        pattern="broken_waves", scale=110, roughness=30, ink_fade=15,
        ink_multiply=90, background="#f4f1ea", offset_angles=45, dot_gain=45),
    "Poster Shop": _p(
        [_i("#c0392b"), _i("#2960a5"), _i("#8a5a9c"), _i("#26221f")],
        scale=70, roughness=25, ink_fade=15, plate_drift=2.5,
        background="#eae4d6"),
    "Free of Charge": _p(
        [_i("#2f72c4"), _i("#e2622b")],
        scale=80, roughness=15, ink_multiply=70, ink_fade=8,
        background="#f2efe8"),
    "Strange Process": _p(
        [_i("#4b3a8f"), _i("#3f9f74"), _i("#e0563a"), _i("#262233")],
        pattern="cross_waves", scale=95, roughness=30, ink_fade=18,
        plate_drift=3.0, background="#ece7dc"),
    # ------------------------------------------------------------- CMYK press
    # Authentic letterpress screen angles (Y 90°, M 75°, C 105°, K 45°) and
    # Ben-Day tint quantization: plates only existed at 0/20/50/100%, so
    # colors come from the classic 64-color comic palette.
    "Comic CMYK": _p(
        [_i("#f0d92e", angle=90), _i("#dd3a86", angle=75),
         _i("#1899d6", angle=105), _i("#22222a", angle=45)],
        scale=55, roughness=22, plate_drift=3.5, ink_fade=12,
        ink_multiply=85, background="#efe9da", tint_quantize="25/50",
        dot_gain=55),
    "Golden Age Comic": _p(
        [_i("#e8cf35", angle=75, freq=0.7), _i("#d44480", angle=45),
         _i("#2b8fc4", angle=105), _i("#26241f", angle=45, freq=1.2)],
        scale=95, roughness=40, plate_drift=6.0, ink_fade=26,
        ink_multiply=85, background="#e8dcc0", tint_quantize="25/50",
        plate_render="benday", contrast=10, dot_gain=70),
    # --- The three real comic-book eras -----------------------------------
    # Craftint Multicolor (c.1938-1955). The colourist had exactly three
    # calls per primary: 25% square-grid dots, 50% diagonal LINES, 100% solid
    # painted in, 4 levels ^ 3 primaries = the 64-colour comic palette. Dots
    # and lines sat in perfect register on one pre-printed board, which is
    # what plate_render "benday" reproduces. Screen angles per the 1948
    # Graphic Arts Production Yearbook: Yellow 75, Magenta 45, Cyan 105.
    "Craftint Golden Age": _p(
        [_i("#f0d92e", angle=75, freq=0.8), _i("#dd3a86", angle=45),
         _i("#1899d6", angle=105), _i("#22222a", angle=45, freq=1.2)],
        scale=75, roughness=28, plate_drift=4.0, ink_fade=15,
        ink_multiply=85, background="#e9e0c6", tint_quantize="25/50",
        plate_render="benday", dot_gain=55),
    # DC until 1969 left yellow tints out entirely, yellow could only print
    # solid, halving the palette to 32 colours and making every caucasian
    # face flat pale magenta (R2) instead of Marvel's Y2R2.
    "DC Golden Age": _p(
        [_i("#f0d92e", angle=75, solid_only=True), _i("#dd3a86", angle=45),
         _i("#1899d6", angle=105), _i("#22222a", angle=45, freq=1.2)],
        scale=75, roughness=28, plate_drift=4.5, ink_fade=18,
        ink_multiply=85, background="#e9dfc2", tint_quantize="25/50",
        plate_render="benday", dot_gain=55),
    # Silver Age acetate method (Marvel 1954, DC 1956, into the 80s). Same
    # three calls, but the 50% is no longer lines: one contact halftone screen
    # was shot twice at different exposures, so the 25% positive dots and the
    # 50% "negative dots" come from the same screen in the same position,
    # exactly what the Euclidean dot function does across 50%.
    "Silver Age": _p(
        [_i("#f5d93a", angle=90, freq=0.85), _i("#e03a80", angle=75),
         _i("#00a2dd", angle=105), _i("#221f22", angle=45, freq=1.2)],
        scale=62, roughness=18, plate_drift=3.0, ink_fade=10,
        ink_multiply=88, background="#eee6d2", tint_quantize="25/50",
        dot_gain=60),
    # Mid-70s the engravers switched to a cheaper camera and screened every
    # colour at the SAME angle, no rosette, visibly coarser colour.
    "Bronze Age 70s": _p(
        [_i("#f2d54a", freq=0.85), _i("#dc4a80"), _i("#2f92c8"), _i("#26232a")],
        scale=70, roughness=30, plate_drift=5.0, ink_fade=22,
        ink_multiply=85, background="#e4d8ba", tint_quantize="25/50",
        offset_angles=0, rotate=45, dot_gain=70),
    # One plate, several screens: light tints print as dots, deep tints as a
    # line sheet, 100% as an unscreened solid fill, the engraver's multi-mask
    # plate. Yellow runs coarse (freq 0.6) because fine yellow tints blurred
    # away on newsprint, and the heavy inks run coarser than the black plate.
    "Ben-Day Workshop": _p(
        [_i("#f0d92e", angle=90, freq=0.6), _i("#dd3a86", angle=75, freq=0.8),
         _i("#1899d6", angle=105, freq=0.8), _i("#22222a", angle=45, freq=1.2)],
        scale=70, roughness=25, plate_drift=4.0, ink_fade=15,
        ink_multiply=85, background="#ece2c8", tint_quantize="10/20/50/70",
        plate_render="benday", dot_gain=60),
    "CMYK '74": _p(
        [_i("#d4b13e", freq=0.85), _i("#c4547e"), _i("#4aa3c4"), _i("#33302e")],
        pattern="elliptical", scale=65, roughness=30, plate_drift=3.0,
        ink_fade=25, ink_multiply=80, background="#ece4d2", offset_angles=30,
        dot_gain=50),
    # Sunday colour supplements were still true Ben-Day well after the comic
    # books had moved to Craftint: a wider range of tint values than the three
    # calls, laid down by hand, printed huge and heavy on cheap stock.
    "Sunday Funnies": _p(
        [_i("#f2d640", angle=75, freq=0.7), _i("#e04a86", angle=45),
         _i("#2f97cc", angle=105), _i("#2a2622", angle=45, freq=1.2)],
        scale=105, roughness=32, plate_drift=6.5, ink_fade=24,
        ink_multiply=85, background="#e9dcc0", tint_quantize="10/20/50/70",
        plate_render="benday", contrast=8, dot_gain=70),
    # The elliptical screen commercial presses moved to, run clean and fine.
    "Chain Dot Press": _p(
        [_i("#f2d93c", freq=0.9), _i("#e0397f"), _i("#1b9ad4"), _i("#232227")],
        pattern="elliptical", scale=55, roughness=12, plate_drift=1.0,
        ink_fade=8, ink_multiply=88, background="#f4f1e8", offset_angles=30,
        dot_gain=40),
    # ------------------------------------------------------------- warm tints
    "Charles Brown": _p(
        [_i("#3b2f1e"), _i("#d4a53f")],
        mode="tint", scale=60, roughness=20, ink_multiply=75, ink_fade=12,
        background="#efe6cf"),
    "Desert Etching": _p(
        [_i("#2b2622"), _i("#c07a3d")],
        mode="tint", pattern="broken_lines", scale=95, roughness=35,
        ink_fade=20, background="#e8dcc4", offset_angles=10, rotate=-25),
    "Cigar Club": _p(
        [_i("#33686b"), _i("#b56a35"), _i("#2b241d")],
        pattern="lines", scale=80, roughness=30, ink_fade=18,
        ink_multiply=70, background="#e6d9bd", offset_angles=12, rotate=-20, dot_gain=25),
    "Folk Festival": _p(
        [_i("#c9a35c"), _i("#a5583a"), _i("#3f6f66"), _i("#302a22")],
        scale=75, roughness=28, ink_fade=22, ink_multiply=70,
        background="#e9e0cc"),
    "Early Days": _p(
        [_i("#6f8f86"), _i("#b49668"), _i("#4a3c30")],
        scale=70, roughness=35, ink_fade=30, ink_multiply=65,
        background="#e9e2d2"),
    # ------------------------------------------------------------ bold colors
    "Jungle Tour": _p(
        [_i("#d55a9c"), _i("#3f8f5f"), _i("#2c6f76"), _i("#241f28")],
        scale=65, roughness=20, ink_fade=12, background="#ede8dc"),
    "Jewel Thief": _p(
        [_i("#d9b23c"), _i("#d84f7e"), _i("#2e8f8a"), _i("#2a2430")],
        pattern="waves", scale=85, roughness=25, ink_fade=15,
        background="#ece6d8", offset_angles=10, rotate=-20),
    "Orange Crate": _p(
        [_i("#f0ece2"), _i("#d9975c"), _i("#cf5f2a")],
        pattern="print_dots", scale=260, roughness=35, ink_fade=20,
        ink_multiply=30, background="#151312", opaque_bottom=True,
        offset_angles=30, dot_gain=25),
    "Gallery Stipple": _p(
        [_i("#5f7388"), _i("#7e2f26"), _i("#c97a3f")],
        pattern="mezzotint", scale=150, roughness=25, ink_fade=15,
        ink_multiply=70, background="#e7d9b8", offset_angles=60,
        plate_drift=3.0, dot_gain=35),
    "Glam T-Shirt": _p(
        [_i("#f2ece2"), _i("#d968a8"), _i("#4fb3a5")],
        scale=90, roughness=20, ink_fade=10, background="#141216",
        opaque_bottom=True, ink_multiply=45),
    # ------------------------------------------------------------- intaglio
    # Mezzotint and aquatint have no lattice: the plate is roughened all over
    # and the tone comes from how much of that grain holds ink.
    "Mezzotint Plate": _p(
        [_i("#141416"), _i("#7a7468")],
        mode="tint", pattern="mezzotint", scale=70, roughness=20,
        ink_multiply=85, ink_fade=10, background="#e8e2d2", dot_gain=45,
        contrast=10),
    "Aquatint Sepia": _p(
        [_i("#2e2216"), _i("#b08a52")],
        mode="tint", pattern="mezzotint", scale=95, roughness=25,
        ink_multiply=80, ink_fade=15, background="#efe4cc", dot_gain=40),
    # ------------------------------------------------------------- graphic
    "Op Art Record": _p(
        [_i("#c62828"), _i("#17171b")],
        pattern="concentric", scale=60, roughness=8, plate_drift=0.0,
        ink_fade=6, ink_multiply=90, background="#f2efe6", contrast=20,
        offset_angles=0, dot_gain=30),
    "Hypnotic Spiral": _p(
        [_i("#e8b13a"), _i("#1d1a24")],
        pattern="spiral", scale=70, roughness=10, plate_drift=0.0,
        ink_fade=8, ink_multiply=90, background="#f2ece0", contrast=15,
        offset_angles=0, dot_gain=30),
    "Pixel Press": _p(
        [_i("#e8402f"), _i("#1c1c22")],
        pattern="square_dots", scale=150, roughness=5, plate_drift=1.0,
        ink_fade=5, ink_multiply=90, background="#efe9dc", contrast=12,
        offset_angles=45, dot_gain=30),
    # Ordered dither: greys faked from two flat colours, thresholded hard.
    "8-Bit Dither": _p(
        [_i("#0f380f"), _i("#8bac0f")],
        mode="tint", pattern="bayer", scale=40, roughness=0,
        ink_multiply=95, ink_fade=0, plate_drift=0.0, background="#9bbc0f",
        contrast=15, dot_gain=0),
    "Blueprint": _p(
        [_i("#0d2f6b")],
        mode="tint", pattern="lines", scale=90, roughness=22, ink_fade=12,
        ink_multiply=85, background="#dfe6ee", offset_angles=8, rotate=-20,
        dot_gain=30),
    # -------------------------------------------------------------- mono/etch
    "Newspaper": _p(
        [_i("#2a2a2a")],
        mode="tint", scale=42, roughness=12, ink_multiply=80, ink_fade=8,
        background="#e9e5da", dot_gain=45),
    "One-Pass White": _p(
        [_i("#efeae0")],
        mode="tint", scale=60, roughness=25, ink_multiply=30, ink_fade=12,
        background="#17151a", dot_gain=25),
    "Crosshatch": _p(
        # Four stepped grays through the color-match solver: shadows stack
        # multiple line directions, mids stay open, tint hats would drive
        # coverage to 1 and merge the lines into murk.
        [_i("#26231f", pattern="lines"),
         _i("#37332d", pattern="lines"),
         _i("#4c463d", pattern="lines"),
         _i("#645c50", pattern="lines")],
        mode="color_match", pattern="lines", scale=75, roughness=25,
        offset_angles=45, ink_multiply=85, ink_fade=10,
        background="#ece5d4", dot_gain=25),
    # ---------------------------------------------------------- mixed pattern
    "Hand Toned": _p(
        [_i("#dfae3c", pattern="print_dots"),
         _i("#c15b38", pattern="waves"),
         _i("#232025", pattern="cross_lines")],
        scale=80, roughness=30, ink_fade=18, ink_multiply=70,
        background="#ebe2cd"),
}


# One line per preset, shown as the gallery caption's tooltip and in the
# panel's help strip.
PRESET_DESC = {
    "Vintage Poster": "Orange, teal and black broken waves on aged stock, the "
                      "hand-pulled travel poster look.",
    "Rose Matinee": "Fine parallel wave hatching in dusty pinks on cream.",
    "Surf Poster": "Crossed broken waves, bright blue and orange on near-white.",
    "Poster Shop": "Four bold poster inks, clean dots, light misregistration.",
    "Free of Charge": "Two-ink blue and orange riso on white, cheap and cheerful.",
    "Strange Process": "Four odd inks through crossed waves; unstable, psychedelic.",
    "Comic CMYK": "Process CMYK with letterpress angles and Ben-Day tint calls.",
    "Golden Age Comic": "Coarse aged newsprint comic: big dots, heavy drift, warm paper.",
    "Craftint Golden Age": "The 1938-55 method: 25% dots, 50% diagonal LINES, "
                           "100% solid, angles Y75/M45/C105.",
    "DC Golden Age": "Craftint with no yellow tints, as DC printed until 1969: "
                     "flat pale pink flesh, 32 colours.",
    "Silver Age": "The acetate method: no lines, the 50% tint is round negative "
                  "dots from the same screen.",
    "Bronze Age 70s": "Every plate screened at the same angle, as cheap 70s "
                      "cameras did. No rosette, coarser colour.",
    "Ben-Day Workshop": "One plate carrying several screens at once, coarse "
                        "yellow, how engravers actually worked.",
    "CMYK '74": "Faded seventies process colour, wide angles, worn ink.",
    "Charles Brown": "Warm brown and gold duotone gradient map on cream.",
    "Desert Etching": "Broken line hatching, ink and burnt orange, sun-bleached.",
    "Cigar Club": "Teal, tobacco and near-black in near-parallel line hatching.",
    "Folk Festival": "Four muted earth inks, soft dots, worn paper.",
    "Early Days": "Sage, wheat and brown, heavily faded, old field-guide print.",
    "Jungle Tour": "Hot pink and greens on warm paper, clean dots.",
    "Jewel Thief": "Gold, rose and teal in flowing wave hatching.",
    "Orange Crate": "Giant opaque pop dots, white base coat on near-black stock.",
    "Gallery Stipple": "Organic coarse stipple in slate, rust and ochre.",
    "Glam T-Shirt": "Opaque white base then pink and mint, screen print on black.",
    "Newspaper": "Single black ink, fine screen, grey newsprint.",
    "One-Pass White": "One near-white ink on dark stock, a single light pass.",
    "Crosshatch": "Four stepped greys, all line screens at 45-degree steps.",
    "Hand Toned": "Mixed patterns per ink: dots, waves and cross-lines together.",
    "Sunday Funnies": "Ben-Day Sunday supplement: huge coarse tints, many tint "
                      "values, heavy off-register on cheap stock.",
    "Chain Dot Press": "The elliptical screen commercial presses moved to, run "
                       "clean and fine on white stock.",
    "Mezzotint Plate": "Lattice-free stochastic grain, rich blacks, a roughened "
                       "intaglio plate.",
    "Aquatint Sepia": "Aquatint grain in sepia and cream, soft and powdery.",
    "Op Art Record": "Concentric rings in red and black, sixties op-art sleeve.",
    "Hypnotic Spiral": "One continuous spiral in gold and near-black.",
    "Pixel Press": "Big square dots meshing to a checkerboard, blunt and "
                   "mechanical.",
    "8-Bit Dither": "Ordered dither in four shades of handheld green.",
    "Blueprint": "Single blue ink hatched in lines on pale drafting paper.",
}


# Ink palettes: background + ink colors only (applied to the current settings,
# or drawn at random per run when the Inks randomize flag is on). Built from
# complementary/triad color theory and real print ink schemes.
PALETTES = {
    "Process CMYK": {"background": "#f2efe8", "inks": ["#f0d92e", "#dd3a86", "#1899d6", "#22222a"]},
    "Warm Process '74": {"background": "#ece4d2", "inks": ["#d4b13e", "#c4547e", "#4aa3c4", "#33302e"]},
    "Riso Blue Orange": {"background": "#f4f1ea", "inks": ["#2f72c4", "#e2622b"]},
    "Riso Pink Teal": {"background": "#f2ede4", "inks": ["#e64578", "#2e8f8a"]},
    "Riso Green Violet": {"background": "#f1eee6", "inks": ["#3f9f74", "#6a4a9f"]},
    "Fluor Riso": {"background": "#f5f2ec", "inks": ["#ff4fa0", "#2560c9", "#1e1e26"]},
    "War Poster": {"background": "#e9ddc0", "inks": ["#b5382e", "#26221e"]},
    "Navy & Gold": {"background": "#ece5d2", "inks": ["#d4a53f", "#243a5e"]},
    "Coral Mint": {"background": "#f3ece0", "inks": ["#e8735a", "#66b29a", "#2c2a33"]},
    "Primary Triad": {"background": "#f0ece2", "inks": ["#e3b52e", "#d43a35", "#2960a5", "#232323"]},
    "Autumn Earth": {"background": "#e9dfc8", "inks": ["#c07a3d", "#7e5433", "#3f5a40", "#2b241d"]},
    "Sepia Duo": {"background": "#efe6cf", "inks": ["#d4a53f", "#3b2f1e"]},
    "Newsprint": {"background": "#e9e5da", "inks": ["#2a2a2a"]},
    "Cyanotype": {"background": "#e8edf2", "inks": ["#1d3f7a"]},
    "Pop Teal Orange": {"background": "#efe6d2", "inks": ["#2a9d8f", "#e76f51", "#1d1d24"]},
    "Berry Crush": {"background": "#f0e8dc", "inks": ["#d05f7e", "#8a2f52", "#2c2233"]},
    "Surf Trio": {"background": "#f4f1ea", "inks": ["#3a7bd0", "#d05f28", "#26301f"]},
    "Night Print": {"background": "#141216", "inks": ["#f2ece2", "#d968a8", "#4fb3a5"]},
}

# Paper stocks for randomizing the background on its own.
PAPER_TONES = [
    "#f4f1ea", "#f2efe8", "#efe6cf", "#ece4d2", "#e9ddc0", "#e6d9bd",
    "#e9e5da", "#f2ede4", "#e8dcc4", "#e8edf2", "#d9cba8", "#17151a", "#141216",
]
