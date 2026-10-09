"""Coverage planner: lawn zones -> ArduPilot missions, geofence, and a coverage report.

Usage:
    .venv/bin/python coverage.py lawns/sample-farm.json            # plan every zone
    .venv/bin/python coverage.py lawns/sample-farm.json --zone east

Per zone it writes to plans/<lawn>/:
    <zone>.waypoints   Mission Planner mission (one zone = one day's job)
    <zone>.plan        QGroundControl plan: the same mission plus the geofence
    <zone>.png         map of the plan: path, cut area, missed area
and plans/<lawn>/report.md with mowing time, path length, and coverage per zone.

Pattern (the deck is offset to the robot's right):
    1. Perimeter lap(s), driven so the deck faces the boundary: counter-clockwise around
       the outside, clockwise around trees and beds. Cuts to ~0.19 m from the boundary.
    2. Back-and-forth stripes over the rest, at the angle that needs the fewest turns.
The whole robot body stays inside the lawn; the blade is switched with
DO_SEND_SCRIPT_MESSAGE, which only scripts/blade_interlock.lua acts on.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import substring, unary_union

SIM = Path(__file__).parent
sys.path.insert(0, str(SIM.parent.parent / "hardware" / "cad"))
from params import Params  # noqa: E402  (robot geometry comes from the CAD parameters)

PIVOT_OVERHEAD_S = 5.0  # stop + settle + restart per pivot, calibrated against a SITL run (run_sitl.py)
MAV_CMD_NAV_WAYPOINT = 16
MAV_CMD_DO_CHANGE_SPEED = 178
MAV_CMD_DO_SEND_SCRIPT_MESSAGE = 217
MAV_FRAME_GLOBAL = 0
MAV_FRAME_GLOBAL_RELATIVE_ALT = 3
BLADE_MSG_ID = 1


class Robot:
    """Robot geometry relevant to coverage, derived from hardware/cad/params.py."""

    # overlap 0.15 m: SITL tracking (p95 ~0.14 m) left strips uncut at 0.075. Revisit once the real
    # robot's tracking is measured; 0.10 is likely with RTK + tuned steering.
    def __init__(self, config="razor", overlap=0.15, speed=0.6, pivot_rate=45.0, obstacle_clearance=0.25):
        p = Params()
        # Lateral extent of the cut relative to the robot centreline (left positive).
        lo, hi = p.cut_span(config)
        self.cut_right, self.cut_left = lo / 1000, hi / 1000
        self.cut_width = self.cut_left - self.cut_right
        self.cut_centre = (self.cut_left + self.cut_right) / 2  # negative = right of centreline
        outer_fork = p.side_rail_y + p.dropout_spacing / 2 + p.fork_plate_t
        self.body_half_width = outer_fork / 1000  # outermost part (drive fork plate)
        self.half_width = self.body_half_width + 0.05  # + 5 cm tracking margin at lawn edges
        # Trees and beds are hard obstacles: keep extra room so corner-cutting on curved laps
        # can't bring the body into them (the fence stops the robot first).
        self.obstacle_clearance = obstacle_clearance
        self.min_leg = 0.3  # m; shorter legs are merged (see merge_short_legs)
        self.spacing = self.cut_width - overlap
        self.speed = speed
        self.pivot_rate = pivot_rate
        self.config = config


# ------------------------------------------------------------------ geometry --
def circle(x, y, r, n=24):
    return Polygon([(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n))
                    for i in range(n)])


def exclusion_shape(e):
    return circle(*e["circle"]) if "circle" in e else Polygon(e["polygon"])


def parts(geom):
    if geom.is_empty:
        return []
    return list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]


def cut_of_path(coords, robot: Robot):
    """Area cut while driving the path with the blade on."""
    if len(coords) < 2:
        return Polygon()
    line = LineString(coords)
    centre = line.offset_curve(robot.cut_centre) if abs(robot.cut_centre) > 1e-6 else line
    return centre.buffer(robot.cut_width / 2, cap_style="flat", join_style="round")


def cut_of_track(points, blade_flags, robot: Robot):
    """Area cut along a driven/planned track: consecutive blade-on legs form continuous runs,
    each swept as one polyline (round joins), so heading changes don't leave artificial wedges."""
    runs, cur, heading = [], [], None
    for i in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        if math.hypot(x1 - x0, y1 - y0) < 0.005:
            continue  # stationary sample (pivoting in place)
        h = math.atan2(y1 - y0, x1 - x0)
        # A pivot (sharp heading change) starts a new run: offsetting a path that doubles back
        # on itself is meaningless, and the robot sweeps nothing new while pivoting.
        sharp = heading is not None and abs((h - heading + math.pi) % (2 * math.pi) - math.pi) > math.radians(45)
        heading = h
        if blade_flags[i] and not sharp:
            if not cur:
                cur = [points[i]]
            cur.append(points[i + 1])
        else:
            if cur:
                runs.append(cur)
            cur = [points[i], points[i + 1]] if blade_flags[i] else []
    if cur:
        runs.append(cur)
    shapes = []
    for run in runs:
        line = LineString(run).simplify(0.01)
        if line.length > 0:
            shapes.append(cut_of_path(list(line.coords), robot))
    return unary_union(shapes) if shapes else Polygon()


