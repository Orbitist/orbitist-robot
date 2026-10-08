"""Parametric assembly of the Orbitist platform v1 frame (build123d).

Each part is returned as a PartRecord carrying its name, group, display
color and an estimated mass, so build.py can export STEP, renders, a cut
list and a centre-of-gravity estimate from one source of truth.
"""

from dataclasses import dataclass, field

from build123d import Align, Box, Cylinder, Pos, Rot, Shape

from params import Params

GROUP_COLORS = {
    "frame": (0.72, 0.74, 0.78),
    "drive": (0.15, 0.15, 0.17),
    "fork": (0.85, 0.45, 0.15),
    "caster": (0.25, 0.25, 0.28),
    "deck": (0.20, 0.55, 0.30),
    "electrical": (0.20, 0.40, 0.75),
    "accessory": (0.85, 0.20, 0.20),
}


@dataclass
class PartRecord:
    name: str
    group: str
    shape: Shape
    mass: float
    extrusion: dict | None = None  # {"profile": "30x30", "length": mm}
    meta: dict = field(default_factory=dict)

    @property
    def color(self):
        return GROUP_COLORS[self.group]


def _box(x0, x1, y0, y1, z0, z1) -> Shape:
    """Axis-aligned box from min/max corners."""
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3)


def _y_cylinder(x, y, z, radius, width) -> Shape:
    """Cylinder whose axis runs along Y, centred at (x, y, z)."""
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, width)


def frame(p: Params) -> list[PartRecord]:
    parts = []
    m = p.masses
    sw, sh = p.side_rail
    # Side rails (30x60, standing on edge), full frame length.
    for side, sgn in (("L", 1), ("R", -1)):
        y_out = sgn * p.frame_width / 2
        y_in = y_out - sgn * sw
        parts.append(
            PartRecord(
                f"side_rail_{side}",
                "frame",
                _box(p.frame_rear_x, p.frame_front_x, min(y_in, y_out), max(y_in, y_out),
                     p.frame_bottom_z, p.frame_top_z),
                m["extrusion_30x60_per_m"] * p.frame_length / 1000,
                extrusion={"profile": "30x60", "length": p.frame_length},
            )
        )
    # Cross members between the side rails, flush with the frame top.
    length = p.frame_width - 2 * sw
    for i, x in enumerate(p.cross_member_x):
        cw, ch, prof = p.cross_profile(x)
        x0 = max(x - cw / 2, p.frame_rear_x)
        x0 = min(x0, p.frame_front_x - cw)
        parts.append(
            PartRecord(
                f"cross_member_{i + 1}",
                "frame",
                _box(x0, x0 + cw, -length / 2, length / 2, p.frame_top_z - ch, p.frame_top_z),
                m[f"extrusion_{prof}_per_m"] * length / 1000,
                extrusion={"profile": prof, "length": length},
            )
        )
    return parts


def drive(p: Params) -> list[PartRecord]:
    """Hub motors in bolt-on forks under each side rail (swappable drive module)."""
    parts = []
    m = p.masses
    r = p.wheel_diameter / 2
    for side, sgn in (("L", 1), ("R", -1)):
        y = sgn * p.side_rail_y
        tire = _y_cylinder(0, y, r, r, p.tire_width)
        hub = _y_cylinder(0, y, r, p.hub_diameter / 2, p.tire_width + 10)
        axle = _y_cylinder(0, y, r, 6, p.dropout_spacing + 2 * p.fork_plate_t + 30)
        parts.append(PartRecord(f"hub_motor_{side}", "drive", tire.fuse(hub).fuse(axle), m["hub_motor"]))

        # Fork: top plate bolted under the side rail + two dropout side plates.
        half = p.dropout_spacing / 2
        fx0, fx1 = -p.fork_length_x / 2, p.fork_length_x / 2
        z_top = p.frame_bottom_z
        z_bot = r - 35
        top = _box(fx0, fx1, y - half - p.fork_plate_t, y + half + p.fork_plate_t,
                   z_top - p.fork_top_t, z_top)
        plates = []
        for py in (y - half - p.fork_plate_t, y + half):
            plates.append(_box(fx0, fx1, py, py + p.fork_plate_t, z_bot, z_top - p.fork_top_t))
        # Saddle tabs up both faces of the side rail, bolted into its side slots
        # (strength.py: a bottom-slot-only joint is too weak against sideways loads).
        rail_half = p.side_rail[0] / 2
        for ty in (y - rail_half - p.fork_plate_t, y + rail_half):
            plates.append(_box(fx0, fx1, ty, ty + p.fork_plate_t, z_top, z_top + p.side_rail[1] - 5))
        fork = top.fuse(*plates)
        parts.append(PartRecord(f"drive_fork_{side}", "fork", fork, m["drive_fork"],
                                meta={"plate_height": z_top - p.fork_top_t - z_bot,
                                      "axle_z_in_plate": r - z_bot}))
    return parts


