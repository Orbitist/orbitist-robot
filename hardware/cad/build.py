"""Build the platform v1 model and regenerate every derived output.

Usage (from hardware/cad/):
    .venv/bin/python build.py

Writes to hardware/cad/exports/:
    platform-v1-<config>.step      full assembly (import into Onshape, FreeCAD, Fusion)
    platform-v1-<config>-*.png     iso / top / side renders
    *.dxf                          flat patterns for cutting (fork plate, torque arm, gusset, caster plate)
    cut-list.md                    extrusion cut list
    report.md                      envelope, mass, CG, axle loads, clearance checks
"""

import time
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from build123d import Align, Box, Color, Compound, Cylinder, ExportDXF, Pos, Unit, export_step
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from model import CONFIGS, assembly, bumper_layout
from params import Params
from parts import plates

OUT = Path(__file__).parent / "exports"


# ---------------------------------------------------------------- exports --
CHUNK = 160.0  # mm; big parts are drawn as spatial patches so matplotlib's depth sort works


def add_mesh(ax, tri, color, light, edge=True):
    """Add triangles to a 3D axis as several collections grouped by position, shaded by normal."""
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    shade = 0.45 + 0.55 * np.abs(n @ light)
    fc = np.clip(np.array(color)[None, :] * shade[:, None], 0, 1)
    cells = np.floor(tri.mean(axis=1) / CHUNK).astype(int)
    keys = cells[:, 0] * 1_000_000 + cells[:, 1] * 1_000 + cells[:, 2]
    for key in np.unique(keys):
        m = keys == key
        ax.add_collection3d(Poly3DCollection(tri[m], facecolors=fc[m], edgecolors=fc[m] if edge else "none",
                                             linewidths=0.1))

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
            add_mesh(ax, v[t], c, light)
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


DETAIL_VIEWS = {
    # name: (xmin, xmax, ymin, ymax, zmin, zmax, elev, azim)
    "detail-drive": (-230, 230, 430, 720, 0, 420, 22, -150),
    "detail-front-corner": (620, 1200, 260, 700, 0, 420, 24, 150),
    "detail-deck-hangers": (-320, 320, -560, 60, 0, 420, 18, -140),
    "detail-rear": (-460, -40, -600, 250, 250, 600, 26, 140),
    "detail-razor-deck": (120, 700, -600, 600, 0, 420, -24, -125),
    "detail-roof": (-360, 900, -700, 700, 350, 900, 30, -140),
}


def render_details(parts, path_prefix: Path):
    """Close-up renders of the fiddly regions: each part is clipped to the view box."""
    light = np.array([0.4, 0.3, 0.85])
    light /= np.linalg.norm(light)
    for name, (x0, x1, y0, y1, z0, z1, elev, azim) in DETAIL_VIEWS.items():
        clip = Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3)
        fig = plt.figure(figsize=(9, 7), dpi=130)
        ax = fig.add_subplot(projection="3d", proj_type="persp")
        for rec in parts:
            bb = rec.shape.bounding_box()
            if bb.max.X < x0 or bb.min.X > x1 or bb.max.Y < y0 or bb.min.Y > y1 or bb.max.Z < z0 or bb.min.Z > z1:
                continue
            inside = bb.min.X >= x0 and bb.max.X <= x1 and bb.min.Y >= y0 and bb.max.Y <= y1 and bb.min.Z >= z0 and bb.max.Z <= z1
            shape = rec.shape if inside else rec.shape.intersect(clip)
            if shape is None:
                continue
            shapes = list(shape) if isinstance(shape, (list, tuple)) else [shape]
            for sh in shapes:
                if sh.volume < 1e-3:
                    continue
                verts, tris = sh.tessellate(0.8, 0.2)
                if not tris:
                    continue
                v = np.array([(q.X, q.Y, q.Z) for q in verts])
                add_mesh(ax, v[np.array(tris)], rec.color, light)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_zlim(z0, z1)
        ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(name.replace("detail-", "").replace("-", " "))
        fig.tight_layout()
        fig.savefig(f"{path_prefix}-{name}.png")
        plt.close(fig)


def write_dxf(shape, path: Path):
    exp = ExportDXF(unit=Unit.MM)
    exp.add_layer("cut")
    exp.add_shape(shape, layer="cut")
    exp.write(str(path))