def ring_path(ring_coords, start_pt):
    """Rotate a closed ring so it starts at the vertex nearest start_pt."""
    pts = list(ring_coords)[:-1]
    i = min(range(len(pts)), key=lambda k: Point(pts[k]).distance(Point(start_pt)))
    pts = pts[i:] + pts[:i]
    return pts + [pts[0]]


class Router:
    """Shortest routes that stay inside a region (polygon with holes), via a visibility graph.

    Built once per zone. Graph nodes are the region's ring vertices; an edge
    exists where the straight segment stays inside the region. Replaces an earlier ring-following
    connector that fell back to a straight line between different rings, which drove through a
    tree in the sample farm.
    """

    def __init__(self, region):
        self.region = region
        self.inside = region.buffer(1e-3)
        nodes = []
        for poly in parts(region):  # exact vertices: a point on a ring must see its neighbours
            for ring in [poly.exterior, *poly.interiors]:
                nodes.extend(list(ring.coords)[:-1])
        self.nodes = nodes
        self.adj = {i: [] for i in range(len(nodes))}
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if self.visible(nodes[i], nodes[j]):
                    d = math.dist(nodes[i], nodes[j])
                    self.adj[i].append((j, d))
                    self.adj[j].append((i, d))

    def visible(self, a, b):
        return LineString([a, b]).within(self.inside)

    def route(self, a, b):
        """Waypoints after a, ending at b."""
        if self.visible(a, b):
            return [b]
        import heapq
        start, goal = -1, -2
        dist = {start: 0.0}
        prev = {}
        heap = [(0.0, start)]
        done = set()
        while heap:
            d, u = heapq.heappop(heap)
            if u in done:
                continue
            done.add(u)
            if u == goal:
                break
            pu = a if u == start else self.nodes[u]
            neighbours = self.adj.get(u, []) if u >= 0 else \
                [(j, math.dist(a, n)) for j, n in enumerate(self.nodes) if self.visible(a, n)]
            if u >= 0 and self.visible(pu, b) or (u == start and self.visible(a, b)):
                neighbours = neighbours + [(goal, math.dist(pu, b))]
            for v, w in neighbours:
                if d + w < dist.get(v, float("inf")):
                    dist[v] = d + w
                    prev[v] = u
                    heapq.heappush(heap, (d + w, v))
        if goal not in prev:
            raise ValueError(f"no route inside the drivable area from {a} to {b}")
        out, u = [], goal
        while u != start:
            out.append(b if u == goal else self.nodes[u])
            u = prev[u]
        return out[::-1]


def stripes(remaining, drive, robot: Robot, angle):
    """Back-and-forth robot-centre segments covering `remaining`, stripes along `angle` (deg)."""
    rem = affinity.rotate(remaining, -angle, origin=(0, 0))
    drv = affinity.rotate(drive, -angle, origin=(0, 0))
    if rem.is_empty:
        return []
    minx, miny, maxx, maxy = drv.bounds
    rminy, rmaxy = rem.bounds[1], rem.bounds[3]
    segs = []
    y_cut = rminy + robot.cut_width / 2 - 0.02
    i = 0
    while y_cut - robot.cut_width / 2 < rmaxy:
        direction = 1 if i % 2 == 0 else -1
        # Driving +x the robot's right is -y, so the cut centre sits at robot_y + cut_centre.
        robot_y = y_cut - direction * robot.cut_centre
        strip = Polygon([(minx - 1, y_cut - robot.cut_width / 2), (maxx + 1, y_cut - robot.cut_width / 2),
                         (maxx + 1, y_cut + robot.cut_width / 2), (minx - 1, y_cut + robot.cut_width / 2)])
        if strip.intersection(rem).area > 0.2:
            hit = LineString([(minx - 1, robot_y), (maxx + 1, robot_y)]).intersection(drv)
            pieces = [g for g in getattr(hit, "geoms", [hit]) if isinstance(g, LineString) and g.length > 0.3]
            pieces.sort(key=lambda g: g.bounds[0], reverse=direction < 0)
            for g in pieces:
                c = list(g.coords)
                if (c[-1][0] - c[0][0]) * direction < 0:
                    c = c[::-1]
                segs.append([affinity.rotate(Point(pt), angle, origin=(0, 0)).coords[0] for pt in c])
            i += 1
        y_cut += robot.spacing
    return segs


