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
