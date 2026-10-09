"""Hub-motor drive modules: tire, rim, motor can, flatted axle, bolt-on fork, torque arm."""

from build123d import (
    Align, Box, Compound, Cylinder, Plane, Pos, Rot, Torus, extrude,
)

from params import Params
from parts.common import MATERIAL, PartRecord, box, fasteners, hex_bolt, hex_nut, rod
from parts.plates import fork_plate_top_bolts, fork_side_plate, torque_arm, torque_arm_bolts

TREAD_GROOVES = 24


def hub_motor_local(p: Params):
    """Hub motor built along local Z (axle), wheel centred at the origin, cable exit at +Z.

    Returns (tire, metal) shapes so they can carry different colours.
    """
    r = p.wheel_diameter / 2
    w = p.tire_width
    rim_r = p.hub_diameter / 2 + 8
    # Tire: torus section trimmed to the rim, with shallow tread grooves.
    tire = Torus(r - w / 2, w / 2) - Cylinder(rim_r - 1, w + 2)
    for k in range(TREAD_GROOVES):
        groove = Rot(0, 0, k * 360 / TREAD_GROOVES) * (Pos(r - 2, 0, 0) * Box(6, 3.5, w * 0.7))
        tire = tire - groove
    rim = Cylinder(rim_r, w - 14)
    can = Cylinder(p.hub_diameter / 2, w + 10)
    covers = Cylinder(p.hub_diameter / 2 - 20, w + 14)
    motor = rim.fuse(can, covers)
    for s in (1, -1):  # bolt ring on each side cover
        for k in range(6):
            a = k * 60
            motor = motor.fuse(Rot(0, 0, a) * (Pos(p.hub_diameter / 2 - 32, 0, s * (w / 2 + 7)) *
                                                Cylinder(4, 3)))
    # Axle: shoulders inside the dropouts, flatted ends through the fork plates.
    axle_len = p.dropout_spacing + 2 * p.fork_plate_t + 30
    axle = Cylinder(6, axle_len)
    flats = Box(p.axle_flats, 30, axle_len) & Cylinder(6, axle_len)
    half = p.dropout_spacing / 2
    axle = (axle & Cylinder(6, p.dropout_spacing)).fuse(flats - Cylinder(7, p.dropout_spacing))
    axle = axle.fuse(Cylinder(9, p.dropout_spacing))  # shoulder spacers
    motor = motor.fuse(axle)
    return tire, motor


def drive(p: Params) -> list[PartRecord]:
    parts = []
    m = p.masses
    r = p.wheel_diameter / 2
    tire_l, motor_l = hub_motor_local(p)
    sk, w, h, axle_y = fork_side_plate(p)
    arm_sk = torque_arm(p)
    half = p.dropout_spacing / 2
    t = p.fork_plate_t
    z_top = p.frame_bottom_z
    z_bot = z_top - p.fork_top_t - h
    for side, sgn in (("L", 1), ("R", -1)):
        y = sgn * p.side_rail_y
        # Cable exit (+Z local) must point inboard: -Y for the left wheel, +Y for the right.
        orient = Pos(0, y, r) * Rot(90 * sgn, 0, 0)
        parts.append(PartRecord(f"tire_{side}", "drive", orient * tire_l, 1.2, material="rubber"))
        parts.append(PartRecord(f"hub_motor_{side}", "drive", orient * motor_l, m["hub_motor"] - 1.2))
        # Motor cable: out of the hollow axle on the inboard side, straight up, then along the
        # underside of the rail toward the electronics box (the deck skirt is only ~18 mm away).
        axle_len = p.dropout_spacing + 2 * t + 30
        y_exit = y - sgn * (axle_len / 2 + 4)  # turn up right at the axle end: the deck skirt is close
        cable = rod((0, y - sgn * axle_len / 2, r), (0, y_exit, r), 3.5)
        cable = cable.fuse(rod((0, y_exit, r), (0, y_exit, z_top - 12), 3.5),
                           rod((0, y_exit, z_top - 12), (-150, y_exit, z_top - 12), 3.5))
        parts.append(PartRecord(f"motor_cable_{side}", "drive", cable, 0.2, material="black_plastic"))

        # Fork: two dropout side plates (from the DXF outline), top plate, saddle tabs.
        plates = []
        for py in (y - half - t, y + half):
            plane = Plane(origin=(0, py + t, z_bot), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
            plates.append(extrude(plane * sk, t))
        top = box(-w / 2, w / 2, y - half - t, y + half + t, z_top - p.fork_top_t, z_top)
        rail_half = p.side_rail[0] / 2
        tabs = [box(-w / 2, w / 2, ty, ty + t, z_top, z_top + p.side_rail[1] - 5)
                for ty in (y - rail_half - t, y + rail_half)]
        bolts = []
        for ty, s in ((y - rail_half - t, -1), (y + rail_half + t, 1)):  # tab bolts into the rail side slots
            for bx in (-60, 60):
                bolts.append(hex_bolt((bx, ty, z_top + 15), (0, s, 0), 6, 14))
                bolts.append(hex_bolt((bx, ty, z_top + 45), (0, s, 0), 6, 14))
        for bx in fork_plate_top_bolts():  # side plates to top plate (M8), heads outboard
            for py, s in ((y - half - t, -1), (y + half + t, 1)):
                bolts.append(hex_bolt((bx, py, z_bot + h - 15), (0, s, 0), 8, 20))
        for bx in (-70, 0, 70):  # top plate up into the rail's bottom slot (M8)
            bolts.append(hex_bolt((bx, y, z_top - p.fork_top_t), (0, 0, -1), 8, 16))
        fork = top.fuse(*plates, *tabs)
        parts.append(PartRecord(f"drive_fork_{side}", "fork", fork, m["drive_fork"],
                                meta={"plate_height": h, "axle_z_in_plate": axle_y}))

        # Torque arm on the outboard plate, keyed to the axle flats, bolted at the M6 holes.
        py_out = y + sgn * (half + t)
        plane = Plane(origin=(0, py_out + sgn * 5, r), x_dir=(1, 0, 0), z_dir=(0, -sgn, 0))
        arm = extrude(plane * arm_sk, 5)
        parts.append(PartRecord(f"torque_arm_{side}", "fork", arm, 0.15))
        for bx in torque_arm_bolts():
            bolts.append(hex_bolt((bx, py_out + sgn * 5, r), (0, sgn, 0), 6, 16))
        bolts.append(hex_nut((0, py_out + sgn * 5, r), (0, sgn, 0), af=19, height=8, bore=6.2))  # axle nut
        bolts.append(hex_nut((0, y - sgn * (half + t), r), (0, -sgn, 0), af=19, height=8, bore=6.2))
        parts.append(fasteners(f"drive_bolts_{side}", bolts))
    return parts
