"""Build the platform v1 model and regenerate every derived output.

Usage (from hardware/cad/):
    .venv/bin/python build.py

Writes to hardware/cad/exports/:
    platform-v1-<config>.step      full assembly (import into Onshape, FreeCAD, Fusion)
    platform-v1-<config>-*.png     iso / top / side renders
    drive-fork-side-plate.dxf      flat patterns for cutting (+ torque-arm, frame-gusset)
    cut-list.md                    extrusion cut list
    report.md                      envelope, mass, CG, axle loads, clearance checks
"""

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from build123d import (
    Align,
    Circle,
    Color,
    Compound,
    Cylinder,
    ExportDXF,
    Polygon,
    Pos,
    Rectangle,
    SlotCenterPoint,
    Unit,
    export_step,
)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from model import assembly
from params import Params

OUT = Path(__file__).parent / "exports"
CONFIGS = ("single", "twin")


# ---------------------------------------------------------------- exports --
def export_assembly(parts, path: Path):
    children = []
    for rec in parts:
        shape = rec.shape
        shape.label = rec.name
        shape.color = Color(*rec.color)
        children.append(shape)
    export_step(Compound(children=children, label=path.stem), str(path))


def render(parts, path_prefix: Path, title: str):
    meshes = []
    for rec in parts:
        verts, tris = rec.shape.tessellate(2.0, 0.3)
        v = np.array([(q.X, q.Y, q.Z) for q in verts])
        meshes.append((v, np.array(tris), np.array(rec.color)))
    allv = np.vstack([m[0] for m in meshes])
    lo, hi = allv.min(axis=0), allv.max(axis=0)
    light = np.array([0.4, 0.3, 0.85])
    light /= np.linalg.norm(light)
    views = {"iso": (24, -135), "top": (90, -90), "side": (0, -90), "front": (0, 0)}
    for view, (elev, azim) in views.items():
        fig = plt.figure(figsize=(10, 7.5), dpi=130)
        ax = fig.add_subplot(projection="3d", proj_type="ortho" if view != "iso" else "persp")
        for v, t, c in meshes:
            tri = v[t]
            n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
            shade = 0.45 + 0.55 * np.abs(n @ light)
            fc = np.clip(c[None, :] * shade[:, None], 0, 1)
            ax.add_collection3d(Poly3DCollection(tri, facecolors=fc, edgecolors="none"))
        # Ground footprint outline.
        gx = [lo[0], hi[0], hi[0], lo[0], lo[0]]
        gy = [lo[1], lo[1], hi[1], hi[1], lo[1]]
        ax.plot(gx, gy, [0] * 5, color="0.6", lw=0.6, ls="--")
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_zlim(0, hi[2])
        ax.set_box_aspect(hi - np.array([lo[0], lo[1], 0]))
        ax.view_init(elev=elev, azim=azim)
        ax.set_xlabel("X forward (mm)")
        ax.set_ylabel("Y left (mm)")
        ax.set_zlabel("Z (mm)")
        if view == "top":
            ax.set_zticks([])
        ax.set_title(f"{title} — {view}")
        fig.tight_layout()
        fig.savefig(f"{path_prefix}-{view}.png")
        plt.close(fig)


def fork_plate_dxf(p: Params, rec, path: Path):
    """Dropout side plate: open slot from the bottom edge up to the axle centre."""
    h = rec.meta["plate_height"]
    w = p.fork_length_x
    axle_z = rec.meta["axle_z_in_plate"]
    slot_w = p.axle_flats + 0.3  # slip fit over the axle flats
    plate = Pos(0, h / 2) * Rectangle(w, h)
    # Slot: rounded top at the axle centre, open through the bottom edge.
    slot = SlotCenterPoint((0, axle_z / 2 - 1), (0, axle_z), slot_w)
    plate = plate - slot
    # Bolt holes along the top edge (M8 clearance) to fix the plate to the fork top plate.
    for x in (-70, 0, 70):
        plate = plate - Pos(x, h - 15) * Circle(4.5)
    # Torque-arm holes either side of the axle (M6).
    for x in (-50, 50):
        plate = plate - Pos(x, axle_z) * Circle(3.3)
    exp = ExportDXF(unit=Unit.MM)
    exp.add_layer("cut")
    exp.add_shape(plate, layer="cut")
    exp.write(str(path))
    return w, h


def write_dxf(shape, path: Path):
    exp = ExportDXF(unit=Unit.MM)
    exp.add_layer("cut")
    exp.add_shape(shape, layer="cut")
    exp.write(str(path))


