"""Solar roof: four 30x30 posts, a 30x30 roof frame, two semi-flexible panels, the GNSS antenna
and the e-stop on the roof's rear rail (both reachable and in clear sky)."""

from build123d import Compound

from params import Params
from parts.common import PartRecord, box, extrusion_x, extrusion_y, extrusion_z, fasteners, hex_bolt, z_cylinder
from parts.payload import estop as estop_on_frame, rounded_box


def roof(p: Params) -> list[PartRecord]:
    parts = []
    m = p.masses
    zt = p.frame_top_z
    z0 = p.roof_z  # roof frame underside
    sw = 30.0
    x0, x1 = p.frame_rear_x, p.frame_front_x
    yo = p.frame_width / 2
    # Posts at the four corners, standing on the side rails.
    posts = []
    for px in (x0 + 15, x1 - 15):
        for sy in (-1, 1):
            posts.append(extrusion_z(px, sy * (yo - 15), zt, z0, sw))
    for i, post in enumerate(posts):
        parts.append(PartRecord(f"roof_post_{i + 1}", "frame", post, m["extrusion_30x30_per_m"] * p.roof_post_h / 1000,
                                extrusion={"profile": "30x30", "length": p.roof_post_h}))
    # Roof frame: two long rails (X) and two cross rails (Y) between them, flush on top.
    zc = z0 + sw / 2
    for sy in (-1, 1):
        parts.append(PartRecord(f"roof_rail_{'L' if sy > 0 else 'R'}", "frame",
                                extrusion_x(x0, x1, sy * (yo - 15), zc, sw, sw),
                                m["extrusion_30x30_per_m"] * (x1 - x0) / 1000,
                                extrusion={"profile": "30x30", "length": x1 - x0}))
    inner = p.frame_width - 2 * sw
    for name, xc in (("rear", x0 + 15), ("front", x1 - 15)):
        parts.append(PartRecord(f"roof_rail_{name}", "frame", extrusion_y(-inner / 2, inner / 2, xc, zc, sw, sw),
                                m["extrusion_30x30_per_m"] * inner / 1000,
                                extrusion={"profile": "30x30", "length": inner}))
    # Panels side by side across the width, on a thin backing sheet spanning the frame.
    px, py, pt = p.panel_size
    zpan = z0 + sw
    panels = []  # (a thin backing sheet under the panels is in the BOM; not modelled)
    gap = 20.0
    total_w = p.panel_count * py + (p.panel_count - 1) * gap
    xc = (x0 + x1) / 2
    for i in range(p.panel_count):
        yc = -total_w / 2 + py / 2 + i * (py + gap)
        panels.append(box(xc - px / 2, xc + px / 2, yc - py / 2, yc + py / 2, zpan, zpan + pt))
    parts.append(PartRecord("solar_panels", "electrical", Compound(children=panels), m["panel"] * p.panel_count,
                            material="solar"))
    # Corner brackets post→roof rail and post→side rail (bolts only, brackets are inside).
    bolts = []
    for px_ in (x0 + 15, x1 - 15):
        for sy in (-1, 1):
            bolts.append(hex_bolt((px_, sy * (yo - 30), zt + 20), (0, -sy, 0), 6, 14))
            bolts.append(hex_bolt((px_, sy * (yo - 30), z0 - 20), (0, -sy, 0), 6, 14))
    parts.append(fasteners("roof_bolts", bolts))
    # GNSS antenna on a stub on the rear roof rail; e-stop beside it.
    mx, my = p.mast_pos
    stub = z_cylinder(mx, my, z0 + sw, 12.5, p.antenna_stub_h) - z_cylinder(mx, my, z0 + sw, 10, p.antenna_stub_h + 1)
    plate = z_cylinder(mx, my, z0 + sw + p.antenna_stub_h - 3, 75, 3)
    puck = z_cylinder(mx, my, z0 + sw + p.antenna_stub_h, 45, 14)
    dome = z_cylinder(mx, my, z0 + sw + p.antenna_stub_h + 14, 36, 8).fuse(
        z_cylinder(mx, my, z0 + sw + p.antenna_stub_h + 22, 22, 6))
    parts.append(PartRecord("gnss_mast", "electrical", stub.fuse(plate), 0.4, material="aluminium"))
    parts.append(PartRecord("gnss_antenna", "electrical", puck.fuse(dome), m["mast_gnss"] - 0.4, material="white"))
    ex, ey = p.estop_pos
    base = rounded_box(ex - 36, ex + 36, ey - 36, ey + 36, z0 + sw, z0 + sw + 52, 6)
    button = z_cylinder(ex, ey, z0 + sw + 52, 20, 24).fuse(z_cylinder(ex, ey, z0 + sw + 76, 26, 10))
    parts.append(PartRecord("estop_base", "accessory", base, 0.25, material="yellow"))
    parts.append(PartRecord("estop_button", "accessory", button, 0.1, material="red"))
    # MPPT solar charge controller: small box on the electronics-box side.
    bx, by = p.ebox_pos
    mppt = box(bx - 60, bx + 60, by + p.ebox_size[1] / 2 + 20, by + p.ebox_size[1] / 2 + 60, zt + 10, zt + 110)
    parts.append(PartRecord("mppt_controller", "electrical", mppt, m["mppt"], material="grey_box"))
    return parts
