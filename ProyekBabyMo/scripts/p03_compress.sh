#!/bin/bash
# Compress exported GLBs for the web: meshopt geometry + quantisation, keep node names (pivots), resample anims.
set -e
GT=${GT:-gltf-transform}
mkdir -p web/assets/vehicles
$GT optimize web/assets/characters/BabyAis_raw.glb web/assets/characters/BabyAis.glb --compress meshopt --texture-compress webp --simplify false --join false --flatten false --instance false --prune true 2>&1 | tail -1
for f in web/assets/vehicles_raw/*.glb; do
  $GT optimize "$f" "web/assets/vehicles/$(basename $f)" --compress meshopt --simplify false --join false --flatten false --instance false 2>&1 | tail -1
done
cp web/assets/vehicles_raw/vehicles.json web/assets/vehicles/
rm -rf web/assets/vehicles_raw web/assets/characters/BabyAis_raw.glb
du -sh web/assets/characters/BabyAis.glb web/assets/vehicles