def flat_parts(p: Params) -> list[str]:
    """Export every cut plate from the same 2D outlines the 3D model is built from."""
    sk, w, h, _ = plates.fork_side_plate(p)
    write_dxf(sk, OUT / "drive-fork-side-plate.dxf")
    write_dxf(plates.torque_arm(p), OUT / "torque-arm.dxf")
    write_dxf(plates.gusset()[0], OUT / "frame-gusset.dxf")
    csk, cw, ch, _ = plates.caster_plate(p)
    write_dxf(csk, OUT / "caster-plate.dxf")
    dsk, r_pivot = plates.razor_disc(p)
    write_dxf(dsk, OUT / "razor-disc.dxf")
    spacer = p.frame_bottom_z - p.caster_mount_t - p.caster_height
    return [
        "## Flat parts",
        "",
        f"- `drive-fork-side-plate.dxf`: {w:.0f} × {h:.0f} mm, {p.fork_plate_t:.0f} mm steel, qty 4. The axle slot is "
        f"{p.axle_flats + 0.3:.1f} mm wide; **measure the motor's axle flats before cutting**.",
        "- `torque-arm.dxf`: 130 × 30 mm, 5 mm steel, qty 4 (one per fork plate). Double-D hole keyed to the axle "
        "flats; M6 holes match the fork plate. **Required** (see strength-report.md).",
        "- `frame-gusset.dxf`: 150 × 150 mm L-gusset, 5 mm aluminium or 3 mm steel, qty 8 (top of the "
        "rail-to-member joints at x = −120 and x = 215, both sides, both faces).",
        f"- `caster-plate.dxf`: {cw:.0f} × {ch:.0f} mm, {p.caster_mount_t:.0f} mm steel, qty 2 (mirror one). Caster holes "
        "drilled 6.8 mm and **tapped M8**; M6 clearance holes into the side rail and front member. Needs a "
        f"**{spacer:.0f} mm spacer** under each caster (if negative, lengthen the drive forks). "
        "**Measure the caster's bolt pattern and height before cutting.**",
        f"- `razor-disc.dxf`: Ø{2 * (r_pivot + 8):.0f} mm blade carrier, 3 mm aluminium, qty {len(p.razor_discs())}. Three M6 "
        f"shoulder-screw pivots on a {2 * r_pivot:.0f} mm circle for standard robot-mower razor blades; "
        "4 × M4 on a 25 mm circle for the motor hub (match to the motor bought in step 1).",
        "",
    ]


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
    cut_lo, cut_hi = p.cut_span(config)
    edge_r = cut_lo - bb.min.Y
    edge_l = bb.max.Y - cut_hi
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
        f"| Closest cut to an obstacle, right side / left side | {edge_r:.0f} mm / {edge_l:.0f} mm "
        "(cut edge to the robot's outermost part) |",
        f"| Pivot-turn swept radius (about axle centre) | {np.hypot(max(abs(bb.min.X), bb.max.X), max(abs(bb.min.Y), bb.max.Y)):.0f} mm |",
        "",
    ]


def overlap_volume(a, b) -> float:
    if not a.bounding_box().overlaps(b.bounding_box()):
        return 0.0
    common = a.intersect(b)
    if common is None:
        return 0.0
    if isinstance(common, (list, tuple)):  # compounds can return a ShapeList
        return sum(c.volume for c in common)
    return common.volume


