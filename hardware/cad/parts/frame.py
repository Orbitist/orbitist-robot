"""Frame: T-slot side rails and cross members, cast corner brackets, gussets, fasteners."""

from build123d import Compound, Plane, extrude

from params import Params
from parts.common import PartRecord, box, extrusion_x, extrusion_y, fasteners, hex_bolt
from parts.plates import gusset

GUSSET_T = 5.0
BRACKET = 28.0  # cast inside corner bracket, 30-series
BRACKET_T = 8.0


def member_span(p: Params, x):
    """(x0, x1, height) of the cross member centred at x."""
    cw, ch, _ = p.cross_profile(x)
    x0 = max(x - cw / 2, p.frame_rear_x)
    x0 = min(x0, p.frame_front_x - cw)
    return x0, x0 + cw, ch


def rails_and_members(p: Params) -> list[PartRecord]:
    parts = []
    m = p.masses
    sw, sh = p.side_rail
    zc = (p.frame_bottom_z + p.frame_top_z) / 2
    for side, sgn in (("L", 1), ("R", -1)):
        yc = sgn * p.side_rail_y
        parts.append(PartRecord(
            f"side_rail_{side}", "frame",
            extrusion_x(p.frame_rear_x, p.frame_front_x, yc, zc, sw, sh),
            m["extrusion_30x60_per_m"] * p.frame_length / 1000,
            extrusion={"profile": "30x60", "length": p.frame_length}))
    length = p.frame_width - 2 * sw
    for i, x in enumerate(p.cross_member_x):
        x0, x1, ch = member_span(p, x)
        prof = p.cross_profile(x)[2]
        parts.append(PartRecord(
            f"cross_member_{i + 1}", "frame",
            extrusion_y(-length / 2, length / 2, (x0 + x1) / 2, p.frame_top_z - ch / 2, x1 - x0, ch),
            m[f"extrusion_{prof}_per_m"] * length / 1000,
            extrusion={"profile": prof, "length": length}))
    return parts


def corner_brackets(p: Params) -> list[PartRecord]:
    """Two cast inside-corner brackets per cross-member end, in the top slot level, plus bolts."""
    shapes, bolts = [], []
    y_in = p.frame_width / 2 - p.side_rail[0]  # inner face of the side rails
    z1 = p.frame_top_z
    z0 = z1 - BRACKET
    for x in p.cross_member_x:
        x0, x1, _ = member_span(p, x)
        for sgn in (1, -1):
            yi = sgn * y_in
            for face, dx in ((x0, -1), (x1, 1)):
                if (dx < 0 and x0 <= p.frame_rear_x + 0.5) or (dx > 0 and x1 >= p.frame_front_x - 0.5):
                    continue  # end members are flush with the rail ends: no rail beyond that face
                # Leg along the rail (x direction) and leg along the member face (y direction).
                leg_rail = box(face, face + dx * BRACKET, yi, yi - sgn * BRACKET_T, z0, z1)
                leg_member = box(face, face + dx * BRACKET_T, yi, yi - sgn * BRACKET, z0, z1)
                shapes.append(leg_rail.fuse(leg_member))
                zm = (z0 + z1) / 2
                bolts.append(hex_bolt((face + dx * 18, yi - sgn * BRACKET_T, zm), (0, -sgn, 0), 6, 14))
                bolts.append(hex_bolt((face + dx * BRACKET_T, yi - sgn * 18, zm), (dx, 0, 0), 6, 14))
    parts = [PartRecord("corner_brackets", "bracket", Compound(children=shapes),
                        p.masses["bracket"] * len(shapes))]
    parts.append(fasteners("bracket_bolts", bolts))
    return parts


def gussets(p: Params) -> list[PartRecord]:
    """Top-face L-gussets at the joints next to the drive axle (strength.py item 3)."""
    shapes, bolts = [], []
    for x in p.gusset_members:
        x0, x1, _ = member_span(p, x)
        for sgn in (1, -1):
            y_out = sgn * p.frame_width / 2
            for face, sx in ((x0, -1), (x1, 1)):
                sk, holes = gusset(sx, -sgn)
                plane = Plane(origin=(face, y_out, p.frame_top_z))
                shapes.append(extrude(plane * sk, GUSSET_T))
                for hx, hy in holes:
                    bolts.append(hex_bolt((face + hx, y_out + hy, p.frame_top_z + GUSSET_T), (0, 0, 1), 6, 16))
    return [PartRecord("frame_gussets", "bracket", Compound(children=shapes),
                       p.masses["gusset"] * len(shapes), material="aluminium"),
            fasteners("gusset_bolts", bolts)]


def battery_rails(p: Params) -> list[PartRecord]:
    """Two 30x30 rails flush with the frame top, butted between the cross members either side
    of the battery, so the tray has something under it (the battery sits over the axle, between
    members)."""
    bx, by, _ = p.battery_size
    x, y = p.battery_pos
    xs = sorted(p.cross_member_x)
    behind = max(m for m in xs if m <= x - bx / 2 + 1e-6) if any(m <= x - bx / 2 for m in xs) else xs[0]
    ahead = min(m for m in xs if m >= x + bx / 2 - 1e-6) if any(m >= x + bx / 2 for m in xs) else xs[-1]
    x0 = member_span(p, behind)[1]
    x1 = member_span(p, ahead)[0]
    parts, brackets, bolts = [], [], []
    for i, sy in enumerate((-1, 1)):
        yc = y + sy * (by / 2 + 10)
        parts.append(PartRecord(f"battery_rail_{i + 1}", "frame",
                                extrusion_x(x0, x1, yc, p.frame_top_z - 15, 30, 30),
                                p.masses["extrusion_30x30_per_m"] * (x1 - x0) / 1000,
                                extrusion={"profile": "30x30", "length": x1 - x0}))
        for face, dx in ((x0, 1), (x1, -1)):  # corner brackets at both ends, on the outer side
            so = sy  # bracket on the side away from the battery
            yf = yc + so * 15
            leg_a = box(face, face + dx * BRACKET, yf, yf + so * BRACKET_T, p.frame_top_z - BRACKET, p.frame_top_z)
            leg_b = box(face, face - dx * BRACKET_T, yf, yf + so * BRACKET, p.frame_top_z - BRACKET, p.frame_top_z)
            brackets.append(leg_a.fuse(leg_b))
            zm = p.frame_top_z - BRACKET / 2
            bolts.append(hex_bolt((face + dx * 18, yf + so * BRACKET_T, zm), (0, so, 0), 6, 14))
            bolts.append(hex_bolt((face - dx * BRACKET_T, yf + so * 18, zm), (-dx, 0, 0), 6, 14))
    parts.append(PartRecord("battery_rail_brackets", "bracket", Compound(children=brackets),
                            p.masses["bracket"] * len(brackets)))
    parts.append(fasteners("battery_rail_bolts", bolts))
    return parts


def frame(p: Params) -> list[PartRecord]:
    return rails_and_members(p) + corner_brackets(p) + gussets(p) + battery_rails(p)
