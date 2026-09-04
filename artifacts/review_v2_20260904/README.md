# V2 review: reinforced seats, zero bare-TPU gap, uncut M3x30 screws

This is a new review prototype built through Fusion MCP on 2026-09-04. The preceding production artifacts remain unchanged.

The user reported PETG cracking while tightening a root screw. Inspection of the preceding model found only 1.06 mm beneath each head recess and 0.96 mm beneath each nut pocket. The user requested nominal contact between the **bare TPU rails**, with tape thickness ignored, and confirmed that cutting/deburring screws is not available. V2 therefore uses unmodified M3x30 screws.

## Geometry

| Feature | V2 review |
|---|---:|
| Handed PETG adapter envelope, X/Y/Z | 26.0 / 40.5 / 26.7 mm |
| Root-down PETG print envelope | 26.0 / 26.7 / 40.5 mm |
| TPU envelope | 15.48 / 74.019 / 23.990 mm |
| TPU pocket | 15.88 mm, 0.20 mm nominal clearance per side |
| Washer seats | diameter 7.5 mm, depth 0.6 mm |
| Minimum PETG beneath washer seats | 4.46 mm |
| Captive-nut pockets | 6.3 mm across flats, depth 2.5 mm |
| Minimum PETG beneath nut pockets | 2.56 mm |
| PETG M3 / TPU M3 through-clearance | diameter 3.6 / 4.0 mm |
| Installed M3 axes, (Y,Z) | (13,5), (13,19.5), (34,19.5) mm |
| Bare TPU closed gap | 0.000 mm |
| Rigid PETG closed gap | 1.000 mm |
| Full M3x30 protrusion beyond PETG | 4.1 mm |
| Full M3x30 protrusion beyond nominal nut | 4.2 mm |

The accepted six-bay UMI section is translated 0.75 mm toward closure. The contact-side root hole then moves away from the closing edge, so the root-pair spacing is now 14.5 mm instead of 18 mm. The outer root hole and distal hole remain 21 mm apart longitudinally. The silhouette and all six bay polygons are otherwise retained. **New TPU prints are required.**

The Robotiq M5 axis, 4 mm shoulder, 6 mm head pocket, indexing sockets, and Y=10 mm TPU seating plane remain unchanged. The PETG side outline retains five straight edges. No compression sleeves or screw cutting are required for this review.

## Hardware basis and limits

Per jaw: three M3x30 socket-head screws, three M3 washers, and three M3 hex nuts. Reference hardware uses nominal 5.5 mm diameter x 3 mm screw heads and 5.5 mm-AF x 2.4 mm nuts. Threads are represented by clearance envelopes; the nominal nut is fully covered by the screw length.

**Washer size is provisional:** 7 mm outside diameter, 3.2 mm inside diameter, 0.5 mm thickness. The VIGRUE 1225-piece kit listing identifies M3 washers but does not publish their dimensions. Final washer fit therefore remains a physical check. The kit's material descriptions do not establish an allowable tightening torque for this printed joint.

All six screw tips point toward the same transverse side of the installed gripper. They do not project into the jaw closing gap, but remain exposed and can contact objects outside the modeled gripper.

## Verification

- `fusion_qa.json`: both printable bodies per jaw are solid; six bay profiles; all three complete TPU bores; complete PETG bores; all circular washer seats and hex pocket mouths enclosed; exact Robotiq M5/indexing cylinder dimensions; TPU seating at Y=10 mm.
- Fusion interference analysis of all 22 printable/reference hardware bodies returns no positive-volume intersections at mechanical closure. Measured gaps are 0 mm for TPU and 1 mm for PETG.
- `robotiq_fitcheck.json`: checked against the official closed Robotiq STEP with its four original fingertip/pad bodies excluded. All new M3 hardware clears the remaining mechanism, with a minimum distance of 3.5347 mm. The PETG shows the same pre-existing approximately 0.03682 mm3 contact per side at the OEM mounting interface; this is explicitly retained in the report rather than labeled zero overlap.
- `mesh_qa.json`: the two PETG and one TPU STL are watertight, consistently wound, and each one connected solid. Root-down transformations preserve mesh volume.

This verification covers rigid, nominal geometry in the closed configuration. It does not establish tightening torque, fatigue life, printed strength, or full-stroke/surrounding-workspace clearance. Physical fit and low-force closure remain to be checked on V2.

## Files

For slicing, use the [V2 print pack ZIP](../V2_PRINT_PACK_20260904.zip) or [print folder](../print_v2_20260904/PRINT_README.md). That pack contains only the three required STLs, already oriented for printing, with quantities and mesh checks. The assembly-oriented TPU export below requires rotation before slicing.

- `REVIEW_V2_Robotiq_FITCHECK.f3d`: editable full closed-gripper fit-check with nominal hardware.
- `REVIEW_V2_ZeroGap_M3x30.f3d` and `.step`: standalone finger pair and nominal hardware.
- `REVIEW_V2_nut_side.png`: exposed screw tips and captive nuts.
- `REVIEW_V2_head_side.png`: shallow washer seats and socket heads.
- `REVIEW_V2_on_Robotiq.png`: mounted closed-gripper review.
- `REVIEW_V2_2F85_PETG_Adapter_LEFT_M3_ROOT_DOWN_PRINT_1.stl`: one left PETG prototype.
- `REVIEW_V2_2F85_PETG_Adapter_RIGHT_M3_ROOT_DOWN_PRINT_1.stl`: one right PETG prototype.
- `REVIEW_V2_2F85_TPU95A_Finger_M3_PRINT_2.stl`: two identical new TPU prototypes, broad side down at 15.48 mm build height.

The other PETG STLs retain assembly orientation; use the ROOT_DOWN versions for slicing. Do not include any reference hardware in a printed-part export.

## Reproduce

Run `scripts/build_finger_v2_review.py` through Fusion MCP, then `scripts/inspect_finger_v2_review.py`. The copied `source_profile.json` preserves the exact source section used. The generator creates a new document and writes only to this review directory.

For the full mechanism check, import the official `2F-85_Closed.step` into that review, name the imported component `REFERENCE Robotiq closed mechanism`, and run `scripts/check_finger_v2_robotiq.py`. The script verifies the bounding boxes of the four excluded OEM fingertip bodies before excluding them.

Source listing: https://www.walmart.com/ip/503226562

Nominal washer dimensional reference: https://hi-line.com/m3-flat-washer-a2-stainless-steel/
