# Proyek Baby Mo

A 3D construction game for children aged 3–8, using the real Baby Ais and toy-vehicle models.
Ais asks the child to help build a playground for the kids at the masjid, one vehicle at a time:

| Job | Vehicle | What the child does | What it teaches |
|---|---|---|---|
| 1 | Excavator (Ekskavator) | Tap **Dig** 3 times; the arm digs, swings and drops dirt in the truck | What an excavator is for |
| 2 | Dump truck (Truk Jungkit) | Count the rocks, then **Tip**; the truck drives and tips its bed | Counting 2–5 |
| 3 | Bulldozer (Buldoser) | Tap **Push** until the three dirt bumps are flat | Cause and effect |
| 4 | Cement mixer (Truk Molen) | **Spin** the drum 3 times, then **Pour** the slab | Counting to 3 |
| 5 | Crane truck (Truk Derek) | Lift the block Ais names: red, yellow or blue | Colours |
| Finale | — | The playground appears; Ais cheers | Alhamdulillah, finishing a job |

Indonesian by default with an EN toggle; every line is spoken (browser text-to-speech).

## Run it locally
```bash
cd web && python3 -m http.server 8000      # then open http://localhost:8000
```
Add `?start=5` to jump to a job (testing).

## Rebuild the 3D assets
```bash
P=/path/to/blender-python      # Blender 5.2 python with bpy
$P scripts/p01_export_vehicles.py ../Vehicles/ConstructionVehicles.blend web/assets/vehicles_raw
$P scripts/p02_export_ais.py ../BabyAis/BabyAis_Hijab_Final.blend web/assets/characters/BabyAis_raw.glb
GT=gltf-transform ./scripts/p03_compress.sh      # npm i -g @gltf-transform/cli@4.1.1
```
- **Vehicles:** each vehicle exports with real hinge pivots named `PV_*`, which the game rotates: excavator swing, boom, stick and bucket; dump bed; bulldozer blade; crane swing, boom and hook; mixer drum; loader arm; forks; bin; ladder; every wheel.
- **Baby Ais:** exports with her deform bones and 12 animation clips: Idle, Walk, Run, Jump, Wave, Cheer, Clap, Point, ThumbsUp, LetsGo, Nod and Stand.
- **Size:** about 4.6 MB in total after meshopt compression.

## Test
`tests/playthrough.js` plays the whole game headless, tapping like a child, and saves screenshots:
```bash
node tests/playthrough.js "http://localhost:8000/index.html?shot=1" OUTDIR
```

## Notes
- The online copy is a claude.ai artifact. Its host doesn't serve `.glb`, so the models are published as `.glb.wasm`, and the game falls back to that name automatically.
- three.js r170 is vendored in `web/vendor` (MIT licence included), so the game needs no CDN and works offline.
