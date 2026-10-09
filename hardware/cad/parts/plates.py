"""2D flat-plate outlines, used both to build the 3D model and to export cutting DXFs.

Every sketch is drawn in its own local XY frame; the caller positions it.
"""

from build123d import Circle, Polygon, Pos, Rectangle, SlotCenterPoint

from params import Params


def fork_side_plate(p: Params):
    """Dropout side plate: open slot from the bottom edge up to the axle centre.

    Local frame: X along the robot, Y up, origin at the bottom-centre of the plate.
    Returns (sketch, width, height, axle_y).
    """
    r = p.wheel_diameter / 2
    z_bot = r - 35
    h = p.frame_bottom_z - p.fork_top_t - z_bot
    w = p.fork_length_x
    axle_y = r - z_bot
    slot_w = p.axle_flats + 0.3  # slip fit over the axle flats
    plate = Pos(0, h / 2) * Rectangle(w, h)
    plate = plate - SlotCenterPoint((0, axle_y / 2 - 1), (0, axle_y), slot_w)
    for x in fork_plate_top_bolts():  # M8 clearance, into the fork top plate
        plate = plate - Pos(x, h - 15) * Circle(4.5)
    for x in torque_arm_bolts():  # M6, torque arm
        plate = plate - Pos(x, axle_y) * Circle(3.3)
    return plate, w, h, axle_y


def fork_plate_top_bolts():
    return (-70.0, 0.0, 70.0)


def torque_arm_bolts():
    return (-50.0, 50.0)


def torque_arm(p: Params):
    """Plate keyed to the axle flats, bolted to the fork plate at the torque-arm holes."""
    arm = Rectangle(130, 30)
    double_d = Circle(6.1) & Rectangle(p.axle_flats + 0.2, 12.2)
    arm = arm - double_d
    for x in torque_arm_bolts():
        arm = arm - Pos(x, 0) * Circle(3.3)
    return arm


def gusset(sx=1.0, sy=1.0):
    """L-gusset for the top face of a side-rail / cross-member joint (30-series, M6).

    Local origin at the outer corner of the joint; the rail leg runs along +X*sx,
    the member leg along +Y*sy. Returns (sketch, hole_centres).
    """
    pts = [(0, 0), (150, 0), (150, 30), (30, 150), (0, 150)]
    outline = Polygon(*[(x * sx, y * sy) for x, y in pts], align=None)
    holes = [(x * sx, 15 * sy) for x in (60, 105, 135)] + [(15 * sx, y * sy) for y in (60, 105, 135)]
    for hx, hy in holes:
        outline = outline - Pos(hx, hy) * Circle(3.3)
    return outline, holes


def caster_plate_extent(p: Params):
    """(x0, x1, y_inner, y_outer) of the caster corner plate (left side; mirror for right)."""
    cx, cy = p.caster_plate
    return (p.caster_pivot_x - cx / 2 - 10, p.frame_front_x,
            p.caster_pivot_y - cy / 2 - 15, p.frame_width / 2)


def caster_plate(p: Params):
    """Left caster corner plate (flip for the right). Local origin = plate rear-inner corner.

    Returns (sketch, width, height, holes) where holes are (x, y, radius, kind).
    """
    x0, x1, y_in, y_out = caster_plate_extent(p)
    w, h = x1 - x0, y_out - y_in
    plate = Pos(w / 2, h / 2) * Rectangle(w, h)
    px, py = p.caster_pivot_x - x0, p.caster_pivot_y - y_in
    bx, by = p.caster_bolts
    holes = []
    for dx in (-bx / 2, bx / 2):  # caster bolts: drill 6.8, tap M8 (bolts from below)
        for dy in (-by / 2, by / 2):
            holes.append((px + dx, py + dy, 3.4, "caster"))
    rail_y = p.side_rail_y - y_in  # M6 into the side rail's bottom slot
    holes += [(15.0, rail_y, 3.3, "rail"), (px, rail_y, 3.3, "rail")]
    member_x = max(p.cross_member_x) - x0  # M6 into the front member's bottom slot
    holes += [(member_x, py - 15, 3.3, "member"), (member_x, py + 20, 3.3, "member")]
    for i, (ax, ay, *_) in enumerate(holes):
        for bx_, by_, *_ in holes[i + 1:]:
            assert ((ax - bx_) ** 2 + (ay - by_) ** 2) ** 0.5 > 15, "caster plate holes too close"
    for hx, hy, r, _ in holes:
        plate = plate - Pos(hx, hy) * Circle(r)
    return plate, w, h, holes
