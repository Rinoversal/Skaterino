# Skaterino

Measures a map against skate.'s real skater limits before you build it with ReSkate Studio, and
tells you what will and will not work: scale, drops that bail, faceted ramps, flickering
overlays, rails out of reach. Made while porting Tony Hawk's Pro Skater 2 levels to ReSkate;
works on any map you can get into Blender (THPS/THUG, Skater XL, Session, your own).

## Use

1. Install Blender 4.x or 5.x.
2. Get your map into a `.blend` or `.glb` in **metres, Z up** (Blender's default). Mesh objects
   are level geometry; Blender curve objects are grind rails.
3. Drag the file onto `skaterino.bat`, or run:

       blender --background --factory-startup --python skaterino.py -- "C:\path\map.blend" [--scale 0.9]

4. Read `map_skaterino.md` next to the map. `--scale` tests a rescale without touching the file.

## What it checks

| Check | Against | Why |
|---|---|---|
| Stair risers, ledge heights | real world 0.15-0.19 m / 0.3-0.5 m | THPS/THUG/SXL maps are often 10-40% oversized; stairs give the scale away |
| Every edge drop | bail speed 15 m/s, about an 11 m fall | THPS lets you survive any drop; skate. does not |
| Ledges | ollie 1.575 m | what you can and cannot pop onto |
| Banked faces and their creases | grind-edge finder at 30 degrees | low-poly quarter pipes ride bumpy and sprout fake grind ledges |
| Coplanar faces within 1 cm | depth buffer | painted shadows and markings z-fight in a modern engine |
| Rail heights | ollie + 0.3 m | rails you cannot reach from flat |
| Walkable faces above the survivable drop | | rooftops that are a dare, not a line |

## How it works, in plain terms

1. **It knows what the skater can do.** `skate_limits.json` holds the numbers that matter. The
   skater is 1.81 m tall. The highest ollie is 1.575 m. Landing faster than 15 m/s downwards is a
   bail. Any crease sharper than 30 degrees is treated as a grind edge. These come out of the
   game's own physics tuning, so they are the real values and not guesses.
2. **You give it a map.** Drag a `.blend` or `.glb` onto `skaterino.bat`. Blender starts with no
   window, opens the map and runs the script. Meshes are the level. Curves are the rails.
3. **It welds the map into one piece.** Every object is merged into a single mesh so the checks
   can see the whole level at once. With `--scale` that copy is resized first, so you can ask
   "what if the map were 90% of this size?" while your file stays untouched.
4. **It measures.** Most checks work the same way: pick a spot, fire an invisible straight line
   from it, and see what the line hits and how far away that is.
   - **Scale.** It collects every upright face 12 to 25 cm tall and takes the most common height.
     That is nearly always a stair step. Real steps are 15 to 19 cm, so 22 cm steps mean the map
     is about 30% too big, and the report gives the `--scale` value that fixes it.
   - **Drops.** At every open edge of a flat floor it steps 30 cm out and measures straight down.
     Gravity turns the 15 m/s bail speed into a fall of about 11 m, so anything higher is a
     guaranteed bail. Falls of 6 to 11 m are listed as survivable but rough.
   - **Ledges.** Upright faces 25 to 70 cm tall are counted as ledges. Their most common height
     is a second scale clue alongside the stairs.
   - **Ramps.** It finds sloped faces and counts the folds between them. An old low-poly quarter
     pipe is a handful of flat panels. skate. rides over every fold, so it feels bumpy, and folds
     over 30 degrees become grind edges nobody intended. Too many folds gets a warning to
     subdivide and smooth.
   - **Flicker.** For each face it looks 1 cm in front and behind for another face lying flat
     against it. Old games painted shadows and road markings as a second layer on the floor. A
     modern engine cannot decide which layer is on top, so the two flicker.
   - **Rails.** For every point on every rail curve it measures down to the ground. Rails more
     than 30 cm above the highest ollie cannot be reached from flat and need a ramp, stairs or a
     drop-in.
   - **Rooftops.** It takes the low floors as ground level and counts every floor more than 11 m
     above that. THPS lets you jump off any roof. skate. does not.
5. **It writes the report.** Each check adds a line marked OK, WARN or INFO, with the fix in
   plain words. The lines go to `map_skaterino.md` to read and `map_skaterino.json` for other
   tools, both beside your map.

The point is to skip the loop of build, load the game, skate around, find a problem and go back
to Blender. The game never has to start.

## Example (THPS2 School II)

    - OK   Scale: stair risers are 0.16 m, real-world. Keep scale 1.00.
    - WARN Drops: 70 edges drop more than 11 m ... Fence them, add a ramp, or accept the bail.
    - WARN Overlays: 194 faces sit on another face within 1 cm; they will flicker (z-fight) ...
    - INFO Rails: 147 curves; median 1.15 m above ground; 33% of rail points are above ollie reach
    - INFO 627 walkable faces sit more than 11 m above ground level: rooftops ...

The full report is in `example_school2.md`.

## Where the numbers come from

`skate_limits.json`. The skate. values were dumped from the game's own tuning asset
(`gameplay/skatephysicstuning`) with ReSkate Studio's `reskate_cli ebx-values`; `dump_limits.bat`
re-dumps them if the game updates. Skater height is from Studio's `scaleref.glb`.

## Licence

GPL-3.0, like ReSkate.
