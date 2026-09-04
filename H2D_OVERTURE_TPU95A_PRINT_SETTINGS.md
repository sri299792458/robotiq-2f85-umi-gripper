# Bambu H2D — Overture TPU 95A finger profile

Use this existing material/process profile for [`V2_TPU95A_FINGER_PRINT_2.stl`](artifacts/print_v2_20260904/V2_TPU95A_FINGER_PRINT_2.stl). The V2 geometry still needs physical validation. This is regular Overture TPU 95A, not Overture High Speed TPU and not Bambu TPU for AMS.

## Filament preparation and feed

- Overture's forced-air specification is 70 °C for 7 hours. With the available AMS 2 Pro, use its maximum 65 °C for 12 hours as the lower-temperature equivalent.
- Put the spool on the AMS rollers but leave the filament end secured to the spool; do not insert this generic TPU into an AMS feeder funnel.
- On the H2D screen select `AMS Dry`, select the AMS 2 Pro, choose a manual/custom preset, set 65 °C and 12 h, close the lid, and start drying. Keep the AMS air intake and exhaust unobstructed.
- Use the H2D right hotend with the standard 0.4 mm nozzle.
- After drying, remove the spool and feed from the H2D external/bypass spool path. Do not route this filament through AMS 2 Pro.
- No active chamber heating. Keep the chamber below roughly 35 °C; crack the door if heat accumulates.

## Orientation

- The V2 print-pack STL is already broad-side down. For an assembly-orientation export, use **Lay on Face** on either large flat side of the finger.
- The six bays must face upward and the part must be 15.48 mm tall.
- The three M3 clearance holes must have vertical axes.
- Supports: off.
- Print one finger first for fit and stiffness validation; clone it only after that check.

## Filament profile

Start from `Generic TPU` and save a copy named `Overture TPU 95A — H2D 0.4`.

| Setting | Value |
|---|---:|
| Nozzle, first/other layers | 225 / 225 °C |
| Bed, first/other layers | 40 / 40 °C |
| Max volumetric speed | 3.2 mm³/s |
| Flow ratio | 1.00 |
| Retraction length | 0.4 mm |
| Cooling first two layers | 0% |
| Normal part cooling | 70% |
| Overhang/bridge cooling | 100% |
| Auxiliary fan | 0% |

If the extrusion looks intermittent or layers pull apart, use 230 °C. If the dry filament strings heavily, use 220 °C. Do not raise the volumetric limit until a separate flow test succeeds.

## Process profile

| Setting | Value |
|---|---:|
| Layer height / first layer | 0.20 / 0.20 mm |
| Wall generator | Arachne |
| Wall loops | 4 |
| Top / bottom shell layers | 5 / 5 |
| Sparse infill | 35% gyroid |
| First-layer speed | 20 mm/s |
| Outer wall | 25 mm/s |
| Inner wall | 35 mm/s |
| Sparse infill | 35 mm/s |
| Internal solid infill | 30 mm/s |
| Top surface | 25 mm/s |
| Bridges | 20 mm/s |
| Supports | Off |
| Ironing | Off |

- Enable `Avoid crossing walls`.
- Paint the seam onto the non-contact outer rail. Do not use random seam placement and keep the seam off the narrow TPU contact rail.
- Use a thin layer of liquid glue as a release layer on smooth or textured PEI. Do not use the SuperTack plate for this print.
- No brim should be needed with the broad-side-down orientation. Add a 3 mm outer brim only if the first prototype lifts.

## Before pressing Print

1. Confirm the slicer shows an approximately 74.019 × 23.990 mm footprint and 15.48 mm height.
2. Inspect the first-layer preview: all six bay openings must remain open.
3. Confirm support material is zero.
4. Confirm the right nozzle is assigned and the filament is coming from the external/bypass path.
5. Watch the first three layers for clean extrusion and adhesion.

After cooling, flex the plate and peel the part slowly. Clear the three Ø4.0 mm holes by hand if necessary; do not drive the bolts through undersized or string-filled holes.
