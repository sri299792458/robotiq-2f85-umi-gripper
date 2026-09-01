"""Build the video-derived two-part Robotiq 2F-85 replacement finger.

The Robotiq M5/indexing coordinates come from the supplied OEM fingertip STEP,
but no stock working-end solid is retained in the custom part.  The PETG
adapter follows the video-traced root/cheek outline and a separate TPU tongue
continues into the smooth, ribbed working finger seen in the Skild S1 videos.
Three transverse joint bolts are perpendicular to the OEM axial M5 fastening
direction.

Run this file with Fusion MCP's script executor.
"""

import os

import adsk.core
import adsk.fusion


OUTPUT_DIR = r"C:\Users\srini\Downloads\extracted"
OEM_FINGERTIP_STEP = os.path.join(
    OUTPUT_DIR, "2F-85_Flat_Overmolded_Fingertips.step"
)
DESIGN_NAME = "Skild_Inspired_2F85_TwoPart_Finger_Set"

# Affine side-plane trace from flakes_right_profile.  The first two vertices
# are snapped to the known OEM mating plane.  The outer edge beside screws 2
# and 3 is deliberately one straight segment; the earlier intermediate point
# was a false corner caused by glare in the video.
TRACED_PETG_SIDE_PROFILE = [
    # The very top of this edge is hidden under the black Robotiq jaw in the
    # source frame.  Extend only this occluded corner, leaving at least 1.5 mm
    # of PETG beyond the OEM screw-head counterbore.  This makes the mount
    # integral with the traced cheek instead of adding an OEM-derived flange.
    # The OEM STEP has a 9 mm screw-head counterbore about the M5 axis.  The
    # lowest traced root edge was partly hidden by the jaw, so extend only
    # that hidden corner far enough to retain material around the counterbore.
    (0.0, 29.5),
    (0.0, -1.8),
    (41.6, -1.7),
    (44.0, 3.9),
    (17.4, 26.7),
]
TRACED_JOINT_BOLT_CENTRES = [(10.0, 21.0), (10.0, 3.0), (31.0, 3.0)]

# The global opening rails are an affine reconstruction from the sharpest
# flakes-macro near-profile frame.  Points are root-to-tip in model Y/Z mm.
# Bay 0 and bay 1 contain the user's manually corrected hard endpoints.  The
# Bay 0 outer-top pixel was changed from [300, 80] to [304, 74], mapping to
# model Y/Z=(19.522, 8.919) through the established frame affine transform.
# The remaining endpoints are unchanged OpenCV traces.
TRACED_TPU_OUTER_OPENING_RAIL = [
    (19.522, 8.919),
    (27.20, 8.79),
    (30.59, 9.21),
    (41.34, 10.80),
    (44.30, 11.86),
    (59.51, 16.70),
    (63.34, 17.89),
    (76.27, 23.20),
    (80.52, 24.89),
    (87.12, 28.31),
    (89.61, 29.46),
    (96.14, 33.14),
]
TRACED_TPU_INNER_OPENING_RAIL = [
    (15.71, 24.92),
    (22.57, 25.34),
    (25.22, 25.84),
    (31.40, 26.48),
    (34.43, 26.84),
    (42.35, 27.61),
    (46.40, 28.26),
    (56.82, 29.55),
    (63.79, 30.09),
    (76.13, 31.45),
    (82.28, 32.04),
    (95.73, 33.51),
]

# Physical outside surfaces, offset about 2.8 mm from the opening rails.  The
# visible traced rails are unchanged, but the hidden TPU root is trimmed to
# Y=14 so it begins beyond the OEM counterbore opening at Y=13.384.  The root
# M4 bosses begin at Y=14.5.  No TPU enters the STEP-defined M5 keep-out.
TRACED_TPU_OUTER_SILHOUETTE = [
    (8.00, -3.00),
    (13.00, 2.00),
    (19.522, 6.119),
    (27.31, 5.99),
    (30.98, 6.44),
    (41.87, 8.05),
    (45.16, 9.20),
    (60.36, 14.03),
    (64.35, 15.28),
    (77.33, 20.61),
    (81.71, 22.36),
    (88.38, 25.81),
    (90.93, 26.99),
    (97.51, 30.70),
    (100.50, 33.50),
]
TRACED_TPU_INNER_SILHOUETTE = [
    (8.00, 28.00),
    (15.54, 27.71),
    (22.30, 28.13),
    (24.86, 28.62),
    (31.10, 29.26),
    (34.14, 29.63),
    (42.02, 30.39),
    (46.03, 31.04),
    (56.53, 32.33),
    (63.52, 32.88),
    (75.84, 34.23),
    (81.99, 34.82),
    (95.43, 36.29),
    (100.50, 33.50),
]