def torque_arm_dxf(p: Params, path: Path):
    """Plate keyed to the axle flats, bolted to the fork plate's M6 holes at +/-50 mm."""
    arm = Rectangle(130, 30)
    # Double-D hole: 12 mm axle circle trimmed to the flats (+0.2 mm fit).
    double_d = Circle(6.1) & Rectangle(p.axle_flats + 0.2, 12.2)
    arm = arm - double_d
    for x in (-50, 50):
        arm = arm - Pos(x, 0) * Circle(3.3)
    write_dxf(arm, path)


def gusset_dxf(path: Path):
    """L-gusset for the top face of a side-rail / cross-member joint (30-series, M6)."""
    outline = Polygon((0, 0), (150, 0), (150, 30), (30, 150), (0, 150), align=None)
    for x in (60, 105, 135):  # leg over the side rail
        outline = outline - Pos(x, 15) * Circle(3.3)
    for y in (60, 105, 135):  # leg over the cross member
        outline = outline - Pos(15, y) * Circle(3.3)
    write_dxf(outline, path)


# ---------------------------------------------------------------- reports --
def cut_list(p: Params, parts) -> str:
    counts = Counter(
        (rec.extrusion["profile"], round(rec.extrusion["length"]))
        for rec in parts
        if rec.extrusion
    )
    lines = [
        "# Extrusion cut list: platform v1 frame",
        "",
        "*Generated by `build.py`; do not edit by hand. Same for single- and twin-deck builds.*",
        "",
        "| Profile | Length (mm) | Qty | Total (m) |",
        "|---|---|---|---|",
    ]
    total = Counter()
    for (prof, length), qty in sorted(counts.items()):
        lines.append(f"| {prof} | {length} | {qty} | {length * qty / 1000:.2f} |")
        total[prof] += length * qty
    lines.append("")
    lines.append("Buy (with ~10 % for cutting waste): " + ", ".join(
        f"{prof}: {v * 1.1 / 1000:.1f} m" for prof, v in sorted(total.items())))
    lines.append("")
    lines.append(f"Cross members fit **between** the side rails (frame width {p.frame_width:.0f} mm "
                 f"minus 2 × {p.side_rail[0]:.0f} mm), joined with corner brackets.")
    return "\n".join(lines) + "\n"


def mass_report(p: Params, parts, config: str) -> list[str]:
    bb = Compound(children=[r.shape for r in parts]).bounding_box()
    total = sum(r.mass for r in parts)
    cg = sum(np.array(tuple(r.shape.center())) * r.mass for r in parts) / total
    caster_contact_x = p.caster_pivot_x - p.caster_trail
    # Static beam: drive axle at x=0, casters at caster_contact_x.
    r_caster = total * cg[0] / caster_contact_x
    r_drive = total - r_caster
    hitch_x = p.frame_rear_x - 50  # hitch pin position
    return [
        f"## Configuration: {config} deck",
        "",
        "| Quantity | Value |",
        "|---|---|",
        f"| Overall length × width × height | {bb.size.X:.0f} × {bb.size.Y:.0f} × {bb.size.Z:.0f} mm |",
        f"| Estimated mass | {total:.1f} kg |",
        f"| Centre of gravity (x, y, z) | ({cg[0]:.0f}, {cg[1]:.0f}, {cg[2]:.0f}) mm |",
        f"| Load on drive wheels | {r_drive:.1f} kg ({100 * r_drive / total:.0f} %) |",
        f"| Load on casters | {r_caster:.1f} kg ({100 * r_caster / total:.0f} %) |",
        f"| Max cart tongue weight before casters unload | {total * cg[0] / abs(hitch_x):.0f} kg (hitch pin {abs(hitch_x):.0f} mm behind axle) |",
        f"| Pivot-turn swept radius (about axle centre) | {np.hypot(max(abs(bb.min.X), bb.max.X), max(abs(bb.min.Y), bb.max.Y)):.0f} mm |",
        "",
    ]


def overlap_volume(a, b) -> float:
    if not a.bounding_box().overlaps(b.bounding_box()):
        return 0.0
    common = a.intersect(b)
    return common.volume if common is not None else 0.0


