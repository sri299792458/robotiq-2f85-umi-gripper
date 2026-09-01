# Two-part finger technical summary

This document describes the current handed PETG adapter and identical TPU 95A soft-gripper body. For the repository overview and download links, see [`README.md`](README.md).

## Per-finger construction

- 1 × handed PETG adapter
- 1 × identical TPU 95A finger
- 1 × M5 × 0.8 × 12 mm socket-head cap screw for the Robotiq fingertip interface
- 3 × transverse M3 fasteners joining the PETG cheeks to the TPU tongue

Print one LEFT PETG adapter, one RIGHT PETG adapter, and two copies of the TPU finger.

## Current dimensions

- PETG adapter envelope: 22.8 × 40.5 × 27.2 mm
- Root-down PETG print envelope: 22.8 × 27.2 × 40.5 mm
- TPU finger envelope: 15.48 × 74.019 × 23.990 mm
- PETG tongue pocket: 15.88 mm
- TPU thickness: 15.48 mm
- Nominal pocket clearance: 0.20 mm per side
- Installed M3 centers `(Y,Z)`: `(13,2.25)`, `(13,20.25)`, `(34,20.25)` mm
- PETG M3 through-holes: Ø3.6 mm
- TPU M3 clearances: Ø4.0 mm
- M3 head recesses: Ø6.5 × 2.4 mm
- Captive-nut pockets: 6.3 mm across flats × 2.5 mm deep

## Robotiq interface

The removable-fingertip attachment retains the OEM-derived Ø5.3 mm M5 shank clearance and 4 mm shoulder. A Ø9.2 mm head/tool counterbore extends another 6 mm. With the measured 4.9 mm socket-head height, the bolt head ends at Y=8.9 mm and has 1.1 mm clearance before the TPU seating face at Y=10 mm.

Two Ø2 × 2.5 mm indexing sockets remain at X=±4.5 mm. The TPU has no M5-axis groove or relief.

## Finger architecture and closure

The TPU exterior is a direct 0.600-scale UMI soft-gripper section. Its three-hole triangle, exterior rails, and contact rail move as one architecture. Six larger through-bays replace groups of the original UMI cells.

The bare TPU rails retain a 1.5 mm total gap at mechanical closure, intended for approximately 0.75 mm grip tape on each contact face. The final Fusion checks report zero positive-volume intersection between PETG and TPU and between the opposed left/right parts.

## Production artifacts

- `artifacts/Robotiq_2F85_UMI_Handed.f3d`
- `artifacts/Robotiq_2F85_UMI_Handed.step`
- `artifacts/2F85_PETG_Adapter_LEFT_M3_ROOT_DOWN_PRINT_READY.stl`
- `artifacts/2F85_PETG_Adapter_RIGHT_M3_ROOT_DOWN_PRINT_READY.stl`
- `artifacts/2F85_TPU95A_Finger_M3_PRINT_2.stl`

This remains an unvalidated prototype. Begin with low-force fit and closure testing.
