#!/usr/bin/env python3
"""Configure a u-blox ZED-F9P as the farm's RTK base station.

Works on macOS, Linux, and Raspberry Pi; no u-center needed. See
docs/guides/rtk-base-station.md for the full procedure.

    python configure_f9p_base.py PORT raw-log
        Enable raw-observation output (RXM-RAWX/SFRBX) on USB for 24 h PPP logging.
    python configure_f9p_base.py PORT survey-in [--minutes 60] [--acc-m 2.0]
        Quick start: the base averages its own position, then transmits corrections.
    python configure_f9p_base.py PORT fixed --lat 42.1234567890 --lon -76.1234567890 --height 312.345
        Normal operation: transmit corrections from a known (PPP-derived) position.
        --height is the ELLIPSOIDAL height in metres (what PPP services report).
    python configure_f9p_base.py PORT status
        Print survey-in progress / fix status for 30 s.

All modes send RTCM3 corrections out of UART2 at 38400 baud (the F9P default,
which the rover's UART2 already expects) for a transparent 915 MHz radio.
Settings are saved to RAM, battery-backed RAM, and flash.
"""

import argparse
import sys
import time

from pyubx2 import UBXMessage, UBXReader
from serial import Serial

LAYERS = 0b111  # RAM | BBR | FLASH
UART2_BAUD = 38400

# RTCM3 MSM4 (smaller than MSM7, fits a 915 MHz link comfortably) for GPS, GLONASS,
# Galileo, BeiDou + base position (1005) + GLONASS biases (1230).
RTCM_UART2 = [
    ("CFG_MSGOUT_RTCM_3X_TYPE1005_UART2", 1),
    ("CFG_MSGOUT_RTCM_3X_TYPE1074_UART2", 1),
    ("CFG_MSGOUT_RTCM_3X_TYPE1084_UART2", 1),
    ("CFG_MSGOUT_RTCM_3X_TYPE1094_UART2", 1),
    ("CFG_MSGOUT_RTCM_3X_TYPE1124_UART2", 1),
    ("CFG_MSGOUT_RTCM_3X_TYPE1230_UART2", 5),
]
UART2_PORT = [
    ("CFG_UART2_BAUDRATE", UART2_BAUD),
    ("CFG_UART2OUTPROT_RTCM3X", 1),
    ("CFG_UART2OUTPROT_NMEA", 0),
    ("CFG_UART2OUTPROT_UBX", 0),
]
STATUS_USB = [
    ("CFG_USBOUTPROT_UBX", 1),
    ("CFG_MSGOUT_UBX_NAV_SVIN_USB", 1),
    ("CFG_MSGOUT_UBX_NAV_PVT_USB", 1),
]


def send(ser: Serial, cfg: list[tuple[str, int]]):
    # VALSET accepts at most 64 keys per message.
    for i in range(0, len(cfg), 64):
        msg = UBXMessage.config_set(LAYERS, 0, cfg[i : i + 64])
        ser.write(msg.serialize())
        time.sleep(0.2)
    print(f"sent {len(cfg)} settings")


def split_hp(value: float, scale: float, hp_scale: float):
    """Split a coordinate into the F9P's standard + high-precision integer fields."""
    whole = int(value / scale)
    hp = round((value - whole * scale) / hp_scale)
    if hp > 99:  # keep the HP part inside its -99..99 range
        whole, hp = whole + 1, hp - int(scale / hp_scale)
    elif hp < -99:
        whole, hp = whole - 1, hp + int(scale / hp_scale)
    return whole, hp


def fixed_cfg(lat: float, lon: float, height_m: float, acc_m: float):
    lat_i, lat_hp = split_hp(lat, 1e-7, 1e-9)
    lon_i, lon_hp = split_hp(lon, 1e-7, 1e-9)
    h_i, h_hp = split_hp(height_m * 100, 1.0, 0.01)  # cm and 0.1 mm
    return [
        ("CFG_TMODE_MODE", 2),  # fixed
        ("CFG_TMODE_POS_TYPE", 1),  # LLH
        ("CFG_TMODE_LAT", lat_i),
        ("CFG_TMODE_LAT_HP", lat_hp),
        ("CFG_TMODE_LON", lon_i),
        ("CFG_TMODE_LON_HP", lon_hp),
        ("CFG_TMODE_HEIGHT", h_i),
        ("CFG_TMODE_HEIGHT_HP", h_hp),
        ("CFG_TMODE_FIXED_POS_ACC", int(acc_m * 10_000)),
    ]


def status(ser: Serial, seconds: int = 30):
    rdr = UBXReader(ser, protfilter=2)
    end = time.time() + seconds
    while time.time() < end:
        _, msg = rdr.read()
        if msg is None:
            continue
        if msg.identity == "NAV-SVIN":
            print(f"survey-in: {msg.dur} s, mean accuracy {msg.meanAcc / 10_000:.3f} m, "
                  f"valid={msg.valid}, active={msg.active}")
        elif msg.identity == "NAV-PVT":
            print(f"fix type {msg.fixType}, sats {msg.numSV}, lat {msg.lat:.7f}, lon {msg.lon:.7f}, "
                  f"hAcc {msg.hAcc / 1000:.3f} m")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("port", help="serial port, e.g. /dev/ttyACM0 (Pi) or /dev/cu.usbmodem1101 (Mac)")
    ap.add_argument("--baud", type=int, default=38400, help="USB ignores this; set for a UART1 connection")
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("raw-log")
    sv = sub.add_parser("survey-in")
    sv.add_argument("--minutes", type=float, default=60)
    sv.add_argument("--acc-m", type=float, default=2.0, help="stop once mean accuracy is better than this")
    fx = sub.add_parser("fixed")
    fx.add_argument("--lat", type=float, required=True)
    fx.add_argument("--lon", type=float, required=True)
    fx.add_argument("--height", type=float, required=True, help="ellipsoidal height, metres")
    fx.add_argument("--acc-m", type=float, default=0.02, help="accuracy of the given position")
    sub.add_parser("status")
    args = ap.parse_args()

    with Serial(args.port, args.baud, timeout=2) as ser:
        if args.mode == "raw-log":
            send(ser, [("CFG_USBOUTPROT_UBX", 1), ("CFG_RATE_MEAS", 1000),
                       ("CFG_MSGOUT_UBX_RXM_RAWX_USB", 1), ("CFG_MSGOUT_UBX_RXM_SFRBX_USB", 1)])
        elif args.mode == "survey-in":
            send(ser, UART2_PORT + RTCM_UART2 + STATUS_USB + [
                ("CFG_TMODE_MODE", 1),
                ("CFG_TMODE_SVIN_MIN_DUR", int(args.minutes * 60)),
                ("CFG_TMODE_SVIN_ACC_LIMIT", int(args.acc_m * 10_000)),
            ])
        elif args.mode == "fixed":
            if not (-90 <= args.lat <= 90 and -180 <= args.lon <= 180):
                sys.exit("lat/lon out of range")
            send(ser, UART2_PORT + RTCM_UART2 + STATUS_USB
                 + fixed_cfg(args.lat, args.lon, args.height, args.acc_m))
        elif args.mode == "status":
            status(ser)


if __name__ == "__main__":
    main()