def clearance_checks(p: Params, parts) -> list[str]:
    by_name = {r.name: r for r in parts}
    decks = [r for r in parts if r.group == "deck"]
    hard = [r for r in parts if r.group in ("frame", "fork", "drive", "caster")]
    lines = ["| Check | Result |", "|---|---|"]
    for d in decks:
        for h in hard:
            vol = overlap_volume(d.shape, h.shape)
            if vol > 1:
                lines.append(f"| {d.name} vs {h.name} | ❌ overlaps ({vol / 1000:.0f} cm³) |")
    # Caster swivel sweep: the wheel can swing anywhere within this radius.
    for side in ("L", "R"):
        c = by_name[f"caster_{side}"]
        sgn = 1 if side == "L" else -1
        sweep = Pos(p.caster_pivot_x, sgn * p.caster_pivot_y, 0) * Cylinder(
            c.meta["sweep_radius"], p.caster_wheel_diameter, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for d in decks:
            vol = overlap_volume(d.shape, sweep)
            lines.append(f"| caster_{side} swivel sweep vs {d.name} | "
                         + ("✅ clear" if vol < 1 else f"❌ overlaps ({vol / 1000:.0f} cm³)") + " |")
    for d in decks:
        clear = all(overlap_volume(d.shape, h.shape) <= 1 for h in hard)
        lines.append(f"| {d.name} vs frame, forks, wheels, casters | " + ("✅ clear" if clear else "❌ see above") + " |")
        top = d.meta["motor_top_z"]
        lines.append(f"| {d.name} motor top (z={top:.0f}) vs frame top (z={p.frame_top_z:.0f}) | "
                     + ("pokes up through an open frame bay ✅" if top > p.frame_bottom_z else "below frame") + " |")
    # Top-mounted payload must clear the mower motors poking through the frame.
    for e in (r for r in parts if r.group == "electrical"):
        eb = e.shape.bounding_box()
        for d in decks:
            (cx, cy), r = d.meta["center"], p.deck_motor_diameter / 2
            xy_overlap = eb.min.X < cx + r and cx - r < eb.max.X and eb.min.Y < cy + r and cy - r < eb.max.Y
            if xy_overlap and eb.min.Z - d.meta["motor_top_z"] < 30:
                lines.append(f"| {e.name} vs {d.name} motor | ❌ less than 30 mm above the motor |")
    # Uncut strip check for twin decks.
    if len(decks) == 2:
        (x1, y1), (x2, y2) = (d.meta["center"] for d in decks)
        overlap = p.deck_cut_width - abs(y2 - y1)
        lines.append(f"| Twin-deck cut overlap | {overlap:.0f} mm "
                     + ("✅" if overlap > 0 else "❌ uncut strip") + " |")
        lines.append(f"| Twin-deck total cut width | {abs(y2 - y1) + p.deck_cut_width:.0f} mm |")
    return lines + [""]


def main():
    OUT.mkdir(exist_ok=True)
    p = Params()
    report = [
        "# Platform v1 model report",
        "",
        "*Generated by `build.py`; do not edit by hand. Masses and many dimensions are ESTIMATES; see `params.py`.*",
        "",
    ]
    for config in CONFIGS:
        parts = assembly(p, config)
        export_assembly(parts, OUT / f"platform-v1-{config}.step")
        render(parts, OUT / f"platform-v1-{config}", f"Orbitist platform v1 ({config} deck)")
        report += mass_report(p, parts, config)
        report += ["### Clearance checks", ""] + clearance_checks(p, parts)
        print(f"built {config}")
    parts = assembly(p, "single")
    fork = next(r for r in parts if r.name == "drive_fork_L")
    w, h = fork_plate_dxf(p, fork, OUT / "drive-fork-side-plate.dxf")
    report += ["## Flat parts", "",
               f"- `drive-fork-side-plate.dxf`: {w:.0f} × {h:.0f} mm, {p.fork_plate_t:.0f} mm steel, qty 4. "
               f"The axle slot is {p.axle_flats + 0.3:.1f} mm wide; **measure the motor's axle flats before cutting**.",
               ""]
    torque_arm_dxf(p, OUT / "torque-arm.dxf")
    gusset_dxf(OUT / "frame-gusset.dxf")
    report += [f"- `torque-arm.dxf`: 130 × 30 mm, 5 mm steel, qty 4 (one per fork plate). Double-D hole keyed "
               f"to the axle flats; M6 holes match the fork plate. **Required** (see strength-report.md).",
               "- `frame-gusset.dxf`: 150 × 150 mm L-gusset, 5 mm aluminium or 3 mm steel, qty 8 (top of the "
               "rail-to-member joints at x = −120 and x = 215, both sides, plus spares for the rear corners).",
               ""]
    (OUT / "cut-list.md").write_text(cut_list(p, parts))
    (OUT / "report.md").write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
