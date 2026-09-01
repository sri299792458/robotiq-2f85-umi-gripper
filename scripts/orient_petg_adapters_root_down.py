"""Create root-down PETG adapter STLs from the validated production meshes.

The source meshes use the installed CAD axes: X is the three-M3 bolt axis,
Y runs from the Robotiq mating face toward the fingertip, and Z is the jaw
closing direction.  Printing an X side face on the bed leaves the opposite
cheek cantilevered across the TPU slot.  Rotate +90 degrees about X so the
Y=0 Robotiq mating face is the build-plane contact and both cheeks grow in Z.
"""

from pathlib import Path
import math

import numpy as np
import trimesh


OUTPUT = Path(r"C:\Users\srini\Downloads\extracted")
SOURCES = {
    "LEFT": OUTPUT / "2F85_PETG_Adapter_LEFT_M3_PRINT_1.stl",
    "RIGHT": OUTPUT / "2F85_PETG_Adapter_RIGHT_M3_PRINT_1.stl",
}


def orient(source: Path, destination: Path) -> None:
    mesh = trimesh.load_mesh(source, force="mesh")
    if not mesh.is_watertight or not mesh.is_winding_consistent:
        raise RuntimeError(f"Source mesh is not production-valid: {source}")

    source_volume = mesh.volume
    transform = trimesh.transformations.rotation_matrix(
        math.pi / 2.0,
        [1.0, 0.0, 0.0],
    )
    mesh.apply_transform(transform)
    mesh.apply_translation([0.0, 0.0, -mesh.bounds[0, 2]])

    expected_extents = np.array([22.8, 27.2, 40.5])
    if not np.allclose(mesh.extents, expected_extents, atol=0.002):
        raise RuntimeError(
            f"Unexpected root-down extents {mesh.extents.tolist()} for {source}"
        )
    if not math.isclose(mesh.volume, source_volume, abs_tol=0.001):
        raise RuntimeError(f"Rigid orientation changed volume for {source}")
    if not math.isclose(mesh.bounds[0, 2], 0.0, abs_tol=1e-6):
        raise RuntimeError(f"Root face is not on Z=0 for {source}")

    mesh.export(destination)
    print(
        destination,
        "extents_mm=",
        np.round(mesh.extents, 3).tolist(),
        "volume_mm3=",
        round(mesh.volume, 3),
    )


def main() -> None:
    for label, source in SOURCES.items():
        destination = OUTPUT / (
            f"2F85_PETG_Adapter_{label}_M3_ROOT_DOWN_PRINT_READY.stl"
        )
        orient(source, destination)


if __name__ == "__main__":
    main()