def best_angle(remaining, drive, robot):
    best = None
    for angle in range(0, 180, 5):
        segs = stripes(remaining, drive, robot, angle)
        score = len(segs)
        if best is None or score < best[0]:
            best = (score, angle, segs)
    return best[1], best[2]


# ------------------------------------------------------------------ planning --
def plan_zone(zone, robot: Robot, laps: int = 2):
    boundary = Polygon(zone["boundary"])
    excl = unary_union([exclusion_shape(e) for e in zone.get("exclusions", [])]) \
        if zone.get("exclusions") else Polygon()
    lawn = boundary.difference(excl)
    # Robot-centre region. Curves get enough vertices that each heading change stays well under
    # WP_PIVOT_ANGLE (smooth, accurate tracking) without bloating the mission.
    drive = boundary.buffer(-robot.half_width, join_style="mitre")
    if not excl.is_empty:
        drive = drive.difference(excl.buffer(robot.half_width + robot.obstacle_clearance, quad_segs=6))
    drive = drive.simplify(0.02)
    start = zone["approach"][-1]

    path, blade = [list(start)], []  # blade[i] = blade state on segment path[i] -> path[i+1]
    mow_paths = []
    router = Router(drive)

    def connect(a, b, _region=None):
        return router.route(a, b)

    def go(points, blade_on):
        for pt in points:
            path.append(list(pt))
            blade.append(blade_on)

    # 1. Perimeter laps, deck facing the boundary. Lap k runs k pass-spacings further in;
    #    the second lap mows the triangles that stripes leave along slanted edges.
    for k in range(laps):
        ring_region = drive if k == 0 else drive.buffer(-k * robot.spacing, quad_segs=6).simplify(0.02)
        for poly in sorted(parts(ring_region), key=lambda g: g.distance(Point(path[-1]))):
            poly = orient(poly, 1.0)  # exterior CCW, holes CW: boundary always on the right
            for ring in [poly.exterior, *poly.interiors]:
                lap = ring_path(ring.coords, path[-1])
                go(connect(path[-1], lap[0], drive), False)
                go(lap[1:], True)
                mow_paths.append(lap)
    perimeter_cut = unary_union([cut_of_path(m, robot) for m in mow_paths])

    # 2. Stripes over what the perimeter laps didn't cut.
    remaining = lawn.difference(perimeter_cut)
    angle, segs = best_angle(remaining, drive, robot)
    for seg in segs:
        hop = connect(path[-1], seg[0], drive)
        hop_len = LineString([path[-1], *hop]).length if hop else 0
        go(hop, hop_len < 2.0)  # short hops between stripes mow; longer transits run blade-off
        go(seg[1:], True)

    # 3. Back to the zone entry.
    go(connect(path[-1], start, drive), False)
    path, blade = merge_short_legs(path, blade, robot.min_leg)

    # Coverage from every blade-on leg.
    cut = cut_of_track(path, blade, robot).intersection(lawn)
    missed = lawn.difference(cut)
    stats = path_stats(path, blade, robot)
    stats.update(area=lawn.area, covered=cut.area, missed=missed.area, angle=angle, stripes=len(segs))
    return dict(path=path, blade=blade, lawn=lawn, drive=drive, cut=cut, missed=missed, stats=stats,
                boundary=boundary, excl=excl)