# Order for every bay is outer top, inner top, inner bottom, outer bottom.
# These are only the four hard endpoints.  The two side edges are regenerated
# from the continuous global rail functions rather than drawn as chords.
TRACED_BAY_CORNERS = [
    [(19.522, 8.919), (15.71, 24.92), (22.57, 25.34), (27.20, 8.79)],
    [(30.59, 9.21), (25.22, 25.84), (31.40, 26.48), (41.34, 10.80)],
    [(44.30, 11.86), (34.43, 26.84), (42.35, 27.61), (59.51, 16.70)],
    [(63.34, 17.89), (46.40, 28.26), (56.82, 29.55), (76.27, 23.20)],
    [(80.52, 24.89), (63.79, 30.09), (76.13, 31.45), (87.12, 28.31)],
    [(89.61, 29.46), (82.28, 32.04), (95.73, 33.51), (96.14, 33.14)],
]

# The source-frame Z direction is opposite the Robotiq fingertip's installed
# gripping direction.  Keep the established global trace datum so PETG, M5,
# all three M4 axes, and every accepted bay remain at their prior coordinates.
# The manually traced rail tip is registered to raw Z=36.324 mm, which retains
# the existing 0.75 mm per-side clearance at the OEM mechanical zero.
OEM_CONTACT_DATUM_Z = -1.50
CLOSED_CLEARANCE_PER_SIDE = 0.75
TRACE_REFLECTION_SUM = (
    36.324 + OEM_CONTACT_DATUM_Z + CLOSED_CLEARANCE_PER_SIDE
)


def orient_trace(points):
    return [
        (round(y_mm, 3), round(TRACE_REFLECTION_SUM - z_mm, 3))
        for y_mm, z_mm in points
    ]


PETG_SIDE_PROFILE = orient_trace(TRACED_PETG_SIDE_PROFILE)
FRAME_DERIVED_JOINT_BOLT_CENTRES = orient_trace(TRACED_JOINT_BOLT_CENTRES)

# The recovered UMI STEP proves that the complete three-hole triangle is the
# design datum: 30 mm between the root pair and 35 mm from the root pair to the
# third outer hole.  The video-derived Skild offsets are exactly 60% of those
# values: 18 and 21 mm.  Translate the complete triangle together so its root
# reinforcement begins just beyond the Robotiq M5 tool keep-out at Y=13.384;
# never move only the root pair and distort the UMI layout.
JOINT_BOLT_CENTRES = [
    (17.0, FRAME_DERIVED_JOINT_BOLT_CENTRES[0][1]),
    (17.0, FRAME_DERIVED_JOINT_BOLT_CENTRES[1][1]),
    (38.0, FRAME_DERIVED_JOINT_BOLT_CENTRES[2][1]),
]

# Fair quadratic rails fitted to the traced opening endpoints in source-frame
# coordinates.  A quadratic has one curvature sign over its full length, so it
# cannot reproduce the small hills and valleys caused by interpolating every
# noisy image point.  Maximum correction to an accepted bay endpoint is under
# 0.7 mm on the outer rail and under 0.31 mm on the inner rail.
FAIR_OUTER_OPENING_RAW = (
    (19.522, 8.919),
    (57.831, 10.3989647078),
    (96.14, 33.14),
)
FAIR_INNER_OPENING_RAW = (
    (15.71, 24.92),
    (55.72, 29.1623137629),
    (95.73, 33.51),
)
RAIL_WALL = 2.8
TPU_LONGITUDINAL_SHIFT = 7.0


def quadratic_point(control, fraction):
    first, middle, last = control
    inverse = 1.0 - fraction
    return (
        inverse * inverse * first[0]
        + 2.0 * inverse * fraction * middle[0]
        + fraction * fraction * last[0],
        inverse * inverse * first[1]
        + 2.0 * inverse * fraction * middle[1]
        + fraction * fraction * last[1],
    )


def quadratic_point_at_y(control, y_value):
    # Every fair-rail control point uses the midpoint Y, making Y linear in
    # the Bezier parameter and allowing exact evaluation at a bay endpoint.
    fraction = (y_value - control[0][0]) / (control[2][0] - control[0][0])
    return quadratic_point(control, fraction)


