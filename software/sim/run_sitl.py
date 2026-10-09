"""Simulation acceptance tests for the Orbitist robot (ArduPilot Rover SITL).

Usage (from software/sim/):
    .venv/bin/python run_sitl.py                      # all scenarios on lawns/test-plot.json
    .venv/bin/python run_sitl.py mission estop        # selected scenarios
    .venv/bin/python run_sitl.py mission --lawn lawns/sample-farm.json --zone east --speedup 40

Each scenario boots a fresh simulated robot with software/ardupilot/params + the blade
interlock script, uploads the planned mission and geofence, and checks behaviour:

    mission   mows the zone: completes, path-tracking error, actual cut coverage, blade only in AUTO
    rc_loss   RC transmitter lost mid-mission -> Hold, blade off
    estop     e-stop loop opens mid-mission -> disarm and blade off within 0.5 s
    restart   e-stop released afterwards -> robot stays disarmed and still
    gps_loss  GPS lost mid-mission -> blade off at once, robot stops
    fence     commanded toward a point outside the fence -> stays inside (within margin)

Writes runs/<scenario>/ (logs, track plot) and results/<lawn>.md (summary table).
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymavlink import mavutil
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

import coverage
from sitl import MODE, Sitl

SIM = Path(__file__).parent


class Track:
    """Everything the robot reports, timestamped in simulation seconds."""

    def __init__(self, frame):
        self.frame = frame
        self.pos = []  # (t, x, y)
        self.blade = []  # (t, value)
        self.mode = []  # (t, mode, armed)
        self.t = 0.0

    def to_xy(self, lat, lon):
        return ((lon - self.frame.lon0) * self.frame.k_lon, (lat - self.frame.lat0) * self.frame.k_lat)

    def feed(self, m):
        if m is None:
            return
        typ = m.get_type()
        if typ == "GLOBAL_POSITION_INT":
            self.t = m.time_boot_ms / 1000
            if m.lat == 0 and m.lon == 0:
                return  # no position estimate yet
            self.pos.append((self.t, *self.to_xy(m.lat / 1e7, m.lon / 1e7)))
        elif typ == "NAMED_VALUE_FLOAT" and m.name.startswith("BLADE"):
            self.blade.append((m.time_boot_ms / 1000, m.value))
        elif typ == "NAMED_VALUE_FLOAT" and m.name.startswith("ARMED"):
            t = m.time_boot_ms / 1000
            mode = self.mode[-1][1] if self.mode else None
            self.mode.append((t, mode, m.value > 0.5))
        elif typ == "HEARTBEAT" and m.type != mavutil.mavlink.MAV_TYPE_GCS:
            armed = bool(m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            if not self.mode or self.mode[-1][1:] != (m.custom_mode, armed):
                self.mode.append((self.t, m.custom_mode, armed))

    def blade_at(self, t):
        v = 0
        for tb, val in self.blade:
            if tb > t:
                break
            v = val
        return v

    def mode_at(self, t):
        cur = (None, False)
        for tm, mode, armed in self.mode:
            if tm > t:
                break
            cur = (mode, armed)
        return cur


class Scenario:
    def __init__(self, name, lawn_path, zone_name, speedup, instance=0, overlap=0.15, config="razor"):
        self.name = name
        self.lawn = json.loads(Path(lawn_path).read_text())
        self.zone = next(z for z in self.lawn["zones"] if zone_name in (None, z["name"]))
        self.robot = coverage.Robot(config, overlap=overlap)
        self.frame = coverage.LocalFrame(self.lawn["origin"])
        self.plan = coverage.plan_zone(self.zone, self.robot)
        self.items = coverage.mission_items(self.plan, self.zone, self.frame, self.robot)
        incl, excl = coverage.fence_polygons(self.lawn, {self.zone["name"]: self.plan}, self.frame, self.robot)
        self.fence_ll = (incl, excl)
        self.fence_xy = unary_union([Polygon([self.frame_xy(*ll) for ll in poly]) for poly in incl]).difference(
            unary_union([Polygon([self.frame_xy(*ll) for ll in poly]) for poly in excl]))
        o = self.lawn["origin"]
        dock_lat, dock_lon = self.frame.ll(*self.lawn["dock"])  # the robot starts parked at the dock
        self.sitl = Sitl(name, (dock_lat, dock_lon, o["alt"]), speedup=speedup, instance=instance)
        self.track = Track(self.frame)
        self.sitl.on_message = self.track.feed
        self.checks = []  # (description, passed, detail)

    def frame_xy(self, lat, lon):
        return ((lon - self.frame.lon0) * self.frame.k_lon, (lat - self.frame.lat0) * self.frame.k_lat)

    # ------------------------------------------------------------ plumbing --
    def pump(self, seconds_sim):
        """Process messages for a stretch of simulation time."""
        t_end = self.track.t + seconds_sim
        wall_end = time.time() + seconds_sim + 60
        while self.track.t < t_end and time.time() < wall_end:
            self.sitl.recv(None, 0.5)

    def pump_until(self, cond, timeout_sim, poll=None):
        t_end = self.track.t + timeout_sim
        wall_end = time.time() + timeout_sim + 120
        while self.track.t < t_end and time.time() < wall_end:
            m = self.sitl.recv(None, 0.5)
            if poll:
                poll(m)
            if cond():
                return True
        return False

    def check(self, desc, passed, detail=""):
        self.checks.append((desc, bool(passed), detail))

    def start(self):
        s = self.sitl
        s.connect()
        s.wait_ready()
        s.set_param("BLD_ESTOP_SRC", 2)  # simulated e-stop loop
        s.set_param("BLD_ESTOP_SIM", 1)
        fence_items = []
        for kind, polys in ((5001, self.fence_ll[0]), (5002, self.fence_ll[1])):
            for poly in polys:
                for lat, lon in poly:
                    fence_items.append(dict(command=kind, frame=0, params=[len(poly), 0, 0, 0], x=lat, y=lon, z=0))
        s.upload(fence_items, mission_type=1)
        s.upload(self.items, mission_type=0)
        s.set_param("FENCE_ENABLE", 1)
        s.set_mode("HOLD")
        s.arm()
        s.set_mode("AUTO")
        self.t_auto = self.track.t

    def wait_blade_on(self, timeout=300):
        return self.pump_until(lambda: self.track.blade and self.track.blade[-1][1] > 0.5, timeout)

    def finish(self):
        self.sitl.close()
        self.plot()
        out = self.sitl.dir / "result.json"
        out.write_text(json.dumps({"checks": self.checks, "messages": self.sitl.messages,
                                   "planned_path": self.plan["path"], "pos": self.track.pos,
                                   "blade": self.track.blade, "mode": self.track.mode}, indent=0))

    def plot(self):
        if not self.track.pos:
            return
        fig, ax = plt.subplots(figsize=(7, 6), dpi=110)
        for g in coverage.parts(self.fence_xy):
            ax.plot(*g.exterior.xy, color="#e76f51", lw=1, ls="--")
        for g in coverage.parts(self.plan["lawn"]):
            ax.fill(*g.exterior.xy, color="#dfe9d8")
            for h in g.interiors:
                ax.fill(*h.xy, color="#6b4f3a")
        px, py = zip(*self.plan["path"])
        ax.plot(px, py, color="0.6", lw=0.6, label="planned")
        on = [(x, y) for t, x, y in self.track.pos if self.track.blade_at(t) > 0.5]
        off = [(x, y) for t, x, y in self.track.pos if self.track.blade_at(t) <= 0.5]
        if off:
            ax.scatter(*zip(*off), s=1, color="#1d3557", label="driven, blade off")
        if on:
            ax.scatter(*zip(*on), s=1, color="#2a9d8f", label="driven, blade on")
        ax.set_aspect("equal")
        ax.legend(loc="upper right", fontsize=7)
        ax.set_title(f"SITL {self.name}")
        fig.tight_layout()
        fig.savefig(self.sitl.dir / "track.png")
        plt.close(fig)


# ---------------------------------------------------------------- scenarios --
def scenario_mission(sc: Scenario):
    sc.start()
    last = len(sc.items) - 1
    done = {"v": False}

    def poll(m):
        if m and m.get_type() == "MISSION_ITEM_REACHED" and m.seq >= last:
            done["v"] = True

    est = sc.plan["stats"]["hours"] * 3600 * 3 + 300
    finished = sc.pump_until(lambda: done["v"] or (sc.track.mode and sc.track.mode[-1][1] == MODE["HOLD"]
                                                   and sc.track.t > sc.t_auto + 5), est, poll)
    sc.pump(3)  # collect the reason (STATUSTEXT) for whatever ended the mission
    why = "" if done["v"] else " | last messages: " + " / ".join(
        m for m in sc.sitl.messages[-6:] if "waypoint" not in m)
    sc.check("mission completes", finished and done["v"], f"{sc.track.t - sc.t_auto:.0f} s sim{why}")

    path = LineString(sc.plan["path"])
    mowing = [(t, x, y) for t, x, y in sc.track.pos
              if sc.track.mode_at(t)[0] == MODE["AUTO"] and sc.track.blade_at(t) > 0.5]
    xte = sorted(path.distance(Point(x, y)) for _, x, y in mowing)
    if xte:
        p95 = xte[int(0.95 * (len(xte) - 1))]
        # Target for the real robot (RTK + tuned steering) is ~0.05 m; the generic SITL skid model
        # weaves more, so this gate is looser. Coverage below is the check that matters.
        sc.check("path tracking while mowing, p95 ≤ 0.15 m", p95 <= 0.15,
                 f"p95 {p95:.3f} m, median {xte[len(xte) // 2]:.3f} m, max {xte[-1]:.3f} m")
    pts = [(x, y) for _, x, y in sc.track.pos]
    flags = [sc.track.blade_at(t) > 0.5 for t, _, _ in sc.track.pos[1:]]
    cut = coverage.cut_of_track(pts, flags, sc.robot).intersection(sc.plan["lawn"])
    planned = sc.plan["stats"]["covered"] / sc.plan["stats"]["area"]
    actual = cut.area / sc.plan["lawn"].area
    # SITL's generic skid model weaves ~3x more than the real target (p95 ~0.14 m vs ~0.05 m),
    # so allow 2 %; tighten once real-robot tracking is measured.
    sc.check("actual cut ≥ planned − 2 %", actual >= planned - 0.02, f"actual {actual:.1%}, planned {planned:.1%}")
    bad = [t for t, v in sc.track.blade if v > 0.5 and sc.track.mode_at(t) != (MODE["AUTO"], True)]
    sc.check("blade on only while armed in AUTO", not bad, f"{len(bad)} violations")


def run_until_mowing(sc, seconds=20):
    sc.start()
    if not sc.wait_blade_on():
        sc.check("blade starts in AUTO", False)
        return False
    sc.pump(seconds)
    return True


def scenario_rc_loss(sc: Scenario):
    if not run_until_mowing(sc):
        return
    sc.sitl.set_param("SIM_RC_FAIL", 1)
    t0 = sc.track.t  # clock starts when the change is acknowledged (MAVLink latency excluded)
    ok = sc.pump_until(lambda: sc.track.mode[-1][1] == MODE["HOLD"] and sc.track.blade[-1][1] < 0.5, 10)
    sc.check("RC loss → Hold and blade off within 2.5 s", ok and sc.track.t - t0 <= 2.5, f"{sc.track.t - t0:.2f} s")


def scenario_estop(sc: Scenario, check_restart=False):
    if not run_until_mowing(sc):
        return
    sc.sitl.set_param("BLD_ESTOP_SIM", 0)
    t0 = sc.track.t
    ok = sc.pump_until(lambda: not sc.track.mode[-1][2] and sc.track.blade[-1][1] < 0.5, 5)
    sc.check("e-stop → disarmed and blade off within 0.5 s", ok and sc.track.t - t0 <= 0.5, f"{sc.track.t - t0:.2f} s")
    if check_restart:
        sc.pump(3)
        x0, y0 = sc.track.pos[-1][1:]
        sc.sitl.set_param("BLD_ESTOP_SIM", 1)
        sc.pump(10)
        x1, y1 = sc.track.pos[-1][1:]
        rearmed = any(armed for t, _, armed in sc.track.mode if t > t0 + 3)
        moved = math.hypot(x1 - x0, y1 - y0)
        sc.check("after release: stays disarmed and still", not rearmed and moved < 0.05,
                 f"re-armed={rearmed}, moved {moved:.3f} m")


def scenario_gps_loss(sc: Scenario):
    if not run_until_mowing(sc):
        return
    x0, y0 = sc.track.pos[-1][1:]
    sc.sitl.set_param("SIM_GPS_DISABLE", 1)
    t0 = sc.track.t
    ok = sc.pump_until(lambda: sc.track.blade[-1][1] < 0.5, 5)
    sc.check("GPS loss → blade off within 1.0 s", ok and sc.track.t - t0 <= 1.0, f"{sc.track.t - t0:.2f} s")
    stopped = sc.pump_until(lambda: sc.track.mode[-1][1] != MODE["AUTO"] or not sc.track.mode[-1][2], 30)
    t_stop = sc.track.t - t0
    sc.pump(2)
    pos = [(x, y) for t, x, y in sc.track.pos if t0 < t <= t0 + t_stop + 2]
    drift = max((math.hypot(x - x0, y - y0) for x, y in pos), default=0)
    sc.check("GPS loss → paused (Hold) within 3 s, < 2 m travelled", stopped and t_stop <= 3 and drift < 2,
             f"after {t_stop:.1f} s; travelled ≤ {drift:.2f} m (dead-reckoned estimate)")
    sc.sitl.set_param("SIM_GPS_DISABLE", 0)
    t1 = sc.track.t
    resumed = sc.pump_until(lambda: sc.track.mode[-1][1] == MODE["AUTO"] and sc.track.mode[-1][2], 60)
    sc.check("GPS back → mission resumes by itself", resumed, f"after {sc.track.t - t1:.1f} s")


def scenario_fence(sc: Scenario):
    if not run_until_mowing(sc, seconds=5):
        return
    s = sc.sitl
    s.set_mode("GUIDED")
    tx, ty = sc.zone["boundary"][1][0] + 10, sc.zone["boundary"][1][1] + 5  # well outside the lawn
    lat, lon = sc.frame.ll(tx, ty)
    for _ in range(3):
        s.mav.mav.set_position_target_global_int_send(
            0, s.mav.target_system, s.mav.target_component, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            0b110111111000, int(lat * 1e7), int(lon * 1e7), 0, 0, 0, 0, 0, 0, 0, 0, 0)
        sc.pump(1)
    sc.pump(60)
    outside = [sc.fence_xy.exterior.distance(Point(x, y)) if not sc.fence_xy.contains(Point(x, y)) else 0
               for _, x, y in sc.track.pos] if sc.fence_xy.geom_type == "Polygon" else \
        [0 if sc.fence_xy.contains(Point(x, y)) else sc.fence_xy.boundary.distance(Point(x, y))
         for _, x, y in sc.track.pos]
    worst = max(outside)
    sc.check("commanded outside the fence: stays within 1.0 m of it", worst <= 1.0, f"max excursion {worst:.2f} m")
    sc.check("blade off outside AUTO", sc.track.blade[-1][1] < 0.5)


SCENARIOS = {
    "mission": scenario_mission,
    "rc_loss": scenario_rc_loss,
    "estop": scenario_estop,
    "restart": lambda sc: scenario_estop(sc, check_restart=True),
    "gps_loss": scenario_gps_loss,
    "fence": scenario_fence,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios", nargs="*", default=list(SCENARIOS))
    ap.add_argument("--lawn", default=str(SIM / "lawns/test-plot.json"))
    ap.add_argument("--zone")
    ap.add_argument("--speedup", type=int, default=10)
    ap.add_argument("--overlap", type=float, default=0.15, help="pass-to-pass overlap, m (planner default)")
    ap.add_argument("--config", default="razor", choices=["razor", "single", "twin"])
    args = ap.parse_args()

    rows = []
    for name in args.scenarios:
        sc = Scenario(name, args.lawn, args.zone, args.speedup, overlap=args.overlap, config=args.config)
        t0 = time.time()
        try:
            SCENARIOS[name](sc)
        except Exception as e:  # report and keep going with the other scenarios
            sc.check("scenario ran", False, f"{type(e).__name__}: {e}")
        finally:
            sc.finish()
        for desc, ok, detail in sc.checks:
            rows.append((name, desc, ok, detail))
            print(f"{'PASS' if ok else 'FAIL'}  {name:9s} {desc}  {detail}", flush=True)
        print(f"      ({time.time() - t0:.0f} s wall)", flush=True)

    passed = sum(ok for _, _, ok, _ in rows)
    lines = [f"# SITL results: {Path(args.lawn).name}", "",
             f"ArduPilot Rover 4.6.3 SITL (rover-skid model, {args.config} deck), params `software/ardupilot/params`, "
             f"Lua `blade_interlock.lua`. **{passed}/{len(rows)} checks passed.**", "",
             "| Scenario | Check | Result | Detail |", "|---|---|---|---|"]
    lines += [f"| {n} | {d} | {'✅' if ok else '❌'} | {det} |" for n, d, ok, det in rows]
    (SIM / "results").mkdir(exist_ok=True)
    (SIM / "results" / f"{Path(args.lawn).stem}.md").write_text("\n".join(lines) + "\n")
    sys.exit(0 if passed == len(rows) else 1)


if __name__ == "__main__":
    main()
