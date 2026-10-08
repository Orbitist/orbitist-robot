# Guide: setting up the farm RTK base station

**Goal:** a permanent GPS base station that sends centimetre-level corrections to the robot (and any future robot) over a 915 MHz radio, with its own position pinned down accurately enough that lawn maps never shift.

**Time:** about 2 hours of hands-on work, plus 24 hours of unattended logging and 1–3 days waiting for the position result.
**Do it before the ground freezes:** the mast is easier to mount now, and you'll want corrections working to map the lawn edges this fall.

---

## 1. What you need

| Item | Notes |
|---|---|
| u-blox ZED-F9P board | ArduSimple simpleRTK2B or SparkFun GPS-RTK2 class. An XBee-style socket makes the radio plug-in. |
| Multiband (L1/L2) GNSS antenna + ground plane | Survey-style antenna if budget allows, otherwise u-blox ANN-MB on a ≥ 10 cm metal plate |
| Antenna cable | SMA, low-loss (LMR-195/240 class). Keep it under ~10 m. |
| 915 MHz radio pair | SiK-class (e.g. Holybro SiK V3) or XBee-socket radios that match the F9P board. One end at the base, one on the robot. **Separate from the telemetry radio pair.** |
| Raspberry Pi | Pi 4 / Pi 5 / Zero 2 W with Raspberry Pi OS. Logs raw data for the position survey and can later serve corrections over the network. A laptop can stand in for the 24 h log. |
| Mast + mounts | Rigid pole (e.g. 1"–1.5" galvanised pipe) with an antenna mount, a weatherproof box for the F9P + Pi, and a 5 V power supply |
| Optional | Surge/lightning arrestor and grounding for a roof mount |

## 2. Choose the site

- **Clear sky:** no trees or buildings above ~15° elevation in any direction. Open-sky farms are ideal.
- **Rigid and permanent:** the antenna must not move by even a centimetre after its position is measured. Bolt the mast to a building or set it in concrete. No guy wires that sway, and no fence posts that heave with frost.
- **Away from reflectors:** keep it ≥ 1 m above a metal roof and away from tall metal walls.
- **Power and radio line of sight:** a building with power. Mount the 915 MHz radio antenna as high as practical so it can see all the lawns. SiK radios typically reach 1+ km over open ground.
- **Central** to the lawns if possible. Accuracy degrades by ~1 mm per km from the base, so it's irrelevant at farm scale, but radio range isn't.

Mark the antenna's exact mounting point. If it's ever removed, it must go back in the same place, or the position must be measured again.

## 3. Wire it up

```
 [GNSS antenna] ── SMA cable ── [ZED-F9P] ──USB── [Raspberry Pi] ── 5 V supply
                                    │
                                 UART2 (38400 baud, RTCM3 out)
                                    │
                             [915 MHz radio, base end]  ·····air·····  [radio, robot end] ── rover F9P UART2
```