def sample_quadratic(control, count, start_fraction=0.0, end_fraction=1.0):
    return [
        quadratic_point(
            control,
            start_fraction
            + (end_fraction - start_fraction) * index / (count - 1),
        )
        for index in range(count)
    ]


def reflected(points):
    return [(y_mm, TRACE_REFLECTION_SUM - z_mm) for y_mm, z_mm in points]


def shifted_tpu(points):
    return [
        (y_mm + TPU_LONGITUDINAL_SHIFT, z_mm)
        for y_mm, z_mm in points
    ]


def offset_control(control, z_offset):
    return tuple((y_mm, z_mm + z_offset) for y_mm, z_mm in control)


FAIR_OUTER_OPENING = tuple(shifted_tpu(reflected(FAIR_OUTER_OPENING_RAW)))
FAIR_INNER_OPENING = tuple(shifted_tpu(reflected(FAIR_INNER_OPENING_RAW)))
TPU_OUTER_OPENING_RAIL = [
    quadratic_point_at_y(
        FAIR_OUTER_OPENING, y_mm + TPU_LONGITUDINAL_SHIFT
    )
    for y_mm, _ in TRACED_TPU_OUTER_OPENING_RAIL
]
TPU_INNER_OPENING_RAIL = [
    quadratic_point_at_y(
        FAIR_INNER_OPENING, y_mm + TPU_LONGITUDINAL_SHIFT
    )
    for y_mm, _ in TRACED_TPU_INNER_OPENING_RAIL
]


def fair_bay_corners(corners):
    outer_top, inner_top, inner_bottom, outer_bottom = corners
    return [
        quadratic_point_at_y(
            FAIR_OUTER_OPENING,
            outer_top[0] + TPU_LONGITUDINAL_SHIFT,
        ),
        quadratic_point_at_y(
            FAIR_INNER_OPENING,
            inner_top[0] + TPU_LONGITUDINAL_SHIFT,
        ),
        quadratic_point_at_y(
            FAIR_INNER_OPENING,
            inner_bottom[0] + TPU_LONGITUDINAL_SHIFT,
        ),
        quadratic_point_at_y(
            FAIR_OUTER_OPENING,
            outer_bottom[0] + TPU_LONGITUDINAL_SHIFT,
        ),
    ]


VIDEO_TRACED_BAY_CORNERS = [
    fair_bay_corners(corners) for corners in TRACED_BAY_CORNERS
]

# Keep all six accepted bay polygons unchanged.  These exterior rails are
# registered separately from the user's manual upper-finger trace.  Each rail
# has a deliberate bend: the outer rail changes slope at Y=57.575 mm and the
# contact rail bends near Y=63.871 mm.  Two fair quadratic segments retain
# those knees without creating repeated image-noise undulations.
OUTER_ROOT_RAW = (
    (14.0, 3.045099153342),
    (17.499403643985, 6.040862454643),
    (19.522, 6.119),
)
OUTER_HIDDEN_TRANSITION_RAW = (
    (19.522, 6.119),
    (25.5046, 6.3502),
    (31.4871, 7.5980),
    (37.4697, 7.9021),
)
MANUAL_OUTER_ROOT_RAW = (
    (37.4697, 7.9021),
    (47.9232, 8.4334),
    (58.0642, 11.2912),
)
MANUAL_OUTER_MID_RAW = (
    (58.0642, 11.2912),
    (76.7796, 20.2769),
    (94.2772, 31.4165),
)
MANUAL_OUTER_TIP_RAW = (
    (94.2772, 31.4165),
    (97.4405, 32.5882),
    (100.6039, 36.4630),
)
MANUAL_CONTACT_ROOT_RAW = (
    (14.3524, 32.9055),
    (38.3215, 31.1749),
    (62.3994, 30.4978),
)
MANUAL_CONTACT_TIP_RAW = (
    (62.3994, 30.4978),
    (81.0984, 35.2914),
    (100.3962, 36.1852),
)

# The last outer segment stays below the unchanged Bay 5 corner with 0.8 mm
# printable clearance before turning sharply into the traced nose.  The two
# manually traced endpoints differ by only 0.347 mm and are closed with this
# short tangent-directed rounded bridge.
MANUAL_TIP_BRIDGE_RAW = (
    (100.6039, 36.4630),
    (100.6797, 36.5560),
    (100.5161, 36.1908),
    (100.3962, 36.1852),
)


