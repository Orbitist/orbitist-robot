# RTK base station tools

`configure_f9p_base.py` configures a u-blox ZED-F9P as the farm's RTK base (raw logging, survey-in, fixed-position modes). It doesn't need u-center, so it works on Mac, Linux, and Raspberry Pi.

Full procedure: [docs/guides/rtk-base-station.md](../../docs/guides/rtk-base-station.md).

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python configure_f9p_base.py --help
```