def merge_short_legs(path, blade, min_leg):
    """Merge waypoints closer than min_leg into one.

    Tiny legs make ArduPilot hunt: the bearing to a point a few cm away flips with GPS noise,
    and the robot pivots back and forth (found in SITL). With the deck offset to the right, every
    stripe end produces a ~2.5 cm hop to the next stripe; merging it leaves a single waypoint
    where the robot pivots 180 degrees in place.

    Of two close points, keep the one at the end of the longer *mowing* leg: that's the point
    defining a stripe's straight line. Keeping a nearby transit point instead slants the whole
    stripe and leaves a wedge uncut (found in the sample-farm plan).
    """
    n = len(path)

    def score(k):
        legs = []
        if k > 0:
            legs.append(math.dist(path[k - 1], path[k]) * (1.0 if blade[k - 1] else 0.1))
        if k + 1 < n:
            legs.append(math.dist(path[k], path[k + 1]) * (1.0 if blade[k] else 0.1))
        return max(legs, default=0.0)

    out, flags = [path[0]], []
    out_idx = [0]
    for i in range(1, n):
        last = i == n - 1
        if math.dist(path[i], out[-1]) < min_leg and not last and len(out) > 1:
            if score(i) > score(out_idx[-1]):
                out[-1] = path[i]  # keep the point that starts the long leg
                out_idx[-1] = i
            flags[-1] = flags[-1] or blade[i - 1]
            continue
        out.append(path[i])
        out_idx.append(i)
        flags.append(blade[i - 1])
    return out, flags


def path_stats(path, blade, robot):
    dist_on = dist_off = 0.0
    turn_time = 0.0
    prev_heading = None
    for i in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        d = math.hypot(x1 - x0, y1 - y0)
        if d < 1e-6:
            continue
        if blade[i]:
            dist_on += d
        else:
            dist_off += d
        heading = math.degrees(math.atan2(y1 - y0, x1 - x0))
        if prev_heading is not None:
            dh = abs((heading - prev_heading + 180) % 360 - 180)
            if dh > 30:  # WP_PIVOT_ANGLE: stop and pivot
                turn_time += dh / robot.pivot_rate + PIVOT_OVERHEAD_S
        prev_heading = heading
    drive_time = (dist_on + dist_off) / robot.speed
    return dict(dist_on=dist_on, dist_off=dist_off, hours=(drive_time + turn_time) / 3600,
                turn_hours=turn_time / 3600, waypoints=len(path))


# ------------------------------------------------------------------ outputs --
class LocalFrame:
    """Flat-earth conversion around the lawn origin (fine at farm scale)."""

    def __init__(self, origin):
        self.lat0, self.lon0, self.alt = origin["lat"], origin["lon"], origin["alt"]
        self.k_lat = 111_320.0
        self.k_lon = 111_320.0 * math.cos(math.radians(self.lat0))

    def ll(self, x, y):
        return self.lat0 + y / self.k_lat, self.lon0 + x / self.k_lon


def mission_items(plan, zone, frame: LocalFrame, robot: Robot):
    """ArduPilot mission: home, speed, approach, mowing (blade via script message), return."""
    items = []
    lat, lon = frame.ll(*zone["approach"][0])
    items.append(dict(command=MAV_CMD_NAV_WAYPOINT, frame=MAV_FRAME_GLOBAL, params=[0, 0, 0, 0],
                      x=lat, y=lon, z=frame.alt))  # item 0 = home
    items.append(dict(command=MAV_CMD_DO_CHANGE_SPEED, frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
                      params=[1, robot.speed, -1, 0], x=0, y=0, z=0))

    def wp(pt):
        la, lo = frame.ll(*pt)
        items.append(dict(command=MAV_CMD_NAV_WAYPOINT, frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
                          params=[0, 0, 0, 0], x=la, y=lo, z=0))

    def blade(on):
        items.append(dict(command=MAV_CMD_DO_SEND_SCRIPT_MESSAGE, frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
                          params=[BLADE_MSG_ID, 1 if on else 0, 0, 0], x=0, y=0, z=0))

    for pt in zone["approach"][1:]:
        wp(pt)
    state = False
    path, flags = plan["path"], plan["blade"]
    for i in range(1, len(path)):
        if flags[i - 1] != state:
            # A DO command runs when the previous waypoint is reached: switch at the leg's start.
            blade(flags[i - 1])
            state = flags[i - 1]
        wp(path[i])
    if state:
        blade(False)
    for pt in reversed(zone["approach"][:-1]):
        wp(pt)
    return items


FENCE_POINT_BUDGET = 80  # ArduPilot's internal fence storage holds 84 points (BRD_SD_FENCE adds more on hardware)


