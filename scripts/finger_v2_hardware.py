"""Nominal, thread-free M3x30 hardware for V2 fit and protrusion review."""

import math


def build_hardware(parent, label, centres, base):
    adsk = base["adsk"]
    yz_point = base["yz_point"]
    add_polygon = base["add_polygon"]
    one_side_extrude = base["one_side_extrude"]
    occurrence = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    component = occurrence.component
    component.name = "REFERENCE hardware " + label + " - M3x30, nominal 7x0.5 washers"
    head_sign = 1.0 if label == "LEFT" else -1.0
    nut_sign = -head_sign

    def plane_at(x):
        inp = component.constructionPlanes.createInput()
        normal = component.yZConstructionPlane.geometry.normal
        inp.setByOffset(component.yZConstructionPlane,
                        adsk.core.ValueInput.createByReal(x / 10 * (1 if normal.x > 0 else -1)))
        return component.constructionPlanes.add(inp)

    def direction(plane, sign):
        return (adsk.fusion.ExtentDirections.PositiveExtentDirection
                if plane.geometry.normal.x * sign > 0
                else adsk.fusion.ExtentDirections.NegativeExtentDirection)

    def profiles(sketch, annular=False):
        result = adsk.core.ObjectCollection.create()
        for p in sketch.profiles:
            if not annular or p.profileLoops.count == 2:
                result.add(p)
        if result.count != 3:
            raise RuntimeError(f"Expected three hardware profiles in {sketch.name}; got {result.count}")
        return result

    def extrude(sketch, plane, sign, length, operation, annular=False):
        return one_side_extrude(component, profiles(sketch, annular), f"{length} mm",
                                direction(plane, sign), operation)

    def circles_at(x, name, diameter, inner=None):
        plane = plane_at(x)
        sketch = component.sketches.add(plane)
        sketch.name = name
        for y, z in centres:
            sketch.sketchCurves.sketchCircles.addByCenterRadius(yz_point(y, z), diameter / 20)
            if inner:
                sketch.sketchCurves.sketchCircles.addByCenterRadius(yz_point(y, z), inner / 20)
        return sketch, plane

    new = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    # Head-bearing plane = outer face 13 - seat depth 0.6 + washer 0.5.
    bearing_x = head_sign * 12.9
    sketch, plane = circles_at(bearing_x, "Nominal M3 socket heads - 5.5 x 3 mm", 5.5)
    feature = extrude(sketch, plane, head_sign, 3.0, new)
    for i, body in enumerate(feature.bodies):
        body.name = f"M3x30 screw {i + 1} - nominal unthreaded envelope"
    sketch, plane = circles_at(bearing_x, "Full 30 mm screw shanks", 3.0)
    extrude(sketch, plane, -head_sign, 30.0, join)

    plane = plane_at(head_sign * 15.9)
    socket = component.sketches.add(plane)
    socket.name = "2.5 mm hex keys - visual reference"
    radius = 2.5 / math.sqrt(3)
    for y, z in centres:
        add_polygon(socket, [(y + radius * math.cos(i * math.pi / 3),
                              z + radius * math.sin(i * math.pi / 3)) for i in range(6)])
    extrude(socket, plane, -head_sign, 1.5, cut)

    sketch, plane = circles_at(head_sign * 12.4, "Provisional M3 washers - OD7 ID3.2 t0.5", 7, 3.2)
    feature = extrude(sketch, plane, head_sign, 0.5, new, True)
    for i, body in enumerate(feature.bodies):
        body.name = f"M3 washer {i + 1} - PROVISIONAL 7 x 0.5 mm"

    plane = plane_at(nut_sign * 10.5)
    nuts = component.sketches.add(plane)
    nuts.name = "Nominal M3 nuts - AF5.5 x 2.4 mm"
    radius = 5.5 / math.sqrt(3)
    for y, z in centres:
        add_polygon(nuts, [(y + radius * math.cos(i * math.pi / 3),
                            z + radius * math.sin(i * math.pi / 3)) for i in range(6)])
        # Clearance cylinder avoids reporting intended thread engagement as a
        # collision; axial engagement is measured separately by QA.
        nuts.sketchCurves.sketchCircles.addByCenterRadius(yz_point(y, z), 0.16)
    feature = extrude(nuts, plane, nut_sign, 2.4, new, True)
    for i, body in enumerate(feature.bodies):
        body.name = f"M3 nut {i + 1} - nominal thread-free reference"

    design = parent.parentDesign
    app = adsk.core.Application.get()
    library = app.materialLibraries.itemByName("Fusion Appearance Library")
    steel = design.appearances.itemByName("V2 nominal steel hardware")
    if not steel:
        steel = design.appearances.addByCopy(library.appearances.itemByName("Steel - Satin"),
                                            "V2 nominal steel hardware")
    for body in component.bRepBodies:
        body.appearance = steel

    for sketch in component.sketches:
        sketch.isVisible = False
    for plane in component.constructionPlanes:
        plane.isLightBulbOn = False
    return occurrence
