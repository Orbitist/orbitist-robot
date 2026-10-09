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


def assembly(p: Params, config: str = "single") -> list[PartRecord]:
    return frame(p) + drive(p) + casters(p) + decks(p, config) + payload(p)