- On ArduSimple boards, the radio plugs into the XBee socket, which is already connected to UART2.
- On other boards, wire F9P **UART2 TX → radio RX**, plus GND and power (check the radio's voltage).

## 4. Set up the Raspberry Pi

```bash
sudo apt update && sudo apt install -y rtklib python3-venv
git clone https://github.com/Orbitist/orbitist-robot.git
cd orbitist-robot/software/base-station
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
ls /dev/ttyACM*        # the F9P shows up as /dev/ttyACM0 over USB
```

`rtklib` provides `str2str` (logging and streaming) and `convbin` (format conversion). If the Debian package's `convbin` mishandles F9P data, build the [rtklibexplorer "demo5"](https://github.com/rtklibexplorer/RTKLIB) version instead.

## 5. Configure the radios (once)

Both radios in a pair must match. For SiK radios, connect each one to a computer by USB and use a serial terminal. On a Mac, run `screen /dev/cu.usbserial-XXXX 57600` (57600 is the factory default speed). Type `+++` and wait for `OK`, then:

```
ATS1=38      # serial speed 38400, matching F9P UART2
ATS2=64      # air data rate 64 kbps
ATS3=37      # NETID: any number, but different from the telemetry radio pair
ATS5=0       # ECC off
ATS6=0       # MAVLink framing OFF: corrections are raw RTCM, not MAVLink
AT&W         # save
ATZ          # reboot
```

## 6. Measure the base position (24 h log → PPP)

The base needs to know exactly where its antenna is. The free **Canadian CSRS-PPP service** works anywhere in the world, including the US. It processes 24 h of raw data into a position good to about 1–2 cm.

```bash
# 1. Turn on raw measurement output
.venv/bin/python configure_f9p_base.py /dev/ttyACM0 raw-log

# 2. Log for at least 24 hours (runs unattended; use tmux or nohup so it survives logout)
str2str -in serial://ttyACM0:115200 -out file://base_%Y%m%d_%h%M.ubx::S=24

# 3. Convert to RINEX
convbin -r ubx -v 3.04 -od -os -oi -ot base_*.ubx
```

4. Create a free account at [CSRS-PPP](https://webapp.csrs-scrs.nrcan-rncan.gc.ca/geod/tools-outils/ppp.php). Upload the `.obs` file and select **Static** processing and **ITRF** as the reference frame. Results arrive by email, usually within a few hours. Re-submit after ~2 weeks if you want the "final" orbits; the difference is usually millimetres.
5. From the results, record the **latitude, longitude, and ellipsoidal height** (*not* orthometric/sea-level height). Save them in [`base-station-position.md`](#8-record-the-position) along with the date and antenna type.

*Alternative:* NOAA [OPUS](https://geodesy.noaa.gov/OPUS/) accepts 2–48 h of dual-frequency GPS data and returns NAD83 coordinates. It can be fussier about F9P data, so try it only if CSRS-PPP isn't an option.

## 7. Start sending corrections

**Normal operation, with the PPP position known:**

```bash
.venv/bin/python configure_f9p_base.py /dev/ttyACM0 fixed --lat 42.1234567890 --lon -76.1234567890 --height 312.345
.venv/bin/python configure_f9p_base.py /dev/ttyACM0 status
```

The settings are saved to flash, so the base resumes sending corrections by itself after a power cut. The Pi isn't needed for that.

**Quick start while waiting for PPP results:**

```bash
.venv/bin/python configure_f9p_base.py /dev/ttyACM0 survey-in --minutes 60 --acc-m 2.0
```

Survey-in averages the base's own position, which is only accurate to ~1–2 m. The robot still gets centimetre-precise positions *relative to the base*, but all maps would shift by up to ~2 m when you switch to the PPP position later. So **use survey-in only for testing, and wait for the PPP position before recording lawn boundaries.** If you must map early, record the surveyed-in position (from `status`) and keep using it as the `fixed` position permanently. Consistency matters more than absolute accuracy for mowing.

## 8. Record the position

Create `docs/guides/base-station-position.md` (in git) with:

```
Base station: <location description, e.g. "north gable of the barn, mast at NE corner">
Antenna: <make/model>, mounted <date>
Position (ITRF2020, epoch <date>): lat <...>, lon <...>, ellipsoidal height <...> m
Source: CSRS-PPP, <n> h log, <date>, reported 95% accuracy <...>
```

If the antenna is ever moved or replaced, measure the position again and update this file. Lawn maps and fences are only valid against this one position.

## 9. Robot side

- The rover F9P connects to the flight controller's GPS1 port. ArduPilot configures it automatically (`GPS1_TYPE = 1`, `GPS_AUTO_CONFIG = 1`).
- The robot-end radio feeds the **rover F9P's UART2**, which accepts RTCM3 at 38400 baud by factory default. No configuration and no ArduPilot "GPS inject" needed.
- In Mission Planner or QGroundControl, the GPS status should go **3D Fix → RTK Float → RTK Fixed** within a minute or two under open sky. ArduPilot reports this as GPS status 6 (RTK Fixed).

**Acceptance test:** put the rover antenna on a fixed point, such as a nail in a fence post, and record the position. Move away, come back an hour later, and check that it reads within **±2 cm**.

## 10. Later: corrections over the network (NTRIP)

Once the farm network reaches the lawns, the Pi can also publish corrections as an NTRIP caster with `str2str`. Robots with Wi-Fi or LTE, a tractor's guidance system, or survey gear can then use the same base. For example:

```bash
str2str -in serial://ttyACM0:115200 -out ntripc://:password@:2101/FARM
```

That requires the F9P's RTCM output on USB as well as UART2. This step is optional; the radio link is all phase 1 needs.

## Troubleshooting

| Symptom | Check |
|---|---|
| Rover never reaches RTK Float | Radio link LEDs, matching NETID and speeds, `ATS6=0` (MAVLink framing off), and TX → RX wiring |
| Float but never Fixed | Sky view at the rover (trees), the antenna ground plane, and the base position actually being set (`status`) |
| Positions jump by ~1 m after reconfiguring | The base position changed (e.g. switching from survey-in to fixed). Expected; re-map or keep one position. |
| CSRS-PPP rejects the file | Log was too short, or the RINEX is missing observation types. Try the demo5 `convbin`. |
