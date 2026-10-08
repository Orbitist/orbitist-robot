"""Design parameters for the Orbitist platform v1 frame model.

Units: millimetres and kilograms.
Coordinates: X forward, Y left, Z up. The origin is on the ground directly
below the drive-axle midpoint.

Values marked ESTIMATE are typical sizes for parts we haven't bought yet.
Measure the real part and update the value; everything downstream regenerates.
"""

from dataclasses import dataclass, field


@dataclass
class Params:
    # --- Frame -------------------------------------------------------------
    frame_width: float = 1280.0  # outer width across the side rails (Y)
    frame_rear_x: float = -300.0  # rear face of the frame
    frame_front_x: float = 865.0  # front face of the frame
    frame_bottom_z: float = 300.0  # underside of the side rails
    side_rail: tuple = (30.0, 60.0)  # side rails: 30 wide x 60 tall extrusion
    cross_rail: tuple = (30.0, 30.0)  # cross members: 30x30 extrusion
    # Cross-member centre positions (X). Chosen to stay clear of the mower
    # motor housings that poke up through the frame (see deck_slots).
    cross_member_x: tuple = (-285.0, -120.0, 215.0, 600.0, 850.0)

    # --- Drive (10" hub motors in bolt-on forks) ---------------------------
    wheel_diameter: float = 254.0  # 10" pneumatic tire, ESTIMATE
    tire_width: float = 75.0  # 10x3", ESTIMATE
    hub_diameter: float = 160.0  # motor body, ESTIMATE
    dropout_spacing: float = 110.0  # axle shoulder to shoulder, ESTIMATE, measure!
    axle_flats: float = 10.0  # width across axle flats, ESTIMATE, measure!
    fork_plate_t: float = 6.0  # fork side plates (steel)
    fork_top_t: float = 8.0  # fork top plate (steel)
    fork_length_x: float = 200.0

    # --- Casters (zero-turn mower replacement casters) ---------------------
    caster_wheel_diameter: float = 280.0  # 11x4, ESTIMATE
    caster_wheel_width: float = 100.0
    caster_trail: float = 90.0  # pivot axis to wheel axle, ESTIMATE
    caster_pivot_x: float = 850.0  # as far back as the twin front deck allows
    caster_pivot_y: float = 560.0  # +/-; inboard of the side rails

    # --- Mower decks (Ryobi 40 V 20-21" class, handle and wheels removed) ----
    deck_housing_diameter: float = 580.0  # modelled as round, ESTIMATE
    deck_cut_width: float = 533.0  # 21"
    deck_shell_bottom_z: float = 40.0
    deck_shell_height: float = 130.0
    deck_motor_diameter: float = 200.0  # ESTIMATE
    deck_motor_height: float = 190.0  # ESTIMATE
    deck_overlap: float = 50.0  # cut overlap between twin decks
    deck_mass: float = 17.0  # ESTIMATE: ~23 kg mower minus handle, wheels, battery

    # --- Payload / electronics placeholders --------------------------------
    battery_size: tuple = (300.0, 160.0, 110.0)  # 36 V 20 Ah pack, ESTIMATE
    battery_pos: tuple = (0.0, 380.0)  # over the drive axle, left side
    ebox_size: tuple = (220.0, 300.0, 150.0)  # IP65 enclosure, long side across the frame
    ebox_pos: tuple = (-185.0, -60.0)  # rear bay, clear of the rear deck motor
    mast_pos: tuple = (-120.0, 150.0)
    mast_height: float = 600.0  # above the frame top
    hitch_height_z: float = 330.0

    # --- Masses (kg) for the CG / axle-load estimate ------------------------
    masses: dict = field(
        default_factory=lambda: {
            "hub_motor": 5.5,
            "drive_fork": 2.0,
            "caster": 3.0,
            "battery": 6.5,
            "ebox": 3.0,
            "mast_gnss": 1.0,
            "hitch": 1.5,
            "bumper": 1.5,
            "extrusion_30x30_per_m": 0.85,
            "extrusion_30x60_per_m": 1.5,
        }
    )

    # --- Derived helpers ---------------------------------------------------
    @property
    def frame_length(self) -> float:
        return self.frame_front_x - self.frame_rear_x

    @property
    def side_rail_y(self) -> float:
        """Centre-line Y of each side rail (and of the drive wheels)."""
        return self.frame_width / 2 - self.side_rail[0] / 2

    @property
    def frame_top_z(self) -> float:
        return self.frame_bottom_z + self.side_rail[1]

    def deck_slots(self, config: str):
        """(x, y) centres of the mower decks for a configuration.

        twin: staggered so the cuts overlap by deck_overlap while the round
        housings just clear each other (rear deck right, front deck left).
        """
        if config == "single":
            return [(50.0, 0.0)]
        if config == "twin":
            dy = (self.deck_cut_width - self.deck_overlap) / 2
            d = self.deck_housing_diameter
            dx = (d**2 - (2 * dy) ** 2) ** 0.5 + 10.0  # +10 mm clearance
            return [(50.0, -dy), (50.0 + dx, dy)]
        raise ValueError(config)