def casters(p: Params) -> list[PartRecord]:
    parts = []
    r = p.caster_wheel_diameter / 2
    for side, sgn in (("L", 1), ("R", -1)):
        px, py = p.caster_pivot_x, sgn * p.caster_pivot_y
        wx = px - p.caster_trail  # wheel trails behind the pivot when driving forward
        wheel = _y_cylinder(wx, py, r, r, p.caster_wheel_width)
        half = p.caster_wheel_width / 2 + 8
        fork_top_z = 2 * r + 10  # yoke top; spindle housing fills the gap to the frame
        fork = _box(wx - 30, px + 40, py - half - 6, py + half + 6, fork_top_z, fork_top_z + 8)
        for fy in (py - half - 6, py + half):
            fork = fork.fuse(_box(wx - 25, wx + 25, fy, fy + 6, r - 20, fork_top_z))
        spindle = Pos(px, py, fork_top_z) * Cylinder(16, p.frame_bottom_z - fork_top_z,
                                                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Mount block bridging the cross member down to the spindle housing.
        mount = _box(px - 45, px + 45, py - 45, py + 45, p.frame_bottom_z,
                     p.frame_top_z - p.cross_profile(p.caster_pivot_x)[1])
        shape = wheel.fuse(fork, spindle)
        if mount.volume > 0:
            shape = shape.fuse(mount)
        parts.append(PartRecord(f"caster_{side}", "caster", shape, p.masses["caster"],
                                meta={"sweep_radius": p.caster_trail + r}))
    return parts


def decks(p: Params, config: str) -> list[PartRecord]:
    parts = []
    for i, (x, y) in enumerate(p.deck_slots(config)):
        shell = Pos(x, y, p.deck_shell_bottom_z) * Cylinder(
            p.deck_housing_diameter / 2, p.deck_shell_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        motor_z = p.deck_shell_bottom_z + p.deck_shell_height
        motor = Pos(x, y, motor_z) * Cylinder(
            p.deck_motor_diameter / 2, p.deck_motor_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        parts.append(PartRecord(f"mower_deck_{i + 1}", "deck", shell.fuse(motor), p.deck_mass,
                                meta={"center": (x, y), "motor_top_z": motor_z + p.deck_motor_height}))
    return parts


def payload(p: Params) -> list[PartRecord]:
    parts = []
    m = p.masses
    zt = p.frame_top_z
    bx, by, bz = p.battery_size
    parts.append(PartRecord("battery", "electrical",
                            _box(p.battery_pos[0] - bx / 2, p.battery_pos[0] + bx / 2,
                                 p.battery_pos[1] - by / 2, p.battery_pos[1] + by / 2, zt, zt + bz),
                            m["battery"]))
    ex, ey, ez = p.ebox_size
    parts.append(PartRecord("electronics_box", "electrical",
                            _box(p.ebox_pos[0] - ex / 2, p.ebox_pos[0] + ex / 2,
                                 p.ebox_pos[1] - ey / 2, p.ebox_pos[1] + ey / 2, zt, zt + ez),
                            m["ebox"]))
    mx, my = p.mast_pos
    mast = Pos(mx, my, zt) * Cylinder(12, p.mast_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    antenna = Pos(mx, my, zt + p.mast_height) * Cylinder(50, 25, align=(Align.CENTER, Align.CENTER, Align.MIN))
    parts.append(PartRecord("gnss_mast", "electrical", mast.fuse(antenna), m["mast_gnss"]))

    estop = Pos(p.frame_rear_x + 60, -p.side_rail_y + 60, zt) * Cylinder(
        25, 90, align=(Align.CENTER, Align.CENTER, Align.MIN))
    parts.append(PartRecord("estop", "accessory", estop, 0.3))

    # Rear hitch plate + pin, hanging off the rear cross member.
    hx = p.frame_rear_x
    hitch = _box(hx - 80, hx, -40, 40, p.hitch_height_z - 6, p.hitch_height_z + 6)
    hitch = hitch.fuse(_box(hx - 10, hx, -40, 40, p.hitch_height_z, p.frame_top_z))
    hitch = hitch.fuse(Pos(hx - 50, 0, p.hitch_height_z - 40) * Cylinder(
        8, 100, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    parts.append(PartRecord("rear_hitch", "accessory", hitch, m["hitch"]))

    # Front bumper bar ahead of the caster sweep, on two arms.
    sweep = p.caster_trail + p.caster_wheel_diameter / 2
    bump_x = p.caster_pivot_x + sweep + 30
    arm_y = p.caster_pivot_y - 120
    bumper = _box(bump_x, bump_x + 30, -p.frame_width / 2 + 60, p.frame_width / 2 - 60, 230, 290)
    for ay in (-arm_y, arm_y):
        bumper = bumper.fuse(_box(p.frame_front_x - 1, bump_x, ay - 15, ay + 15, 260, 290))
        bumper = bumper.fuse(_box(p.frame_front_x - 30, p.frame_front_x, ay - 15, ay + 15, 260, p.frame_top_z))
    parts.append(PartRecord("front_bumper", "accessory", bumper, m["bumper"]))
    return parts


def assembly(p: Params, config: str = "single") -> list[PartRecord]:
    return frame(p) + drive(p) + casters(p) + decks(p, config) + payload(p)

