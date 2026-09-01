"""Validate the handed PETG adapters and unchanged TPU production meshes."""

from pathlib import Path

import trimesh


EXPORT_DIR = Path(r"C:\Users\srini\Downloads\extracted")
FILES = {
    "2F85_PETG_Adapter_LEFT_M3_PRINT_1.stl": (22.8, 40.5, 27.2),
    "2F85_PETG_Adapter_RIGHT_M3_PRINT_1.stl": (22.8, 40.5, 27.2),
    "2F85_TPU95A_Finger_M3_PRINT_2.stl": (15.48, 74.019, 23.990),
}


def main() -> None:
    failures = []
    for name, expected_extents in FILES.items():
        # Merge coincident tessellation vertices before topology checks. Fusion
        # writes valid binary STL facets with vertices duplicated per triangle.
        mesh = trimesh.load_mesh(EXPORT_DIR / name, process=True)
        extents = ", ".join(f"{value:.3f}" for value in mesh.extents)
        print(
            f"{name}: watertight={mesh.is_watertight} "
            f"winding={mesh.is_winding_consistent} "
            f"volume_mm3={abs(mesh.volume):.3f} extents_mm=({extents})"
        )
        if not mesh.is_watertight:
            failures.append(f"{name} is not watertight")
        if not mesh.is_winding_consistent:
            failures.append(f"{name} has inconsistent winding")
        for actual, expected in zip(mesh.extents, expected_extents):
            if abs(actual - expected) > 0.05:
                failures.append(
                    f"{name} extent {actual:.3f} differs from {expected:.3f} mm"
                )
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
