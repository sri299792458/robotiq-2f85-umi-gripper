# Robotiq 2F-85 UMI gripper

Prototype UMI-style soft gripper for the Robotiq 2F-85. Each jaw uses a rigid PETG adapter and a compliant TPU 95A gripper body based on the open UMI Fin-Ray-style architecture.

This is an independent experimental design. It is not supplied or endorsed by Robotiq and is not load-rated.

![Robotiq 2F-85 with the UMI-style soft gripper](artifacts/robotiq-2f85-umi-gripper.png)

## Final geometry

- PETG adapter: 22.8 × 40.5 × 27.2 mm
- TPU finger: 15.48 × 74.019 × 23.990 mm
- TPU slot: 15.88 mm, providing 0.20 mm nominal clearance per side
- Three transverse M3 axes at `(Y,Z) = (13,2.25), (13,20.25), (34,20.25)` mm
- Robotiq interface: Ø5.3 mm M5 clearance, 4 mm OEM-derived shoulder, Ø9.2 × 6 mm head/tool pocket, and two Ø2 × 2.5 mm indexing sockets
- Measured Ø8.5 × 4.9 mm M5 head has 1.1 mm axial clearance before the TPU seating face at Y=10 mm
- Bare TPU pair retains a 1.5 mm closing gap intended to be filled by approximately 0.75 mm grip tape per side

The TPU body is derived from a direct 0.600-scale section of the UMI soft gripper. The original UMI internal cells are grouped into six larger through-bays while retaining the two-rail compliant load path. The PETG carrier is redesigned around the Robotiq removable-fingertip interface.

## Print files

The final files are in [`artifacts/`](artifacts/):

- `2F85_PETG_Adapter_LEFT_M3_ROOT_DOWN_PRINT_READY.stl` — print one in PETG
- `2F85_PETG_Adapter_RIGHT_M3_ROOT_DOWN_PRINT_READY.stl` — print one in PETG
- `2F85_TPU95A_Finger_M3_PRINT_2.stl` — print two identical copies in TPU 95A
- `Skild_Inspired_2F85_Handed.f3d` — editable Fusion archive
- `Skild_Inspired_2F85_Handed.step` — neutral assembly CAD

The PETG STLs are already oriented with the Robotiq mating face on the build plate. Printing them on a cheek face creates an unsupported bridge across the TPU slot and should be avoided.

See [`H2D_OVERTURE_TPU95A_PRINT_SETTINGS.md`](H2D_OVERTURE_TPU95A_PRINT_SETTINGS.md) for the tested Bambu H2D / Overture TPU 95A preparation and slicer profile.

## Verification performed

- Both handed PETG and the TPU meshes are watertight with consistent winding.
- All three M3 circular and captive-hex pockets remain complete and enclosed.
- The measured M5-head keep-out intersects neither PETG nor TPU.
- PETG/TPU intersection is zero.
- Opposed PETG and TPU pairs have zero positive-volume intersection at closure.
- The final TPU export is byte-identical to the preceding accepted TPU; the last adapter trim did not alter the TPU part.

## Rebuilding

The Fusion generator and QA scripts are in [`scripts/`](scripts/). They expect Autodesk Fusion with its Python API and local reference-data paths documented in the scripts. Computer-vision utilities require the packages in [`requirements.txt`](requirements.txt).

The reconstruction log, measurements, corrections, and QA results are maintained in [`running_notes.md`](running_notes.md).

## Prototype warning

Perform a low-force fit and closure test before carrying a payload. Verify M5 seating, indexing-pin engagement, M3 hardware clearance, jaw collision, print tolerances, grip-tape thickness, and TPU stiffness on your physical gripper.