def clearance_checks(p: Params, parts) -> list[str]:
    by_name = {r.name: r for r in parts}
    deck_parts = [r for r in parts if r.group == "deck"]
    deck_refs = [r for r in deck_parts if "center" in r.meta and (r.name.endswith("_motor") or r.name == "razor_deck_plate")]
    hard = [r for r in parts if r.group in ("frame", "fork", "drive", "caster", "bracket")]
    lines = ["| Check | Result |", "|---|---|"]
    problems = []
    for d in deck_parts:
        for h in hard:
            vol = overlap_volume(d.shape, h.shape)
            if vol > 1:
                problems.append(f"| {d.name} vs {h.name} | ❌ overlaps ({vol / 1000:.1f} cm³) |")
    lines += problems
    for side in ("L", "R"):
        c = by_name[f"caster_{side}"]
        sgn = 1 if side == "L" else -1
        sweep = Pos(p.caster_pivot_x, sgn * p.caster_pivot_y, 0) * Cylinder(
            c.meta["sweep_radius"], p.caster_wheel_diameter, align=(Align.CENTER, Align.CENTER, Align.MIN))
        worst = max((overlap_volume(d.shape, sweep) for d in deck_parts), default=0)
        for other in (r for r in parts if r.name.startswith("bumper_")):
            worst = max(worst, overlap_volume(other.shape, sweep))
        lines.append(f"| caster_{side} swivel sweep vs decks and bumper parts | "
                     + ("✅ clear" if worst < 1 else f"❌ overlaps ({worst / 1000:.0f} cm³)") + " |")
    names = sorted({r.name.rsplit("_", 1)[0] if not r.name.endswith(("deck_1", "deck_2")) else r.name
                    for r in deck_parts})
    lines.append(f"| decks (shell, blade, motor, rollers) vs frame, brackets, forks, wheels, casters | "
                 + ("✅ clear" if not problems else "❌ see above") + " |")
    for d in deck_refs:
        top = d.meta["motor_top_z"]
        lines.append(f"| {d.name} top (z={top:.0f}) vs frame top (z={p.frame_top_z:.0f}) | "
                     + ("pokes up through an open frame bay ✅" if top > p.frame_bottom_z else "below frame") + " |")
    # Top-mounted payload must clear the mower motors poking through the frame.
    for e in (r for r in parts if r.group == "electrical"):
        eb = e.shape.bounding_box()
        for d in deck_refs:
            (cx, cy), r = d.meta["center"], p.deck_motor_diameter / 2 + 5
            xy_overlap = eb.min.X < cx + r and cx - r < eb.max.X and eb.min.Y < cy + r and cy - r < eb.max.Y
            if xy_overlap and eb.min.Z - d.meta["motor_top_z"] < 30 and eb.min.Z < p.frame_top_z + 1:
                lines.append(f"| {e.name} vs {d.name} | ❌ less than 30 mm above the motor |")
    # Hangers must not pass through anything but the deck tab and the member.
    for hng in (r for r in parts if r.group == "hanger"):
        for h in (r for r in parts if r.group in ("electrical", "accessory", "fork", "drive", "caster")):
            vol = overlap_volume(hng.shape, h.shape)
            if vol > 1:
                lines.append(f"| {hng.name} vs {h.name} | ❌ overlaps ({vol / 1000:.0f} cm³) |")
    bar_rear = bumper_layout(p)[0]
    sweep_front = p.caster_pivot_x + p.caster_trail + p.caster_wheel_diameter / 2
    gap = bar_rear - p.bumper_travel - sweep_front
    lines.append(f"| Bumper at full travel vs caster swivel sweep | {gap:.0f} mm clear " + ("✅" if gap > 0 else "❌") + " |")
    # Uncut strip check for twin decks.
    if len(deck_refs) == 2 and all(r.name.startswith("mower_deck") for r in deck_refs):
        (x1, y1), (x2, y2) = (d.meta["center"] for d in deck_refs)
        overlap = p.deck_cut_width - abs(y2 - y1)
        lines.append(f"| Twin-deck cut overlap | {overlap:.0f} mm "
                     + ("✅" if overlap > 0 else "❌ uncut strip") + " |")
        lines.append(f"| Twin-deck total cut width | {abs(y2 - y1) + p.deck_cut_width:.0f} mm |")
    return lines + [""]


def main():
    import sys
    OUT.mkdir(exist_ok=True)
    p = Params()
    if "--details" in sys.argv:  # quick path while adjusting the close-up views
        render_details(assembly(p, "razor"), OUT / "platform-v1")
        return
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
        t1 = time.time()
        report += ["### Clearance checks", ""] + clearance_checks(p, parts)
        print(f"built {config} (clearance checks {time.time() - t1:.0f} s)")
    parts = assembly(p, "razor")
    render_details(parts, OUT / "platform-v1")
    report += flat_parts(p)
    (OUT / "cut-list.md").write_text(cut_list(p, parts))
    (OUT / "report.md").write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
