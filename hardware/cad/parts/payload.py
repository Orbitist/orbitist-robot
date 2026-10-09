"""Top-deck payload and accessories: battery + tray, electronics box, GNSS mast, e-stop,
rear hitch receiver, sprung front bumper with switches."""

from build123d import Align, Axis, Box, Compound, Cylinder, Helix, Plane, Pos, Rot, Circle, fillet, sweep

from params import Params
from parts.common import MATERIAL, PartRecord, box, extrusion_y, fasteners, hex_bolt, rod, y_cylinder, z_cylinder
from parts.frame import member_span


def rounded_box(x0, x1, y0, y1, z0, z1, r):
    b = box(x0, x1, y0, y1, z0, z1)
    return fillet(b.edges().filter_by(Axis.Z), r)


def battery(p: Params) -> list[PartRecord]:
    zt = p.frame_top_z
    bx, by, bz = p.battery_size
    x, y = p.battery_pos
    pack = rounded_box(x - bx / 2, x + bx / 2, y - by / 2, y + by / 2, zt + 6, zt + 6 + bz, 8)
    handle = rod((x - 60, y, zt + 6 + bz), (x - 60, y, zt + 6 + bz + 30), 5).fuse(
        rod((x + 60, y, zt + 6 + bz), (x + 60, y, zt + 6 + bz + 30), 5),
        rod((x - 66, y, zt + 6 + bz + 30), (x + 66, y, zt + 6 + bz + 30), 6))
    connector = box(x + bx / 2 - 2, x + bx / 2 + 14, y - 14, y + 14, zt + 6 + 20, zt + 6 + 36)
    # Tray: 3 mm aluminium pan with two side lips, bolted to the cross members' top slots.
    tray = box(x - bx / 2 - 10, x + bx / 2 + 10, y - by / 2 - 10, y + by / 2 + 10, zt, zt + 3)
    for sy in (-1, 1):
        ly = y + sy * (by / 2 + 10)
        tray = tray.fuse(box(x - bx / 2 - 10, x + bx / 2 + 10, ly - 1.5, ly + 1.5, zt, zt + 40))
    strap = box(x - 15, x + 15, y - by / 2 - 12, y + by / 2 + 12, zt + 6 + bz, zt + 6 + bz + 2)
    for sy in (-1, 1):
        ly = y + sy * (by / 2 + 11)
        strap = strap.fuse(box(x - 15, x + 15, ly - 1, ly + 1, zt + 3, zt + 6 + bz + 2))
    return [PartRecord("battery", "electrical", pack.fuse(handle, connector), p.masses["battery"]),
            PartRecord("battery_tray", "electrical", tray, 0.6, material="aluminium"),
            PartRecord("battery_strap", "accessory", strap, 0.1, material="black_plastic")]