def circumscribed_ngon(cx, cy, radius, max_excess=0.1):
    """Regular polygon containing the circle, with corners at most max_excess beyond it."""
    n = max(6, math.ceil(math.pi / math.acos(radius / (radius + max_excess))))
    r = radius / math.cos(math.pi / n)
    return Polygon([(cx + r * math.cos(2 * math.pi * (k + 0.5) / n), cy + r * math.sin(2 * math.pi * (k + 0.5) / n))
                    for k in range(n)])


def fence_polygons(lawn_def, zone_plans, frame: LocalFrame, robot: Robot, tol=0.3):
    """Inclusion: each zone's drivable area (robot centre) + tol, plus paths.
    Exclusion: trees and beds grown by the body half-width, i.e. the robot centre may not come
    closer than the point where its body would touch them. Laps keep obstacle_clearance + 5 cm
    more than that, so normal tracking never breaches.

    Every simplification is conservative (exclusions only grow) and the total stays within
    FENCE_POINT_BUDGET, found when a full-size zone's fence was rejected in SITL."""
    excl = []
    for zone in lawn_def["zones"]:
        if zone["name"] not in zone_plans:
            continue
        for e in zone.get("exclusions", []):
            if "circle" in e:
                cx, cy, r = e["circle"]
                excl.append(circumscribed_ngon(cx, cy, r + robot.body_half_width))
            else:
                # Rounded corners like the laps (a mitred corner would stick out ~0.3 m past the
                # body-contact line and the lap rounds the corner right next to it: found in SITL).
                # An 8-sided corner arc lies inside the true circle by r(1 - cos 22.5°), so grow r to cover it.
                r = robot.body_half_width / math.cos(math.pi / 8)
                excl.append(Polygon(e["polygon"]).buffer(r, quad_segs=2))
    n_excl = sum(len(p.exterior.coords) - 1 for p in excl)
    incl_raw = unary_union([z["drive"].buffer(tol, join_style="mitre") for z in zone_plans.values()]
                           + [Polygon(p["polygon"]) for p in lawn_def.get("paths", [])])
    for simp in (0.02, 0.05, 0.1, 0.15, 0.2):
        # Simplify, then grow by the same amount so the fence never cuts inside the laps.
        merged = incl_raw.simplify(simp).buffer(simp, join_style="mitre", mitre_limit=2.0)
        if n_excl + sum(len(p.exterior.coords) - 1 for p in parts(merged)) <= FENCE_POINT_BUDGET:
            break
    else:
        raise ValueError("fence needs more than %d points: split the lawn file or enable BRD_SD_FENCE"
                         % FENCE_POINT_BUDGET)

    def to_ll(poly):
        return [list(frame.ll(x, y)) for x, y in list(poly.exterior.coords)[:-1]]

    return [to_ll(p) for p in parts(merged)], [to_ll(p) for p in excl]


def write_waypoints(items, path: Path):
    lines = ["QGC WPL 110"]
    for i, it in enumerate(items):
        p = it["params"]
        lines.append("\t".join(str(v) for v in [i, 1 if i == 0 else 0, it["frame"], it["command"],
                                                 *p, f"{it['x']:.8f}", f"{it['y']:.8f}", f"{it['z']:.2f}", 1]))
    path.write_text("\n".join(lines) + "\n")


def write_qgc_plan(items, incl, excl, frame: LocalFrame, robot: Robot, path: Path):
    plan = {
        "fileType": "Plan", "version": 1, "groundStation": "QGroundControl",
        "mission": {
            "version": 2, "firmwareType": 3, "vehicleType": 10,
            "cruiseSpeed": robot.speed, "hoverSpeed": robot.speed,
            "plannedHomePosition": [items[0]["x"], items[0]["y"], frame.alt],
            "items": [{"type": "SimpleItem", "autoContinue": True, "command": it["command"],
                       "doJumpId": i, "frame": it["frame"],
                       "params": [*it["params"], it["x"], it["y"], it["z"]]}
                      for i, it in enumerate(items[1:], start=1)],
        },
        "geoFence": {"version": 2, "circles": [],
                     "polygons": [{"inclusion": True, "polygon": p, "version": 1} for p in incl]
                     + [{"inclusion": False, "polygon": p, "version": 1} for p in excl]},
        "rallyPoints": {"version": 2, "points": []},
    }
    path.write_text(json.dumps(plan, indent=1))


