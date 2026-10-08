"""Start ArduPilot Rover SITL as our robot and talk to it over MAVLink.

Used by run_sitl.py. Each run gets its own directory under runs/ (logs, eeprom,
and a scripts/ folder with the Lua interlock), so runs never share state.
"""

import shutil
import subprocess
import time
from pathlib import Path

from pymavlink import mavutil

SIM = Path(__file__).parent
REPO = SIM.parent.parent
AP = SIM / "ardupilot"
BINARY = AP / "build/sitl/bin/ardurover"
PARAMS = REPO / "software/ardupilot/params"
SCRIPTS = REPO / "software/ardupilot/scripts"

MODE = {"MANUAL": 0, "HOLD": 4, "AUTO": 10, "RTL": 11, "GUIDED": 15}


class Sitl:
    def __init__(self, run_name: str, home, speedup: int = 10, instance: int = 0):
        self.dir = SIM / "runs" / run_name
        if self.dir.exists():
            shutil.rmtree(self.dir)
        (self.dir / "scripts").mkdir(parents=True)
        for f in SCRIPTS.glob("*.lua"):
            shutil.copy(f, self.dir / "scripts" / f.name)
        defaults = [
            AP / "Tools/autotest/default_params/rover.parm",
            AP / "Tools/autotest/default_params/rover-skid.parm",
            PARAMS / "orbitist-v1.param",
            PARAMS / "sitl-overlay.param",
        ]
        lat, lon, alt = home
        cmd = [str(BINARY), "--model", "rover-skid", "--speedup", str(speedup),
               "--home", f"{lat},{lon},{alt},0", "--defaults", ",".join(str(d) for d in defaults),
               "-I", str(instance)]
        self.log = open(self.dir / "sitl.out", "w")
        self.proc = subprocess.Popen(cmd, cwd=self.dir, stdout=self.log, stderr=subprocess.STDOUT)
        self.port = 5760 + 10 * instance
        self.mav = None
        self.messages = []  # STATUSTEXT log
        self.on_message = None  # optional hook that sees every message (keeps timing exact)

    def connect(self, timeout=30):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.proc.poll() is not None:
                raise RuntimeError(f"SITL exited, see {self.dir / 'sitl.out'}")
            try:
                self.mav = mavutil.mavlink_connection(f"tcp:127.0.0.1:{self.port}", source_system=255)
                if self.mav.wait_heartbeat(timeout=10):
                    self.mav.mav.request_data_stream_send(self.mav.target_system, self.mav.target_component,
                                                          mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)
                    return self
            except OSError:
                time.sleep(0.5)
        raise TimeoutError("no heartbeat from SITL")

    def close(self):
        try:
            if self.mav:
                self.mav.close()
        finally:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.log.close()

    # ------------------------------------------------------------- helpers --
    def recv(self, types=None, timeout=1.0):
        t_end = time.time() + timeout
        while True:
            msg = self.mav.recv_match(blocking=True, timeout=max(0.0, t_end - time.time()))
            if msg is None:
                return None
            if msg.get_type() == "STATUSTEXT":
                self.messages.append(msg.text)
            if self.on_message:
                self.on_message(msg)
            if types is None or msg.get_type() in ([types] if isinstance(types, str) else types):
                return msg

    def heartbeat(self):
        self.mav.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)

    def get_param(self, name, timeout=5):
        self.mav.mav.param_request_read_send(self.mav.target_system, self.mav.target_component,
                                             name.encode(), -1)
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = self.recv("PARAM_VALUE", 1)
            if m and m.param_id == name:
                return m.param_value
        return None

    def set_param(self, name, value, timeout=5):
        for _ in range(3):
            self.mav.mav.param_set_send(self.mav.target_system, self.mav.target_component, name.encode(),
                                        float(value), mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
            t0 = time.time()
            while time.time() - t0 < timeout / 3:
                m = self.recv("PARAM_VALUE", 0.5)
                if m and m.param_id == name and abs(m.param_value - value) < 1e-4:
                    return True
        raise RuntimeError(f"could not set {name}")

    def all_params(self, timeout=60):
        self.mav.mav.param_request_list_send(self.mav.target_system, self.mav.target_component)
        params, t0 = {}, time.time()
        while time.time() - t0 < timeout:
            m = self.recv("PARAM_VALUE", 3)
            if m is None:
                break
            params[m.param_id] = m.param_value
            if len(params) >= m.param_count:
                break
        return params

    def set_mode(self, name, timeout=10):
        num = MODE[name]
        t0 = time.time()
        while time.time() - t0 < timeout:
            self.mav.mav.set_mode_send(self.mav.target_system,
                                       mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, num)
            m = self.recv("HEARTBEAT", 1)
            if m and m.custom_mode == num:
                return True
        raise TimeoutError(f"mode {name} not accepted")

    def mode(self):
        m = self.recv("HEARTBEAT", 2)
        return m.custom_mode if m else None

    def arm(self, timeout=60):
        t0 = time.time()
        while time.time() - t0 < timeout:
            self.mav.mav.command_long_send(self.mav.target_system, self.mav.target_component,
                                           mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
            t1 = time.time()
            while time.time() - t1 < 2:
                m = self.recv(["HEARTBEAT", "STATUSTEXT"], 0.5)
                if m and m.get_type() == "HEARTBEAT" and m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
                    return True
        raise TimeoutError("could not arm: " + " | ".join(self.messages[-5:]))

    def is_armed(self):
        m = self.recv("HEARTBEAT", 2)
        return bool(m and m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

    def wait_ready(self, timeout=90):
        """Wait for GPS fix and EKF to settle (position estimate available)."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = self.recv("GPS_RAW_INT", 1)
            if m and m.fix_type >= 3:
                e = self.recv("EKF_STATUS_REPORT", 2)
                if e and (e.flags & 0x10):  # EKF_POS_HORIZ_ABS
                    return True
        raise TimeoutError("GPS/EKF never became ready")

    # ------------------------------------------------- mission protocol --
    def upload(self, items, mission_type=0, timeout=60):
        """items: list of dicts with command, frame, params (p1..p4), x, y, z (lat/lon as degrees)."""
        mav = self.mav.mav
        mav.mission_count_send(self.mav.target_system, self.mav.target_component, len(items), mission_type)
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = self.recv(["MISSION_REQUEST_INT", "MISSION_REQUEST", "MISSION_ACK"], 2)
            if m is None:
                continue
            if m.get_type() == "MISSION_ACK":
                if m.mission_type != mission_type:
                    continue
                if m.type == 0:
                    return True
                raise RuntimeError(f"mission upload rejected: type {m.type}")
            if getattr(m, "mission_type", 0) != mission_type:
                continue
            it = items[m.seq]
            p = it["params"]
            mav.mission_item_int_send(self.mav.target_system, self.mav.target_component, m.seq,
                                      it["frame"], it["command"], 0, 1, p[0], p[1], p[2], p[3],
                                      int(round(it["x"] * 1e7)), int(round(it["y"] * 1e7)), it["z"],
                                      mission_type)
        raise TimeoutError("mission upload timed out")
