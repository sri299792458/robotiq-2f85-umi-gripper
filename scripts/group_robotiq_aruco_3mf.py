"""Group Fusion's per-body 3MF objects into one multipart object per plate.

Fusion exports every flush marker cell as a separate build item.  Bambu Studio
must instead receive two multipart objects so arranging the plate cannot move
individual cells.  This postprocessor preserves Fusion's black/white color
groups and creates one parent component for each marker ID found in the source.
"""

from __future__ import annotations

import json
import re
import sys
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
ET.register_namespace("", CORE)
ET.register_namespace("p", PROD)
ET.register_namespace("m", "http://schemas.microsoft.com/3dmanufacturing/material/2015/02")


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def group_3mf(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source, "r") as archive:
        files = {name: archive.read(name) for name in archive.namelist()}

    model_name = "3D/3dmodel.model"
    root = ET.fromstring(files[model_name])
    resources = root.find(q(CORE, "resources"))
    build = root.find(q(CORE, "build"))
    if resources is None or build is None:
        raise RuntimeError("Fusion 3MF has no resources/build section")

    objects = resources.findall(q(CORE, "object"))
    object_ids = [int(obj.attrib["id"]) for obj in objects]
    next_id = max(object_ids) + 1

    children_by_marker: dict[int, list[ET.Element]] = {}
    for obj in objects:
        match = re.match(r"ID(\d+) ", obj.attrib.get("name", ""))
        if match:
            children_by_marker.setdefault(int(match.group(1)), []).append(obj)
    if not children_by_marker:
        raise RuntimeError(f"No marker bodies found in {source}")

    grouped_ids: list[int] = []
    for marker_id, children in sorted(children_by_marker.items()):

        parent_id = next_id
        next_id += 1
        parent = ET.SubElement(
            resources,
            q(CORE, "object"),
            {
                "id": str(parent_id),
                "name": f"Robotiq linkage ArUco ID {marker_id}",
                "type": "model",
                q(PROD, "UUID"): str(uuid.uuid4()),
            },
        )
        components = ET.SubElement(parent, q(CORE, "components"))
        for child in children:
            ET.SubElement(
                components,
                q(CORE, "component"),
                {
                    "objectid": child.attrib["id"],
                    q(PROD, "UUID"): str(uuid.uuid4()),
                },
            )
        grouped_ids.append(parent_id)

    for item in list(build):
        build.remove(item)
    for parent_id in grouped_ids:
        ET.SubElement(
            build,
            q(CORE, "item"),
            {
                "objectid": str(parent_id),
                q(PROD, "UUID"): str(uuid.uuid4()),
            },
        )

    files[model_name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    files["Metadata/project_settings.config"] = (
        json.dumps(
            {
                "version": "02.00.00.00",
                "printer_technology": "FFF",
                "filament_colour": ["#000000", "#FFFFFF"],
                "filament_type": ["PLA", "PLA"],
                "nozzle_diameter": ["0.4"],
            },
            indent=4,
        )
        + "\n"
    ).encode("utf-8")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)

    print(destination)
    print(f"grouped build objects: {len(grouped_ids)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: group_robotiq_aruco_3mf.py SOURCE.3mf DESTINATION.3mf")
    group_3mf(Path(sys.argv[1]), Path(sys.argv[2]))