TPU_OUTER_ROOT = tuple(shifted_tpu(reflected(OUTER_ROOT_RAW)))
TPU_OUTER_HIDDEN_TRANSITION = tuple(
    shifted_tpu(reflected(OUTER_HIDDEN_TRANSITION_RAW))
)
TPU_MANUAL_OUTER_ROOT = tuple(
    shifted_tpu(reflected(MANUAL_OUTER_ROOT_RAW))
)
TPU_MANUAL_OUTER_MID = tuple(
    shifted_tpu(reflected(MANUAL_OUTER_MID_RAW))
)
TPU_MANUAL_OUTER_TIP = tuple(
    shifted_tpu(reflected(MANUAL_OUTER_TIP_RAW))
)
TPU_MANUAL_CONTACT_ROOT = tuple(
    shifted_tpu(reflected(MANUAL_CONTACT_ROOT_RAW))
)
TPU_MANUAL_CONTACT_TIP = tuple(
    shifted_tpu(reflected(MANUAL_CONTACT_TIP_RAW))
)
TPU_MANUAL_TIP_BRIDGE = tuple(
    shifted_tpu(reflected(MANUAL_TIP_BRIDGE_RAW))
)
UMI_CONTACT_SURFACE_Z = TRACE_REFLECTION_SUM - 36.324
UMI_CONTACT_ROOT = (
    14.0 + TPU_LONGITUDINAL_SHIFT,
    UMI_CONTACT_SURFACE_Z,
)
UMI_CONTACT_TIP = (
    100.5 + TPU_LONGITUDINAL_SHIFT,
    UMI_CONTACT_SURFACE_Z,
)


def yz_point(y_mm: float, z_mm: float) -> adsk.core.Point3D:
    """Return a point in a YZ-plane sketch from model Y/Z millimetres."""

    # Fusion's YZ sketch X maps to -model Z and sketch Y maps to model Y.
    return adsk.core.Point3D.create(-z_mm / 10.0, y_mm / 10.0, 0)


def xz_point(x_mm: float, z_mm: float) -> adsk.core.Point3D:
    """Return a point in an XZ-plane sketch from model X/Z millimetres."""

    # Fusion orients the XZ sketch's local Y opposite model Z.
    return adsk.core.Point3D.create(x_mm / 10.0, -z_mm / 10.0, 0)


def point_collection(points, mapper):
    collection = adsk.core.ObjectCollection.create()
    for first, second in points:
        collection.add(mapper(first, second))
    return collection


def sample_rail_segment(control, start, end, count=6):
    start_fraction = (start[0] - control[0][0]) / (
        control[2][0] - control[0][0]
    )
    end_fraction = (end[0] - control[0][0]) / (
        control[2][0] - control[0][0]
    )
    samples = sample_quadratic(control, count, start_fraction, end_fraction)
    samples[0] = start
    samples[-1] = end
    return samples


def add_bay_profile(sketch, corners):
    """Draw one bay with straight ribs and sides on the two global rails."""

    outer_top, inner_top, inner_bottom, outer_bottom = corners
    inner_side = sample_rail_segment(
        FAIR_INNER_OPENING, inner_top, inner_bottom
    )
    outer_side = sample_rail_segment(
        FAIR_OUTER_OPENING, outer_top, outer_bottom
    )
    lines = sketch.sketchCurves.sketchLines
    splines = sketch.sketchCurves.sketchFittedSplines
    lines.addByTwoPoints(yz_point(*outer_top), yz_point(*inner_top))
    splines.add(point_collection(inner_side, yz_point))
    lines.addByTwoPoints(yz_point(*inner_bottom), yz_point(*outer_bottom))
    splines.add(point_collection(list(reversed(outer_side)), yz_point))


def add_quadratic_control_spline(sketch, quadratic_control):
    """Create an exact quadratic as an equivalent cubic Bezier spline."""

    first, middle, last = quadratic_control
    cubic_control = [
        first,
        (
            first[0] + (middle[0] - first[0]) * 2.0 / 3.0,
            first[1] + (middle[1] - first[1]) * 2.0 / 3.0,
        ),
        (
            last[0] + (middle[0] - last[0]) * 2.0 / 3.0,
            last[1] + (middle[1] - last[1]) * 2.0 / 3.0,
        ),
        last,
    ]
    return add_cubic_control_spline(sketch, cubic_control)


def add_cubic_control_spline(sketch, cubic_control):
    return sketch.sketchCurves.sketchControlPointSplines.add(
        [yz_point(first, second) for first, second in cubic_control], 3
    )


def add_parameter(design, name, expression, units, comment):
    existing = design.userParameters.itemByName(name)
    if existing:
        existing.expression = expression
        existing.comment = comment
        return existing
    return design.userParameters.add(
        name,
        adsk.core.ValueInput.createByString(expression),
        units,
        comment,
    )