def plot(plan, zone, path: Path):
    fig, ax = plt.subplots(figsize=(8, 8), dpi=110)

    def fill(geom, **kw):
        for g in parts(geom):
            ax.fill(*g.exterior.xy, **kw)
            for h in g.interiors:
                ax.fill(*h.xy, color="white")

    fill(plan["lawn"], color="#dfe9d8")
    fill(plan["cut"], color="#7fb069", alpha=0.8)
    fill(plan["missed"], color="#d1495b", alpha=0.9)
    for g in parts(plan["excl"]):
        ax.fill(*g.exterior.xy, color="#6b4f3a")
    xs, ys = zip(*plan["path"])
    ax.plot(xs, ys, color="#1d3557", lw=0.5)
    ax.plot(*plan["path"][0], "ko")
    s = plan["stats"]
    ax.set_title(f"{zone['name']}: {s['covered'] / s['area']:.1%} cut, {s['hours']:.1f} h at "
                 f"0.6 m/s, missed (red) {s['missed']:.0f} m²")
    ax.set_aspect("equal")
    ax.set_xlabel("m east")
    ax.set_ylabel("m north")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lawn", type=Path)
    ap.add_argument("--zone", help="plan only this zone")
    ap.add_argument("--config", default="razor", choices=["razor", "single", "twin"])
    ap.add_argument("--laps", type=int, default=2, help="perimeter laps before striping")
    ap.add_argument("--out", type=Path, help="output directory (default plans/<lawn name>)")
    args = ap.parse_args()

    lawn_def = json.loads(args.lawn.read_text())
    robot = Robot(args.config)
    frame = LocalFrame(lawn_def["origin"])
    out = args.out or SIM / "plans" / f"{args.lawn.stem}-{args.config}"
    out.mkdir(parents=True, exist_ok=True)

    zones = [z for z in lawn_def["zones"] if args.zone in (None, z["name"])]
    plans = {z["name"]: plan_zone(z, robot, args.laps) for z in zones}

    rows = []
    for zone in zones:
        plan = plans[zone["name"]]
        items = mission_items(plan, zone, frame, robot)
        # One fence per day's job: this zone plus the paths, within the fence-point budget.
        incl, excl = fence_polygons(lawn_def, {zone["name"]: plan}, frame, robot)
        (out / f"{zone['name']}-fence.json").write_text(json.dumps({"inclusion": incl, "exclusion": excl}))
        write_waypoints(items, out / f"{zone['name']}.waypoints")
        write_qgc_plan(items, incl, excl, frame, robot, out / f"{zone['name']}.plan")
        plot(plan, zone, out / f"{zone['name']}.png")
        s = plan["stats"]
        rows.append((zone["name"], s, len(items)))

    tot_area = sum(s["area"] for _, s, _ in rows)
    tot_cov = sum(s["covered"] for _, s, _ in rows)
    tot_h = sum(s["hours"] for _, s, _ in rows)
    lines = [
        f"# Coverage plan: {args.lawn.name} ({args.config} deck)",
        "",
        f"Robot ({args.config}): cut {robot.cut_width:.3f} m, pass spacing {robot.spacing:.3f} m, body half-width "
        f"{robot.half_width:.2f} m, {robot.speed} m/s, pivot {robot.pivot_rate:.0f}°/s.",
        "",
        "| Zone | Lawn area | Cut | Missed | Stripe angle | Stripes | Blade-on / transit distance | "
        "Time (of which turning) | Mission items |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, s, n in rows:
        lines.append(f"| {name} | {s['area']:.0f} m² | {s['covered'] / s['area']:.1%} | {s['missed']:.0f} m² | "
                     f"{s['angle']}° | {s['stripes']} | {s['dist_on'] / 1000:.2f} / {s['dist_off'] / 1000:.2f} km | "
                     f"{s['hours']:.1f} h ({s['turn_hours']:.1f} h) | {n} |")
    lines += [
        f"| **Total** | **{tot_area:.0f} m²** | **{tot_cov / tot_area:.1%}** | "
        f"{tot_area - tot_cov:.0f} m² | | | | **{tot_h:.1f} h** | |",
        "",
        "Missed area is the band along fences, beds, and trees that the robot can't reach with its body "
        "inside the lawn: hand-trim it, or define a softer boundary where the lawn continues past the edge.",
    ]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
