"""Parametric assembly of the Orbitist platform v1 (build123d).

The geometry lives in parts/ (frame, drive, casters, deck, payload); this module
assembles it and re-exports the helpers that build.py, strength.py and the
simulation planner use.
"""

from params import Params
from parts.casters import casters
from parts.common import GROUP_COLORS, MATERIAL, PartRecord  # noqa: F401 (re-exported)
from parts.deck import decks
from parts.drive import drive
from parts.frame import frame
from parts.payload import bumper_layout, payload  # noqa: F401 (re-exported)
from parts.plates import caster_plate_extent  # noqa: F401 (re-exported)
from parts.razor_deck import razor_deck
from parts.roof import roof

CONFIGS = ("razor", "single", "twin")  # razor = v1 baseline (daily cutting + solar roof)


def assembly(p: Params, config: str = "razor") -> list[PartRecord]:
    base = frame(p) + drive(p) + casters(p)
    if config == "razor":
        # The roof carries the GNSS antenna and e-stop, so payload() drops its own.
        skip = {"gnss_mast", "gnss_antenna", "mast_bolts", "estop_base", "estop_button"}
        return base + razor_deck(p) + [r for r in payload(p) if r.name not in skip] + roof(p)
    return base + decks(p, config) + payload(p)