def add_polygon(sketch, points):
    lines = sketch.sketchCurves.sketchLines
    for index, start in enumerate(points):
        end = points[(index + 1) % len(points)]
        lines.addByTwoPoints(yz_point(*start), yz_point(*end))


def profiles_collection(sketch):
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    return profiles


def largest_profile(sketch):
    candidates = []
    for index in range(sketch.profiles.count):
        profile = sketch.profiles.item(index)
        candidates.append((profile.areaProperties().area, profile))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def symmetric_extrude(
    component,
    profiles,
    distance_expression,
    operation,
    participant_bodies=None,
):
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profiles, operation)
    extrude_input.setSymmetricExtent(
        adsk.core.ValueInput.createByString(distance_expression), True
    )
    if participant_bodies is not None:
        extrude_input.participantBodies = list(participant_bodies)
    return extrudes.add(extrude_input)


def one_side_extrude(
    component,
    profiles,
    distance_expression,
    direction,
    operation,
    participant_bodies=None,
):
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profiles, operation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString(distance_expression)
    )
    extrude_input.setOneSideExtent(extent, direction)
    if participant_bodies is not None:
        extrude_input.participantBodies = list(participant_bodies)
    return extrudes.add(extrude_input)


def positive_y_direction(component):
    normal = component.xZConstructionPlane.geometry.normal
    if normal.y >= 0:
        return adsk.fusion.ExtentDirections.PositiveExtentDirection
    return adsk.fusion.ExtentDirections.NegativeExtentDirection


def y_offset_plane(component, y_mm):
    normal = component.xZConstructionPlane.geometry.normal
    signed_y = y_mm if normal.y >= 0 else -y_mm
    plane_input = component.constructionPlanes.createInput()
    plane_input.setByOffset(
        component.xZConstructionPlane,
        adsk.core.ValueInput.createByString(str(signed_y) + " mm"),
    )
    return component.constructionPlanes.add(plane_input)


def import_oem_master(app, root):
    before = root.occurrences.count
    options = app.importManager.createSTEPImportOptions(OEM_FINGERTIP_STEP)
    imported = app.importManager.importToTarget2(options, root)
    if not imported or root.occurrences.count <= before:
        raise RuntimeError("The OEM fingertip STEP did not import into Fusion")
    occurrence = root.occurrences.item(before)
    occurrence.component.name = "2F-85 Two-Part Finger Master"
    if occurrence.component.bRepBodies.count != 1:
        raise RuntimeError("Expected one OEM fingertip seed body")
    occurrence.component.bRepBodies.item(0).name = "OEM fingertip interface seed"
    return occurrence


def build_petg_adapter(component):
    # The imported STEP is measurement/reference geometry only.  Keeping any
    # portion of that stock flat fingertip adds a flange absent from the video.
    component.bRepBodies.item(0).deleteMe()

    adapter_sketch = component.sketches.add(component.yZConstructionPlane)
    adapter_sketch.name = "PETG adapter - video-traced five-edge side cheek"
    add_polygon(adapter_sketch, PETG_SIDE_PROFILE)
    feature = symmetric_extrude(
        component,
        largest_profile(adapter_sketch),
        "adapterOverallWidth",
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    adapter = feature.bodies.item(0)
    adapter.name = "PETG Adapter - traced root with OEM hole coordinates"

    # Make two 4 mm PETG cheeks around a 14 mm central TPU tongue.  The main
    # rectangular slot begins at Y=13.5, just beyond the OEM STEP counterbore
    # opening at Y=13.384.  The continuous UMI-derived TPU joint frame begins
    # at the same plane; no isolated circular pockets or exposed lugs exist.
    slot_sketch = component.sketches.add(component.yZConstructionPlane)
    slot_sketch.name = "Central TPU tongue slot - 0.3 mm clearance per side"
    add_polygon(
        slot_sketch,
        [
            (13.5, -8.0),
            (47.0, -8.0),
            (47.0, 45.0),
            (8.0, 45.0),
        ],
    )
    symmetric_extrude(
        component,
        profiles_collection(slot_sketch),
        "adapterSlotWidth",
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )

    # Restore the complete OEM axial fastening geometry after the union.  The
    # supplied STEP has a 5.3 mm shank clearance from Y=0 to a Y=4 shoulder,
    # followed by a 9 mm screw-head counterbore.  Give the printed PETG head
    # pocket 0.2 mm diametral clearance.  The two 2 mm indexing holes are
    # shallow, as in the stock fingertip, rather than tunnels through the
    # complete adapter.
    m5_shank_sketch = component.sketches.add(component.xZConstructionPlane)
    m5_shank_sketch.name = "OEM M5 shank clearance to 4 mm head shoulder"
    m5_shank_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        xz_point(0.0, 12.36), 0.265
    )
    one_side_extrude(
        component,
        profiles_collection(m5_shank_sketch),
        "4 mm",
        positive_y_direction(component),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )

    counterbore_sketch = component.sketches.add(y_offset_plane(component, 4.0))
    counterbore_sketch.name = "OEM M5 screw-head counterbore - 9.2 mm print clearance"
    counterbore_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        xz_point(0.0, 12.36), 0.460
    )
    one_side_extrude(
        component,
        profiles_collection(counterbore_sketch),
        "40 mm",
        positive_y_direction(component),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        participant_bodies=(adapter,),
    )

    indexing_sketch = component.sketches.add(component.xZConstructionPlane)
    indexing_sketch.name = "Two OEM 2 mm indexing-pin sockets - 2.5 mm deep"
    indexing_circles = indexing_sketch.sketchCurves.sketchCircles
    indexing_circles.addByCenterRadius(xz_point(-4.5, 12.36), 0.100)
    indexing_circles.addByCenterRadius(xz_point(4.5, 12.36), 0.100)
    one_side_extrude(
        component,
        profiles_collection(indexing_sketch),
        "2.5 mm",
        positive_y_direction(component),
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        participant_bodies=(adapter,),
    )

    return adapter


