"""Mower deck modules: Ryobi-class 21" deck shell, blade, motor, anti-scalp rollers, hangers."""

from build123d import Align, Compound, Cylinder, Plane, Polygon, Pos, Rot, revolve, Axis

from params import Params
from parts.common import PartRecord, box, hex_nut, rod, y_cylinder, z_cylinder
from parts.frame import member_span

SHELL_T = 3.0


def deck_shell_local(p: Params):
    """Deck shell (revolved pan with a skirt), blade and motor, centred on local Z.

    Returns (shell, blade, motor, flange_z_at(r)).
    """
    R = p.deck_housing_diameter / 2
    z0 = p.deck_shell_bottom_z
    z_skirt = z0 + 80
    z_top = z0 + p.deck_shell_height
    outer = [(0, z_top), (0.38 * R, z_top), (0.8 * R, z_top - 20), (R, z_skirt), (R, z0)]
    inner = [(R - SHELL_T, z0), (R - SHELL_T, z_skirt - 1), (0.8 * R - 1, z_top - 20 - SHELL_T),
             (0.38 * R - 1, z_top - SHELL_T), (0, z_top - SHELL_T)]
    profile = Plane.XZ * Polygon(*(outer + inner), align=None)
    shell = revolve(profile, Axis.Z)
    # Stiffening rib around the top and a mulching-plug boss.
    shell = shell.fuse(z_cylinder(0, 0, z_top - 2, 0.4 * R, 4) - z_cylinder(0, 0, z_top - 3, 0.4 * R - 6, 6))

    def flange_z(r):
        if r <= 0.38 * R:
            return z_top
        if r <= 0.8 * R:
            return z_top - 20 * (r - 0.38 * R) / (0.42 * R)
        return z_top - 20 - (z_top - 20 - z_skirt) * (r - 0.8 * R) / (0.2 * R)

    blade_z = z0 + 18
    blade = box(-p.deck_cut_width / 2, p.deck_cut_width / 2, -24, 24, blade_z, blade_z + 4)
    for s in (1, -1):  # lift wings at the blade tips
        blade = blade.fuse(box(s * (p.deck_cut_width / 2 - 60), s * p.deck_cut_width / 2, 14, 24,
                               blade_z + 4, blade_z + 16))
    blade = blade.fuse(z_cylinder(0, 0, blade_z, 22, 20))
    motor = z_cylinder(0, 0, z_top - 2, p.deck_motor_diameter / 2, p.deck_motor_height * 0.75 + 2)
    motor = motor.fuse(z_cylinder(0, 0, z_top + p.deck_motor_height * 0.75, p.deck_motor_diameter / 2 - 25,
                                  p.deck_motor_height * 0.25))
    for k in range(8):  # cooling ribs
        motor = motor.fuse(Rot(0, 0, k * 45) * box(p.deck_motor_diameter / 2 - 2, p.deck_motor_diameter / 2 + 4,
                                                    -3, 3, z_top + 10, z_top + p.deck_motor_height * 0.7))
    return shell, blade, motor, flange_z


def decks(p: Params, config: str) -> list[PartRecord]:
    parts = []
    shell_l, blade_l, motor_l, flange_z = deck_shell_local(p)
    R = p.deck_housing_diameter / 2
    for i, (x, y) in enumerate(p.deck_slots(config)):
        place = Pos(x, y, 0)
        name = f"mower_deck_{i + 1}"
        # Hanger tabs on the flange, as close to the neighbouring cross members as the deck allows.
        tabs = []
        hanger_rods = []
        attach_xs = []
        xs = sorted(p.cross_member_x)
        behind = max(m for m in xs if m <= x)
        ahead = min(m for m in xs if m > x)
        for mx in (behind, ahead):
            dx = max(-150.0, min(150.0, mx - x))
            for sy in (-1, 1):
                dy = sy * p.deck_hanger_spread
                r = (dx * dx + dy * dy) ** 0.5
                tz = flange_z(min(r, R - 10)) + 2
                tabs.append(box(x + dx - 15, x + dx + 15, y + dy - 12, y + dy + 12, tz - 6, tz + 6))
                x0, x1, ch = member_span(p, mx)
                top = (x + dx, y + dy, tz + 6)
                bottom_of_member = p.frame_top_z - ch
                anchor = ((x0 + x1) / 2, y + dy, bottom_of_member)
                hanger_rods.append(rod(top, (anchor[0], anchor[1], anchor[2] + 12), 4))  # M8 rod into a T-nut
                hanger_rods.append(box(anchor[0] - 12, anchor[0] + 12, anchor[1] - 10, anchor[1] + 10,
                                       bottom_of_member - 10, bottom_of_member))  # drop-in slot block
                hanger_rods.append(hex_nut((x + dx, y + dy, tz + 6), (0, 0, 1), af=13, height=6.5, bore=4))
                hanger_rods.append(hex_nut((x + dx, y + dy, tz - 6), (0, 0, -1), af=13, height=6.5, bore=4))
        shell = place * shell_l
        for t in tabs:
            shell = shell.fuse(t)
        parts.append(PartRecord(name, "deck", shell, p.deck_mass * 0.45,
                                meta={"center": (x, y),
                                      "motor_top_z": p.deck_shell_bottom_z + p.deck_shell_height + p.deck_motor_height}))
        parts.append(PartRecord(f"{name}_blade", "deck", place * blade_l, 0.8, material="steel"))
        parts.append(PartRecord(f"{name}_motor", "deck", place * motor_l, p.deck_mass * 0.5,
                                material="black_plastic",
                                meta={"center": (x, y),
                                      "motor_top_z": p.deck_shell_bottom_z + p.deck_shell_height + p.deck_motor_height}))
        # Anti-scalp rollers front and rear of the deck.
        rollers = []
        for sx in (1, -1):
            rx = x + sx * (R - 25)
            rollers.append(y_cylinder(rx, y, 42, 30, 44))
            rollers.append(box(rx - 8, rx + 8, y - 30, y + 30, 42, flange_z(R - 25) + 2))
            rollers.append(y_cylinder(rx, y, 42, 5, 70))
        parts.append(PartRecord(f"{name}_rollers", "deck", Compound(children=rollers),
                                2 * p.masses["roller"], material="black_plastic"))
        parts.append(PartRecord(f"{name}_hangers", "hanger", Compound(children=hanger_rods),
                                4 * p.masses["hanger"]))
    return parts
