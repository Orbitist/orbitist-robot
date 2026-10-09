"""Shared building blocks: part records, colours, T-slot extrusion, fasteners, rods."""

from dataclasses import dataclass, field

from build123d import (
    Align,
    Box,
    Circle,
    Compound,
    Cylinder,
    Plane,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    Shape,
    Solid,
    extrude,
)

# Colours by material; a PartRecord can override its group colour with one of these.
MATERIAL = {
    "aluminium": (0.78, 0.80, 0.83),
    "steel": (0.45, 0.47, 0.50),
    "zinc": (0.62, 0.64, 0.66),
    "rubber": (0.12, 0.12, 0.13),
    "black_plastic": (0.20, 0.20, 0.22),
    "green_plastic": (0.24, 0.52, 0.28),
    "lime": (0.55, 0.75, 0.20),
    "blue_box": (0.22, 0.40, 0.72),
    "grey_box": (0.55, 0.58, 0.62),
    "yellow": (0.95, 0.80, 0.10),
    "red": (0.85, 0.15, 0.12),
    "foam": (0.30, 0.30, 0.32),
    "white": (0.92, 0.92, 0.90),
}

GROUP_COLORS = {
    "frame": MATERIAL["aluminium"],
    "bracket": MATERIAL["zinc"],
    "fastener": MATERIAL["zinc"],
    "drive": MATERIAL["black_plastic"],
    "fork": MATERIAL["steel"],
    "caster": MATERIAL["zinc"],
    "deck": MATERIAL["green_plastic"],
    "hanger": MATERIAL["zinc"],
    "electrical": MATERIAL["blue_box"],
    "accessory": MATERIAL["red"],
}


@dataclass
class PartRecord:
    name: str
    group: str
    shape: Shape
    mass: float
    extrusion: dict | None = None  # {"profile": "30x30", "length": mm}
    meta: dict = field(default_factory=dict)
    material: str | None = None  # overrides the group colour

    @property
    def color(self):
        return MATERIAL[self.material] if self.material else GROUP_COLORS[self.group]


# ------------------------------------------------------------- primitives --
def box(x0, x1, y0, y1, z0, z1) -> Shape:
    """Axis-aligned box from min/max corners (any order per axis)."""
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3)


def y_cylinder(x, y, z, radius, width) -> Shape:
    """Cylinder whose axis runs along Y, centred at (x, y, z)."""
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, width)


def z_cylinder(x, y, z0, radius, height) -> Shape:
    """Vertical cylinder standing on z0."""
    return Pos(x, y, z0) * Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def rod(p0, p1, radius) -> Shape:
    """Cylinder from point p0 to point p1."""
    d = tuple(b - a for a, b in zip(p0, p1))
    length = sum(c * c for c in d) ** 0.5
    return Solid.make_cylinder(radius, length, Plane(origin=p0, z_dir=d))


def hex_nut(origin, z_dir, af=10.0, height=5.0, bore=3.0) -> Shape:
    """Hex nut sitting on the plane through origin with normal z_dir."""
    plane = Plane(origin=origin, z_dir=z_dir)
    nut = extrude(plane * RegularPolygon(af / (3 ** 0.5), 6), height)
    return nut - Solid.make_cylinder(bore, height, plane)


def hex_bolt(origin, z_dir, d=6.0, shank=12.0) -> Shape:
    """Hex-head bolt: head sits on the surface at origin (normal z_dir), shank goes into it."""
    af = {5: 8.0, 6: 10.0, 8: 13.0, 10: 17.0, 12: 19.0}.get(d, 1.6 * d)
    head_h = 0.65 * d
    plane = Plane(origin=origin, z_dir=z_dir)
    head = extrude(plane * RegularPolygon(af / (3 ** 0.5), 6), head_h)
    back = Plane(origin=origin, z_dir=tuple(-c for c in z_dir))
    return head.fuse(Solid.make_cylinder(d / 2, shank, back))


def fasteners(name, bolts, mass_each=0.012) -> PartRecord:
    """Many small solids as one compound record (keeps the STEP tree sane)."""
    return PartRecord(name, "fastener", Compound(children=list(bolts)), mass_each * len(bolts))


# ---------------------------------------------------------- T-slot profile --
# 30-series, slot 8 ("B-type"): typical catalog geometry, see the datasheet of the
# extrusion actually bought and update here if it differs.
SLOT_OPEN = 8.2  # slot opening at the face
SLOT_LIP = 2.0  # lip thickness from face to cavity
CAVITY_W = 16.5  # cavity width behind the lips
CAVITY_D = 5.5  # cavity depth
CORE_BORE = 6.8  # centre bore (M8 tap)
CHAMFER = 1.5


def tslot_sketch(w: float, h: float):
    """Cross-section of a w x h T-slot extrusion with a slot every 30 mm on each face."""
    sk = Rectangle(w, h)
    for c in ((w / 2, h / 2), (-w / 2, h / 2), (w / 2, -h / 2), (-w / 2, -h / 2)):
        sk = sk - Pos(*c) * Rot(0, 0, 45) * Rectangle(CHAMFER * 2 ** 0.5, CHAMFER * 2 ** 0.5)
    slots = []
    for i in range(int(round(w / 30))):  # slots on the top/bottom (±h/2) faces
        x = -w / 2 + 15 + 30 * i
        for s in (1, -1):
            slots.append(Pos(x, s * (h / 2 - SLOT_LIP / 2)) * Rectangle(SLOT_OPEN, SLOT_LIP + 0.01))
            slots.append(Pos(x, s * (h / 2 - SLOT_LIP - CAVITY_D / 2)) * Rectangle(CAVITY_W, CAVITY_D))
    for j in range(int(round(h / 30))):  # slots on the side (±w/2) faces
        y = -h / 2 + 15 + 30 * j
        for s in (1, -1):
            slots.append(Pos(s * (w / 2 - SLOT_LIP / 2), y) * Rectangle(SLOT_LIP + 0.01, SLOT_OPEN))
            slots.append(Pos(s * (w / 2 - SLOT_LIP - CAVITY_D / 2), y) * Rectangle(CAVITY_D, CAVITY_W))
    for i in range(int(round(w / 30))):
        for j in range(int(round(h / 30))):
            slots.append(Pos(-w / 2 + 15 + 30 * i, -h / 2 + 15 + 30 * j) * Circle(CORE_BORE / 2))
    for s in slots:
        sk = sk - s
    return sk


_PROFILE_CACHE = {}


def extrusion_x(x0, x1, yc, zc, w, h) -> Shape:
    """T-slot bar along X from x0 to x1, section w (Y) x h (Z), centred at (yc, zc)."""
    key = (w, h)
    if key not in _PROFILE_CACHE:
        _PROFILE_CACHE[key] = tslot_sketch(w, h)
    # Sketch is in XY; extrude along +Z then rotate so local Z -> +X, local X -> Y, local Y -> Z.
    bar = extrude(_PROFILE_CACHE[key], x1 - x0)
    return Pos(x0, yc, zc) * Rot(0, 90, 0) * Rot(0, 0, 90) * bar


def extrusion_y(y0, y1, xc, zc, w, h) -> Shape:
    """T-slot bar along Y from y0 to y1, section w (X) x h (Z)."""
    key = (w, h)
    if key not in _PROFILE_CACHE:
        _PROFILE_CACHE[key] = tslot_sketch(w, h)
    bar = extrude(_PROFILE_CACHE[key], y1 - y0)
    return Pos(xc, y0, zc) * Rot(-90, 0, 0) * bar