def add_smooth_tpu_profile(component):
    sketch = component.sketches.add(component.yZConstructionPlane)
    sketch.name = "TPU smooth video-derived silhouette"

    # The accepted bay cuts are independent from this exterior silhouette.
    # Preserve the traced bends of the outer rail, but use the recovered UMI
    # mechanical rule for the working face: one straight contact datum from
    # root to tip.  That is what lets two identical fingers close without the
    # large V-shaped gap produced by perspective-fitting both silhouettes.
    outer = [
        add_quadratic_control_spline(sketch, TPU_OUTER_ROOT),
        add_cubic_control_spline(sketch, TPU_OUTER_HIDDEN_TRANSITION),
        add_quadratic_control_spline(sketch, TPU_MANUAL_OUTER_ROOT),
        add_quadratic_control_spline(sketch, TPU_MANUAL_OUTER_MID),
        add_quadratic_control_spline(sketch, TPU_MANUAL_OUTER_TIP),
    ]

    lines = sketch.sketchCurves.sketchLines
    lines.addByTwoPoints(outer[-1].endSketchPoint, yz_point(*UMI_CONTACT_TIP))
    contact = lines.addByTwoPoints(
        yz_point(*UMI_CONTACT_TIP), yz_point(*UMI_CONTACT_ROOT)
    )
    contact.isConstruction = False
    lines.addByTwoPoints(yz_point(*UMI_CONTACT_ROOT), outer[0].startSketchPoint)
    return sketch


