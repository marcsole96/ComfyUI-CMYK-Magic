"""Explanations shown in the panel's help strip.

The node models a real printing process, so most controls need a sentence of
context to be usable. Keys are widget names, pattern ids, option values and
panel concepts; the panel looks them up on hover.
"""

HELP = {
    # ------------------------------------------------------------- settings
    "preset": "A complete look: pattern, all sliders, ink set, paper and print "
              "behaviour. Loading one fills every control, then stays selected "
              "until you change something.",
    "pattern": "The screen each ink plate is printed through. Dots are the "
               "classic halftone; lines and waves are hatching; solid prints "
               "flat ink with no screen at all.",
    "scale": "Size of the screen pattern. ~60 is fine print, 150+ gives bold "
             "poster dots, 300+ is pop-art. Scales with image size, so previews "
             "and full renders match.",
    "roughness": "Distresses the screen: ragged ink edges and wander, without "
                 "changing how much ink is laid down. 0 is a clean press, 40+ "
                 "is worn analogue.",
    "brightness": "Lightens or darkens the image before it is separated into "
                  "inks. Applied first, so it changes which tints the solver "
                  "calls for.",
    "contrast": "Pushes tones apart before separation. Raising it drives areas "
                "toward solid ink and bare paper, which is how comic art holds "
                "up on newsprint.",
    "ink_multiply": "How the inks stack. 0 = opaque paint that hides what is "
                    "under it, 100 = pure multiply like transparent ink. "
                    "Between the two is the half-opaque mix real inks have.",
    "ink_fade": "Worn, patchy ink: coarse faded areas plus fine paper tooth "
                "eating into the coverage. Simulates dry pigment on rough "
                "stock.",
    "dot_gain": "Ink spreading on absorbent paper, so a called tint prints "
                "heavier than it was drawn. 0 is a calibrated press (20% inks "
                "exactly 20%); 100 grows 20% to ~36%, the newsprint figure.",
    "plate_drift": "Misregistration, how far each plate slips out of "
                   "alignment, in pixels. The off-register colour fringing of "
                   "fast letterpress printing.",
    "offset_angles": "Degrees between each ink's screen. 30-60 gives the "
                     "classic rosette; 6-12 makes every ink hatch in the same "
                     "direction like a hand-pulled print; 0 puts them all on "
                     "the same angle, as cheap 1970s cameras did.",
    "rotate": "Rotates the whole set of screens together. With line or wave "
              "patterns this sets the direction the strokes run.",
    "plate_render": "Whether one plate carries a single screen or several at "
                    "once, chosen by tint level.",
    "tint_quantize": "Restricts every plate to the tint percentages a colourist "
                     "could actually call for, giving flat stepped colour "
                     "fields instead of smooth gradients.",
    "seed": "Drives every random choice: distress, misregistration and any "
            "diced setting. The same seed always reproduces the same result.",

    # -------------------------------------------------------- option values
    "plate_render:uniform": "One screen per plate at every tint level. This is "
                            "how Silver Age comics worked, the darker tints "
                            "come from the same dot screen printed heavier.",
    "plate_render:benday": "One plate carries several screens at once, masked "
                           "by tint level: light tints as dots, deep tints as a "
                           "line sheet, full strength as unscreened solid. The "
                           "Craftint / Golden Age method.",
    "tint_quantize:off": "Continuous coverage, smooth gradients, like modern "
                         "printing.",
    "tint_quantize:25/50": "The three calls Craftint and the Silver Age acetate "
                           "system offered: 25%, 50% and solid. Four levels "
                           "across three primaries is the famous 64-colour "
                           "comic palette.",
    "tint_quantize:25/50/75": "The three classic calls plus the 75% tint that "
                              "arrived in the early 1980s.",
    "tint_quantize:20/50": "An earlier approximation of the comic tint calls.",
    "tint_quantize:10/20/50/70": "A finer stepped set, more levels than any "
                                 "real comic press offered, but useful.",

    # ------------------------------------------------------------- patterns
    "pat:print_dots": "Euclidean halftone dots: ink grows as circles to 50%, "
                      "then the paper becomes circles, round holes in ink. "
                      "What a real contact screen does.",
    "pat:negative_dots": "The dot screen inverted: holes of ink in paper.",
    "pat:elliptical": "Chain dot. The elliptical dots touch along their long "
                      "axis first, so mid tones link into chains rather than "
                      "every dot joining at once, presses adopted it to avoid "
                      "the visible jump in tone at 50%.",
    "pat:square_dots": "Square dots that mesh into a checkerboard at 50%. "
                       "Coarse and mechanical.",
    "pat:bayer": "8x8 ordered dither, the threshold map early computers used "
                 "to fake greys from pure black and white. Thresholded hard, "
                 "so it stays crisp.",
    "pat:mezzotint": "Stochastic grain with no lattice at all, like an aquatint "
                     "ground. Never moirés against another plate.",
    "pat:concentric": "Rings centred on the frame.",
    "pat:spiral": "One continuous spiral, the ring screen with its radius "
                  "advanced a pitch per turn, so the line never closes.",
    "pat:lines": "Straight parallel line screen. Craftint printed its 50% tint "
                 "this way.",
    "pat:broken_lines": "Line screen chopped into stitch-like dashes, as a dry "
                        "brush skips.",
    "pat:cross_lines": "Two crossed line screens, denser hatching for shadow.",
    "pat:waves": "Rows that curve as continuous contours, bending into whorls "
                 "like a fingerprint.",
    "pat:broken_waves": "Curving rows broken into dashes: continuous in the "
                        "darks, thinning to ticks in the lights.",
    "pat:cross_waves": "Two wave screens crossed for a woven texture.",
    "pat:fan_dots": "Dots on arcs radiating from a point below the frame.",
    "pat:negative_fan": "The fan screen inverted.",
    "pat:solid": "No screen at all, flat ink fields. Keeps type and line art "
                 "sharp, and is how 100% areas were actually printed.",
    "pat:random": "Picks a fresh pattern from the seed on every run.",

    # ------------------------------------------------------------- concepts
    "color_match": "Solves per pixel for the amount of each ink that best "
                   "reproduces your image. Swap an ink and everything "
                   "re-separates around it.",
    "tint": "Gradient-map mode: each ink is placed at its own darkness across "
            "shadows to highlights, with the paper as the ink-free point. Two "
            "inks give a duotone.",
    "background": "The paper the inks print on. Set it dark for a shirt or a "
                  "night press; the separation accounts for it.",
    "opaque_bottom": "Forces the first ink to print opaque instead of "
                     "transparent, a solid base coat, the way white is laid "
                     "down first on dark stock.",
    "palette": "Swaps the whole ink set and paper for a ready-made scheme: real "
               "process sets, riso pairs, triads and duotones.",
    "palette_dice": "Applies a random palette right now.",
    "rnd_palette": "Draw a different ink palette on every run, from the seed.",
    "rnd_background": "Draw a different paper stock on every run.",
    "rnd_ink_patterns": "Give the inks random per-ink patterns on every run.",
    "adv_toggle": "Show each ink's screen angle, line frequency and solid-only "
                  "flag, the fields presets set that are otherwise invisible.",
    "ink_color": "This ink's colour. Order matters: the top ink prints first, "
                 "underneath the others.",
    "ink_pattern": "Give this one ink its own screen, for mixed-pattern looks: "
                   "e.g. black in cross-lines under orange waves.",
    "ink_angle": "This plate's absolute screen angle, overriding the automatic "
                 "spacing. Authentic letterpress: Y 75, M 45, C 105, K 45.",
    "ink_freq": "Line frequency for this plate only. Below 1 is coarser: "
                "newsprint ran the heavy inks coarser so they would not blob.",
    "ink_solid_only": "This ink never prints a tint, only nothing or full "
                      "strength. DC left yellow tints out until 1969, which is "
                      "why their faces are flat pink.",
    "ink_rnd_color": "Re-roll only this ink's colour each run, leaving the "
                     "others fixed.",
    "ink_rnd_pattern": "Re-roll only this ink's pattern each run.",
    "ink_eye": "Turn this ink off without deleting it.",
    "ink_move": "Reorder the print run. The first ink prints first, at the "
                "bottom of the stack.",
    "ink_delete": "Remove this ink.",
    "add_ink": "Add another ink to the press, up to eight.",
    "auto_sort": "Reorder light inks first and dark inks last, the usual print "
                 "order.",
    "shuffle": "Pick from a shortlist of presets: tick the ones you like, and "
               "one is drawn on every run. Driven by the seed, so any result "
               "can be reproduced by fixing it. Untick Shuffle to go back to "
               "clicking a preset to apply it.",
    "shuffle_pick": "Click to add or remove this preset from the shuffle "
                    "shortlist.",
    "shuffle_all": "Put every preset in the shortlist.",
    "shuffle_none": "Empty the shortlist.",
    "dice": "Randomize this setting on every run, within the range you set. "
            "Driven by the seed, so any result can be reproduced.",
    "dice_range": "Low and high bounds for the roll.",
    "preview": "Rendered by the real engine on this node's last input, so it "
               "matches what the node will output. Falls back to a test card "
               "before the node has run.",
    "default": "Hover any control for what it does.",
}
