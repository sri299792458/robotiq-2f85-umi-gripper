# V2 gripper print pack - 2026-09-04

This pack contains the updated zero-gap design with reinforced washer seats and uncut M3x30 screws.

## Print quantities

| STL | Material | Copies | Build size X x Y x Z (mm) |
| --- | --- | ---: | --- |
| V2_PETG_LEFT_PRINT_1.stl | PETG | 1 | 26.0 x 26.7 x 40.5 |
| V2_PETG_RIGHT_PRINT_1.stl | PETG | 1 | 26.0 x 26.7 x 40.5 |
| V2_TPU95A_FINGER_PRINT_2.stl | TPU 95A | 2 | 74.019 x 23.990 x 15.48 |

Four physical parts total. The TPU STL contains one finger; duplicate it once in the slicer.

## Slicer setup

- Import as millimeters at 100% scale. All STLs are already oriented for printing.
- PETG: Robotiq mating face down; finished build height 40.5 mm. Retain this orientation instead of laying the adapter on a cheek face.
- TPU: broad side down; six bays open upward; M3 hole axes vertical; finished build height 15.48 mm. Supports off for TPU.
- Put PETG and TPU on separate plates and use the material/process profiles from the previous print.
- This pack contains geometry, not printer-specific sliced G-code.

## Assembly notes

- Print both updated TPU fingers: the contact-side root hole moved, so the preceding TPU parts do not match this revision.
- For the pair: six M3x30 socket-head screws, six M3 washers and six M3 hex nuts. Retain the existing Robotiq mounting hardware.
- Washer seats are 7.5 mm diameter. Reference washer dimensions are provisionally 7 mm OD x 0.5 mm thick; check the actual kit washers fit freely before tightening.
- Nominal closure: bare TPU rails touch; PETG adapters retain a 1 mm gap. Tape thickness is ignored as requested.
- Screw ends project about 4.1 mm past the PETG. No screw cutting is required.

The meshes have been checked for watertightness, connected solids, dimensions and orientation. V2 remains a prototype awaiting physical fit and low-force closure checks; the CAD mechanism check covered the closed configuration.