def build_tpu_finger(component):
    profile_sketch = add_smooth_tpu_profile(component)
    feature = symmetric_extrude(
        component,
        largest_profile(profile_sketch),
        "tpuFingerThickness",
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    finger = feature.bodies.item(0)
    finger.name = "TPU 95A Smooth Truss Finger"

    # The original UMI finger does not use three isolated circular lugs.  Its
    # root wall and outer rail form one continuous frame around the triangular
    # M4 layout.  Recreate that scaled logic inside the PETG cheeks: a root
    # strap surrounds the 18 mm pair and a straight outer cap reaches the
    # third hole 21 mm forward.  Bay 0 is cut afterward, so it remains a true
    # through-bay beneath the PETG adapter rather than being filled in.
    finger = add_tpu_joint_frame(component, finger)

    window_sketch = component.sketches.add(component.yZConstructionPlane)
    window_sketch.name = "Six true through-bays 0-5 traced from video"
    for corners in VIDEO_TRACED_BAY_CORNERS:
        add_bay_profile(window_sketch, corners)
    symmetric_extrude(
        component,
        profiles_collection(window_sketch),
        "20 mm",
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        participant_bodies=(finger,),
    )

    return finger


def add_tpu_joint_frame(component, finger):
    """Add the continuous UMI-derived root/outer frame around three M4 holes."""

    sketch = component.sketches.add(component.yZConstructionPlane)
    sketch.name = "UMI-derived continuous three-screw TPU joint frame"
    # Root pair center Y=17 with 3.5 mm material to the M5 keep-out boundary.
    add_polygon(
        sketch,
        [(13.5, 10.5), (20.5, 10.5), (20.5, 36.1), (13.5, 36.1)],
    )
    # One straight, non-lobed outer reinforcement contains both outer M4
    # holes and terminates inside the extended PETG cheek.
    add_polygon(
        sketch,
        [(16.0, 29.0), (41.5, 29.0), (41.5, 36.1), (16.0, 36.1)],
    )
    feature = symmetric_extrude(
        component,
        profiles_collection(sketch),
        "tpuFingerThickness",
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        participant_bodies=(finger,),
    )
    if feature.bodies.count:
        return feature.bodies.item(0)
    return finger


def cut_three_joint_bolts(component):
    # Video-visible triangular pattern.  All axes are model X and therefore
    # perpendicular to the OEM M5 axis, which is model Y.  The two
    # root screws form an 18 mm transverse pair in the side plane and screw 3
    # remains exactly 21 mm forward on the outer rail: the complete 0.600x UMI
    # triangle.  The triangle is translated as one unit to clear the M5 tool
    # envelope without changing those relative dimensions.
    centres = JOINT_BOLT_CENTRES
    sketch = component.sketches.add(component.yZConstructionPlane)
    sketch.name = "Three transverse PETG-to-TPU joint bolts"
    circles = sketch.sketchCurves.sketchCircles
    for y_mm, z_mm in centres:
        circles.addByCenterRadius(yz_point(y_mm, z_mm), 0.215)
    symmetric_extrude(
        component,
        profiles_collection(sketch),
        "30 mm",
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )
    return centres


def apply_appearances(app, design, adapter, finger):
    library = app.materialLibraries.itemByName("Fusion Appearance Library")
    gray_source = library.appearances.itemByName("Plastic - Matte (Gray)")
    green_source = library.appearances.itemByName("Plastic - Matte (Green)")
    gray = design.appearances.addByCopy(gray_source, "Printed PETG - Light Gray")
    green = design.appearances.addByCopy(green_source, "Printed TPU 95A - Pale Green")
    adapter.appearance = gray
    finger.appearance = green


def export_stl(export_manager, body, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    options = export_manager.createSTLExportOptions(body, path)
    options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    export_manager.execute(options)
    return path


def extent_mm(body):
    box = body.boundingBox
    return tuple(
        round((high - low) * 10.0, 3)
        for low, high in zip(box.minPoint.asArray(), box.maxPoint.asArray())
    )


def save_flat_preview(app, path):
    """Save an appearance-check preview without misleading black shadows."""

    graphics = app.preferences.graphicsPreferences
    previous_preset = graphics.graphicsPreset
    graphics.graphicsPreset = adsk.core.GraphicsPresets.CustomGraphicsPreset
    effects = graphics.canvasEffects
    previous_effects = {
        "ground_plane": effects.isGroundPlaneEnabled,
        "ground_shadow": effects.isGroundShadowEnabled,
        "ground_reflection": effects.isGroundReflectionEnabled,
        "object_shadow": effects.isObjectShadowEnabled,
        "ambient_occlusion": effects.isAmbientOcclusionEnabled,
    }
    try:
        effects.isGroundPlaneEnabled = False
        effects.isGroundShadowEnabled = False
        effects.isGroundReflectionEnabled = False
        effects.isObjectShadowEnabled = False
        effects.isAmbientOcclusionEnabled = False
        app.activeViewport.visualStyle = adsk.core.VisualStyles.ShadedVisualStyle
        app.activeViewport.fit()
        app.activeViewport.refresh()
        if not app.activeViewport.saveAsImageFile(path, 1600, 1200):
            raise RuntimeError("Fusion did not save the flat preview")
    finally:
        if previous_preset == adsk.core.GraphicsPresets.CustomGraphicsPreset:
            effects.isGroundPlaneEnabled = previous_effects["ground_plane"]
            effects.isGroundShadowEnabled = previous_effects["ground_shadow"]
            effects.isGroundReflectionEnabled = previous_effects[
                "ground_reflection"
            ]
            effects.isObjectShadowEnabled = previous_effects["object_shadow"]
            effects.isAmbientOcclusionEnabled = previous_effects[
                "ambient_occlusion"
            ]
        else:
            graphics.graphicsPreset = previous_preset
        app.activeViewport.refresh()


def robotiq_closed_transform(is_left):
    """Map the OEM fingertip-local frame onto the supplied closed gripper."""

    matrix = adsk.core.Matrix3D.create()
    if is_left:
        values = (
            (0.0, 0.0, -1.0, -0.15),
            (0.0, 1.0, 0.0, 12.482),
            (1.0, 0.0, 0.0, 0.0),
        )
    else:
        values = (
            (0.0, 0.0, 1.0, 0.15),
            (0.0, 1.0, 0.0, 12.482),
            (-1.0, 0.0, 0.0, 0.0),
        )
    for row, row_values in enumerate(values):
        for column, value in enumerate(row_values):
            matrix.setCell(row, column, value)
    return matrix


def run(_context: str):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    document = app.activeDocument
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent

    add_parameter(
        design,
        "adapterOverallWidth",
        "22 mm",
        "mm",
        "OEM fingertip width retained by the PETG adapter",
    )
    add_parameter(
        design,
        "adapterSlotWidth",
        "14 mm",
        "mm",
        "Central space between PETG clamp cheeks",
    )
    add_parameter(
        design,
        "tpuFingerThickness",
        "13.4 mm",
        "mm",
        "TPU tongue; 0.3 mm clearance per side",
    )
    add_parameter(
        design,
        "jointBoltDiameter",
        "4.3 mm",
        "mm",
        "M4 clearance for the three transverse joint bolts",
    )
    add_parameter(
        design,
        "closedClearancePerSide",
        "0.75 mm",
        "mm",
        "Per-side TPU-to-TPU clearance at mechanical zero",
    )

    master_occurrence = import_oem_master(app, root)
    component = master_occurrence.component
    adapter = build_petg_adapter(component)
    finger = build_tpu_finger(component)
    joint_centres = cut_three_joint_bolts(component)
    apply_appearances(app, design, adapter, finger)

    adapter.name = "PETG Adapter - PRINT 2"
    finger.name = "TPU 95A Finger - PRINT 2"

    # Place the opposed pair on the actual closed-jaw transforms recovered
    # from 2F-85_Closed.step.  The local OEM Z=-1.5 mm surfaces map to global
    # X=0, while local Y=0 maps to global Y=124.82 mm on both jaws.
    master_occurrence.transform = robotiq_closed_transform(True)
    root.occurrences.addExistingComponent(
        component, robotiq_closed_transform(False)
    )

    design.computeAll()
    if component.bRepBodies.count != 2:
        raise RuntimeError(
            "Expected exactly PETG and TPU bodies; got "
            + str(component.bRepBodies.count)
        )
    # Feature cuts can replace a body's underlying BRep object.  Refresh the
    # handles by their final names before export so Fusion does not silently
    # skip an STL when an earlier handle has gone stale.
    adapter = component.bRepBodies.itemByName("PETG Adapter - PRINT 2")
    finger = component.bRepBodies.itemByName("TPU 95A Finger - PRINT 2")
    if adapter is None or finger is None or not adapter.isValid or not finger.isValid:
        raise RuntimeError("Could not refresh the final PETG/TPU bodies for export")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    export_manager = design.exportManager
    exports = []
    f3d_path = os.path.join(OUTPUT_DIR, DESIGN_NAME + ".f3d")
    export_manager.execute(
        export_manager.createFusionArchiveExportOptions(f3d_path, root)
    )
    exports.append(f3d_path)
    step_path = os.path.join(OUTPUT_DIR, DESIGN_NAME + ".step")
    export_manager.execute(export_manager.createSTEPExportOptions(step_path, root))
    exports.append(step_path)
    exports.append(
        export_stl(export_manager, adapter, "2F85_PETG_Adapter_PRINT_2.stl")
    )
    exports.append(
        export_stl(export_manager, finger, "2F85_TPU95A_Finger_PRINT_2.stl")
    )

    # Plain shaded mode avoids drawing BRep boundary lines between tangent
    # faces.  Disable viewport shadows only while saving: deep cavities were
    # otherwise rendered nearly black and could be mistaken for an appearance
    # override.  The user's normal graphics preferences are restored afterward.
    preview_path = os.path.join(OUTPUT_DIR, DESIGN_NAME + "_preview.png")
    save_flat_preview(app, preview_path)
    exports.append(preview_path)

    print("Created", DESIGN_NAME)
    print("Master bodies", component.bRepBodies.count)
    print("Adapter extent mm", extent_mm(adapter))
    print("TPU extent mm", extent_mm(finger))
    print("OEM M5 axis Y; three joint-bolt axes X; dot product = 0")
    print("Joint centres YZ mm", joint_centres)
    for path in exports:
        print("EXPORT", path)