def electronics_box(p: Params) -> list[PartRecord]:
    zt = p.frame_top_z
    ex, ey, ez = p.ebox_size
    x, y = p.ebox_pos
    base = rounded_box(x - ex / 2, x + ex / 2, y - ey / 2, y + ey / 2, zt + 10, zt + 10 + ez - 12, 10)
    lid = rounded_box(x - ex / 2 - 3, x + ex / 2 + 3, y - ey / 2 - 3, y + ey / 2 + 3,
                      zt + 10 + ez - 12, zt + 10 + ez, 12)
    for k in range(4):  # lid screws
        sx, sy = (1 if k % 2 else -1), (1 if k // 2 else -1)
        lid = lid.fuse(z_cylinder(x + sx * (ex / 2 - 12), y + sy * (ey / 2 - 12), zt + 10 + ez, 4, 2))
    # Mounting feet: an aluminium strip over each cross member under the box, bolted to its top slot.
    feet_shapes, feet_bolts = [], []
    for mx in p.cross_member_x:
        m0, m1, _ = member_span(p, mx)
        if m1 > x - ex / 2 and m0 < x + ex / 2:
            feet_shapes.append(box(m0 - 5, m1 + 5, y - ey / 2 - 20, y + ey / 2 + 20, zt, zt + 10))
            for fy in (y - ey / 2 - 8, y + ey / 2 + 8):
                feet_bolts.append(hex_bolt(((m0 + m1) / 2, fy, zt + 10), (0, 0, 1), 6, 16))
    feet = Compound(children=feet_shapes)
    glands = []
    for k, gy in enumerate((-100, -50, 0, 50, 100)):  # cable glands on the rear face
        gz = zt + 10 + 40 + (k % 2) * 30
        glands.append(Pos(x - ex / 2, y + gy, gz) * Rot(0, 90, 0) *
                      Cylinder(9 if k % 2 else 7, 22, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        glands[-1] = Pos(-22, 0, 0) * glands[-1]
    for gy in (-120, 120):  # antenna/RC connectors on the lid
        glands.append(z_cylinder(x - 40, y + gy, zt + 10 + ez, 6, 18))
    return [PartRecord("electronics_box", "electrical", base, p.masses["ebox"] * 0.7, material="grey_box"),
            PartRecord("electronics_lid", "electrical", lid, p.masses["ebox"] * 0.2, material="grey_box"),
            PartRecord("electronics_feet", "electrical", feet, 0.2, material="aluminium"),
            fasteners("electronics_bolts", feet_bolts),
            PartRecord("electronics_glands", "electrical", Compound(children=glands), 0.1, material="black_plastic")]


def gnss_mast(p: Params) -> list[PartRecord]:
    zt = p.frame_top_z
    mx, my = p.mast_pos
    base = box(mx - 30, mx + 30, my - 30, my + 30, zt, zt + 12)
    clamp = z_cylinder(mx, my, zt + 12, 20, 40)
    tube = z_cylinder(mx, my, zt + 12, 12.5, p.mast_height - 12) - z_cylinder(mx, my, zt + 12, 10, p.mast_height)
    top = zt + p.mast_height
    ground_plane = z_cylinder(mx, my, top - 3, 75, 3)
    puck = z_cylinder(mx, my, top, 45, 14)
    dome = z_cylinder(mx, my, top + 14, 36, 8).fuse(z_cylinder(mx, my, top + 22, 22, 6))
    bolts = [hex_bolt((mx + sx * 22, my + sy * 22, zt + 12), (0, 0, 1), 6, 16) for sx in (-1, 1) for sy in (-1, 1)]
    return [PartRecord("gnss_mast", "electrical", base.fuse(clamp, tube, ground_plane), 0.7, material="aluminium"),
            PartRecord("gnss_antenna", "electrical", puck.fuse(dome), p.masses["mast_gnss"] - 0.7, material="white"),
            fasteners("mast_bolts", bolts)]


def estop(p: Params) -> list[PartRecord]:
    x, y = p.estop_pos
    zt = p.frame_top_z
    plate = box(x - 45, x + 45, y - 40, y + 40, zt, zt + 4)
    base = rounded_box(x - 36, x + 36, y - 36, y + 36, zt + 4, zt + 56, 6)
    collar = z_cylinder(x, y, zt + 56, 20, 12)
    mushroom = z_cylinder(x, y, zt + 68, 20, 12).fuse(z_cylinder(x, y, zt + 80, 26, 10))
    return [PartRecord("estop_base", "accessory", plate.fuse(base), 0.25, material="yellow"),
            PartRecord("estop_button", "accessory", collar.fuse(mushroom), 0.1, material="red")]


def hitch(p: Params) -> list[PartRecord]:
    """2-inch receiver tube under the rear cross member, bolted through a plate."""
    x0, x1, ch = member_span(p, min(p.cross_member_x))
    zb = p.frame_top_z - ch  # member underside
    plate = box(x0 - 50, x1 + 50, -60, 60, zb - 8, zb)
    tube_c = p.hitch_height_z
    tube_len = 180
    tx1 = x1 + 20
    tx0 = tx1 - tube_len
    tube = box(tx0, tx1, -25.4, 25.4, tube_c - 25.4, tube_c + 25.4) - box(tx0 - 1, tx1 + 1, -19.4, 19.4,
                                                                           tube_c - 19.4, tube_c + 19.4)
    web = box(tx0 + 20, tx1, -25.4, 25.4, tube_c + 25.4, zb - 8)
    pin_x = p.frame_rear_x - 50
    tube = tube - y_cylinder(pin_x, 0, tube_c, 8.2, 60)
    pin = y_cylinder(pin_x, 0, tube_c, 7.9, 80).fuse(y_cylinder(pin_x, 36, tube_c, 14, 6))
    bolts = [hex_bolt((bx, by, zb - 8), (0, 0, -1), 8, 20) for bx in (x0 - 35, x1 + 35) for by in (-40, 40)]
    return [PartRecord("rear_hitch", "accessory", plate.fuse(tube, web), p.masses["hitch"], material="steel"),
            PartRecord("hitch_pin", "accessory", pin, 0.2, material="zinc"),
            fasteners("hitch_bolts", bolts)]


def bumper_layout(p: Params):
    """X positions of the bumper bar (rear face, front face, foam face), clear of the caster sweep."""
    sweep_front = p.caster_pivot_x + p.caster_trail + p.caster_wheel_diameter / 2
    bar_rear = sweep_front + p.bumper_travel + 15
    return bar_rear, bar_rear + 30, bar_rear + 30 + p.bumper_foam


def bumper(p: Params) -> list[PartRecord]:
    bar0, bar1, foam1 = bumper_layout(p)
    z0, z1 = p.bumper_z
    half_w = p.frame_width / 2 - 60
    zc = (z0 + z1) / 2
    bar = extrusion_y(-half_w, half_w, (bar0 + bar1) / 2, zc, 30, 60)
    foam = box(bar1, foam1, -half_w, half_w, z0, z1)
    foam = fillet(foam.edges().filter_by(Axis.Y), 12)
    # Guide blocks hang under the front cross member; the arms slide through them on springs.
    x0, x1, ch = member_span(p, max(p.cross_member_x))
    zb = p.frame_top_z - ch
    arm_z = zc
    arms, guides, springs, switches, bolts = [], [], [], [], []
    trip_gap = 8.0  # mm of bar travel before the switch opens
    for ay in (-p.bumper_arm_y, p.bumper_arm_y):
        guide = box(x0 - 30, x1, ay - 25, ay + 25, arm_z - 25, zb)
        guide = guide - Pos(x0 - 31, ay, arm_z) * Rot(0, 90, 0) * Cylinder(
            11, 80, align=(Align.CENTER, Align.CENTER, Align.MIN))
        guides.append(guide)
        arm_x0 = x0 - 30 - p.bumper_travel - 20
        arms.append(Pos(arm_x0, ay, arm_z) * Rot(0, 90, 0) * Cylinder(
            10, bar1 - arm_x0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        arms.append(box(arm_x0 - 6, arm_x0, ay - 20, ay + 20, arm_z - 20, arm_z + 20))  # rear end stop
        collar_x0 = x1 + trip_gap
        arms.append(Pos(collar_x0, ay, arm_z) * Rot(0, 90, 0) * Cylinder(
            18, 8, align=(Align.CENTER, Align.CENTER, Align.MIN)))  # trip collar + spring seat
        # Return spring between the collar and the bar's rear face.
        spring_len = bar0 - (collar_x0 + 8) - 4
        helix = Helix(pitch=14, height=spring_len, radius=15)
        spring = sweep(Plane(origin=helix @ 0, z_dir=helix % 0) * Circle(2.0), path=helix)
        springs.append(Pos(collar_x0 + 10, ay, arm_z) * Rot(0, 90, 0) * spring)
        # NC roller microswitch on the guide's front face beside the arm; the collar presses its
        # lever after trip_gap of travel and opens the e-stop loop.
        sw_y = ay + 30
        switches.append(box(x1 - 28, x1, sw_y - 8, sw_y + 8, arm_z - 10, arm_z + 10))
        switches.append(rod((x1, sw_y, arm_z + 6), (x1 + trip_gap - 2, sw_y - 6, arm_z), 1.5))
        switches.append(y_cylinder(x1 + trip_gap - 2, sw_y - 6, arm_z, 4, 5))
        for bx in (x0 - 15, x1 - 12):
            bolts.append(hex_bolt((bx, ay, arm_z - 25), (0, 0, -1), 6, 20))
    return [PartRecord("bumper_bar", "accessory", bar, p.masses["bumper"] * 0.6, material="aluminium"),
            PartRecord("bumper_foam", "accessory", foam, 0.3, material="foam"),
            PartRecord("bumper_arms", "accessory", Compound(children=arms), p.masses["bumper"] * 0.4, material="steel"),
            PartRecord("bumper_guides", "fork", Compound(children=guides), 0.6, material="black_plastic"),
            PartRecord("bumper_springs", "accessory", Compound(children=springs), 2 * p.masses["spring"], material="zinc"),
            PartRecord("bumper_switches", "accessory", Compound(children=switches), 2 * p.masses["switch"],
                       material="black_plastic"),
            fasteners("bumper_bolts", bolts)]


def payload(p: Params) -> list[PartRecord]:
    return battery(p) + electronics_box(p) + gnss_mast(p) + estop(p) + hitch(p) + bumper(p)
