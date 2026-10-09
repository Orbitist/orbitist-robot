"""Plate-mount pneumatic swivel casters on steel corner plates."""

from build123d import Align, Box, Compound, Cylinder, Plane, Polygon, Pos, Rot, Torus, extrude

from params import Params
from parts.common import PartRecord, box, fasteners, hex_bolt, hex_nut, y_cylinder, z_cylinder
from parts.plates import caster_plate, caster_plate_extent


def caster_local(p: Params):
    """Caster with its pivot axis on local Z, trailing wheel toward -X, plate top at z=caster_height.

    Returns (tire, metal).
    """
    r = p.caster_wheel_diameter / 2
    w = p.caster_wheel_width
    top = p.caster_height
    cx, cy = p.caster_plate
    plate = box(-cx / 2, cx / 2, -cy / 2, cy / 2, top - 8, top)
    bx, by = p.caster_bolts
    for dx in (-bx / 2, bx / 2):
        for dy in (-by / 2, by / 2):
            plate = plate - z_cylinder(dx, dy, top - 9, 5.5, 10)
    race_z = top - 8 - 12
    raceway = z_cylinder(0, 0, race_z, 42, 12)
    balls = z_cylinder(0, 0, race_z + 3, 48, 6) - z_cylinder(0, 0, race_z + 2, 36, 8)
    yoke_z = race_z - 6
    yoke = z_cylinder(0, 0, yoke_z, 46, 6)
    # Two tapered legs from the yoke disc down to the axle, 6 mm plate, 10 mm clear of the tire.
    wx = -p.caster_trail
    leg_pts = [(40, yoke_z + 0.1), (wx - 45, yoke_z + 0.1), (wx - 28, r - 18), (wx + 28, r - 18)]
    legs = []
    for ly in (-(w / 2 + 10), w / 2 + 4):
        plane = Plane(origin=(0, ly, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        legs.append(extrude(plane * Polygon(*[(x, z) for x, z in leg_pts], align=None), 6))
    # Legs are drawn in the XZ plane; extrude along -Y by 6 from ly -> ly-6. Shift to ly..ly+6.
    legs = [Pos(0, 6, 0) * leg for leg in legs]
    axle = y_cylinder(wx, 0, r, 6, w + 44)
    nuts = [hex_nut((wx, w / 2 + 16, r), (0, 1, 0), af=19, height=8, bore=6.1),
            hex_nut((wx, -(w / 2 + 16), r), (0, -1, 0), af=19, height=8, bore=6.1)]
    hub = y_cylinder(wx, 0, r, 38, w - 10)
    hub_caps = y_cylinder(wx, 0, r, 22, w + 6)
    tire = Pos(wx, 0, r) * Rot(90, 0, 0) * (Torus(r - w / 2, w / 2) - Cylinder(r - w / 2 + 8, w + 2))
    metal = plate.fuse(raceway, balls, yoke, *legs, axle, hub, hub_caps, *nuts)
    return tire, metal


def casters(p: Params) -> list[PartRecord]:
    parts = []
    plate_top = p.frame_bottom_z
    plate_bot = plate_top - p.caster_mount_t
    spacer = plate_bot - p.caster_height
    tire_l, metal_l = caster_local(p)
    sk, w, h, holes = caster_plate(p)
    x0, x1, y_in, y_out = caster_plate_extent(p)
    for side, sgn in (("L", 1), ("R", -1)):
        px, py = p.caster_pivot_x, sgn * p.caster_pivot_y
        place = Pos(px, py, 0)
        parts.append(PartRecord(f"caster_tire_{side}", "caster", place * tire_l, 1.0, material="rubber"))
        metal = place * metal_l
        if spacer > 0.5:  # shim between the caster plate and the frame plate
            cx, cy = p.caster_plate
            metal = metal.fuse(box(px - cx / 2, px + cx / 2, py - cy / 2, py + cy / 2,
                                   p.caster_height, plate_bot))
        parts.append(PartRecord(f"caster_{side}", "caster", metal, p.masses["caster"] - 1.0,
                                meta={"sweep_radius": p.caster_trail + p.caster_wheel_diameter / 2,
                                      "spacer": spacer}))
        # Corner plate from the DXF outline, mirrored for the right side.
        plane = Plane(origin=(x0, y_in, plate_bot), x_dir=(1, 0, 0), z_dir=(0, 0, 1))
        plate = extrude(plane * sk, p.caster_mount_t)
        if sgn < 0:
            plate = plate.mirror(Plane.XZ)
        parts.append(PartRecord(f"caster_plate_{side}", "fork", plate, 0.9))
        bolts = []
        for hx, hy, r, kind in holes:
            gx, gy = x0 + hx, sgn * (y_in + hy)
            if kind == "caster":  # M8 up from below through the caster plate into the tapped plate
                bolts.append(hex_bolt((gx, gy, p.caster_height - 8), (0, 0, -1), 8, 16))
            else:  # M6 up into the rail / member bottom slot, head under the plate
                bolts.append(hex_bolt((gx, gy, plate_bot), (0, 0, -1), 6, 20))
        parts.append(fasteners(f"caster_bolts_{side}", bolts))
    return parts
