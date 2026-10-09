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
    frame_front_x: float = 850.0  # front face of the frame
    frame_bottom_z: float = 320.0  # underside of the side rails (set by caster height)
    side_rail: tuple = (30.0, 60.0)  # side rails: 30 wide x 60 tall extrusion
    cross_rail: tuple = (30.0, 30.0)  # cross members: 30x30 extrusion
    # Cross-member centre positions (X). Chosen to stay clear of the mower
    # motor housings that poke up through the frame (see deck_slots).
    cross_member_x: tuple = (-285.0, -120.0, 215.0, 600.0, 835.0)
    # Members that need more than 30x30 (strength.py): x=215 carries both decks in the twin layout;
    # the front member is 30x60 so its underside is flush with the side rails for the caster plates.
    cross_member_profile: dict = field(default_factory=lambda: {215.0: "30x60", 835.0: "30x60"})
    gusset_members: tuple = (-120.0, 215.0)  # joints that get top-face gussets (strength.py)

    # --- Drive (10" hub motors in bolt-on forks) ---------------------------
    wheel_diameter: float = 254.0  # 10" pneumatic tire, ESTIMATE
    tire_width: float = 75.0  # 10x3", ESTIMATE
    hub_diameter: float = 160.0  # motor body, ESTIMATE
    dropout_spacing: float = 110.0  # axle shoulder to shoulder, ESTIMATE, measure!
    axle_flats: float = 10.0  # width across axle flats, ESTIMATE, measure!
    fork_plate_t: float = 6.0  # fork side plates (steel)
    fork_top_t: float = 8.0  # fork top plate (steel)
    fork_length_x: float = 200.0

    # --- Casters (10" pneumatic plate-mount swivel casters, bolt-on) ---------
    caster_wheel_diameter: float = 260.0  # 4.10/3.50-4 tire, ESTIMATE
    caster_wheel_width: float = 85.0
    caster_trail: float = 65.0  # swivel offset, pivot to wheel axle, ESTIMATE
    caster_height: float = 305.0  # ground to top of caster plate, ESTIMATE, measure!
    caster_plate: tuple = (102.0, 114.0)  # caster top plate (X, Y), 4" x 4.5"
    caster_bolts: tuple = (67.0, 92.0)  # caster bolt pattern (X, Y), 2-5/8" x 3-5/8", measure!
    caster_mount_t: float = 8.0  # steel mount plate under the frame corner
    caster_pivot_x: float = 795.0  # caster plate must fit under the frame; front deck sets the limit
    caster_pivot_y: float = 560.0  # +/-; inboard of the side rails

    # --- Front bumper (sliding bar on springs, NC switches in the e-stop loop) ---
    bumper_travel: float = 100.0  # free travel before the bar hits its stops
    bumper_foam: float = 50.0  # closed-cell foam on the bar face
    bumper_z: tuple = (180.0, 300.0)  # bar face height range
    bumper_arm_y: float = 300.0  # +/- position of the two sliding arms (clear of the caster sweep)

    # --- Mower decks (Ryobi 40 V 20-21" class, handle and wheels removed) ----
    deck_housing_diameter: float = 580.0  # modelled as round, ESTIMATE
    deck_cut_width: float = 533.0  # 21"
    deck_shell_bottom_z: float = 40.0
    deck_shell_height: float = 130.0
    deck_motor_diameter: float = 200.0  # ESTIMATE
    deck_motor_height: float = 190.0  # ESTIMATE
    deck_overlap: float = 50.0  # cut overlap between twin decks
    deck_hanger_spread: float = 220.0  # hangers sit +/- this far either side of the deck centre (Y)
    deck_mass: float = 17.0  # ESTIMATE: ~23 kg mower minus handle, wheels, battery

    # --- Razor-disc mower deck (v1 baseline: daily "increment" cutting, see
    #     docs/design/form-factor-exploration.md) --------------------------------
    razor_disc_diameter: float = 280.0  # cutting circle over the blade tips
    # Disc centres, alternating front/rear rows so neighbours never touch while their cuts
    # overlap by 20 mm. Rows sit between the cross members at x = 215 and x = 600.
    razor_disc_xy: tuple = ((470.0, -390.0), (330.0, -130.0), (470.0, 130.0), (330.0, 390.0))
    razor_cut_z: float = 50.0  # blade height above ground (~2" cut)
    razor_plate_t: float = 3.0  # aluminium deck plate
    razor_plate_z: float = 95.0  # underside of the deck plate
    razor_skirt_h: float = 70.0  # HDPE skirt below the plate (blade guard)
    razor_motor_d: float = 60.0  # outrunner can diameter, ESTIMATE
    razor_motor_h: float = 45.0  # ESTIMATE
    razor_hanger_y: float = 450.0  # +/- hanger rods at the plate's sides
    razor_deck_mass: float = 10.0  # ESTIMATE: plate 5, skirt 1.5, 4 motors 2, discs 1.5

    # --- Solar roof ----------------------------------------------------------
    roof_post_h: float = 300.0  # 30x30 posts from the frame top to the roof frame underside
    roof_inset: float = 0.0  # roof frame outline = frame outline
    panel_size: tuple = (1050.0, 540.0, 3.0)  # semi-flexible 100-120 W class panel (X, Y, T), ESTIMATE
    panel_count: int = 2  # side by side across the width
    panel_w_peak: float = 110.0  # W per panel, ESTIMATE
    antenna_stub_h: float = 120.0  # GNSS antenna above the roof

    # --- Payload / electronics placeholders --------------------------------
    battery_size: tuple = (300.0, 160.0, 110.0)  # 36 V 20 Ah pack, ESTIMATE
    battery_pos: tuple = (0.0, 380.0)  # over the drive axle, left side
    ebox_size: tuple = (220.0, 300.0, 150.0)  # IP65 enclosure, long side across the frame
    ebox_pos: tuple = (-185.0, -60.0)  # rear bay, clear of the rear deck motor
    mast_pos: tuple = (-285.0, 300.0)  # on the roof's rear rail (razor config) or the frame (Ryobi configs)
    mast_height: float = 600.0  # above the frame top (Ryobi configs, no roof)
    estop_pos: tuple = (-285.0, -500.0)  # on the rear rail: of the roof (razor) or the frame (Ryobi)
    hitch_height_z: float = 288.0  # receiver tube centre: under the rear member, above the ground

    # --- Masses (kg) for the CG / axle-load estimate ------------------------
    masses: dict = field(
        default_factory=lambda: {
            "hub_motor": 5.5,
            "drive_fork": 2.0,
            "caster": 3.0,
            "battery": 6.5,
            "ebox": 3.0,
            "mast_gnss": 1.0,
            "hitch": 2.5,
            "bumper": 1.5,
            "bracket": 0.03,
            "gusset": 0.1,
            "hanger": 0.15,
            "roller": 0.2,
            "spring": 0.05,
            "switch": 0.03,
            "panel": 2.5,
            "mppt": 0.6,
            "extrusion_30x30_per_m": 0.85,
            "extrusion_30x60_per_m": 1.5,
        }
    )

    # --- Derived helpers ---------------------------------------------------
    @property
    def frame_length(self) -> float:
        return self.frame_front_x - self.frame_rear_x

    def cross_profile(self, x: float):
        """(size along X, height, name) of the cross member at x."""
        name = self.cross_member_profile.get(x, "30x30")
        return (30.0, 60.0, name) if name == "30x60" else (30.0, 30.0, name)

    @property
    def side_rail_y(self) -> float:
        """Centre-line Y of each side rail (and of the drive wheels)."""
        return self.frame_width / 2 - self.side_rail[0] / 2

    @property
    def frame_top_z(self) -> float:
        return self.frame_bottom_z + self.side_rail[1]

    def cut_span(self, config: str):
        """(y_min, y_max) of the cut relative to the robot centreline (left positive)."""
        if config == "razor":
            ys = [y for _, y in self.razor_disc_xy]
            return (min(ys) - self.razor_disc_diameter / 2, max(ys) + self.razor_disc_diameter / 2)
        ys = [y for _, y in self.deck_slots(config)]
        return (min(ys) - self.deck_cut_width / 2, max(ys) + self.deck_cut_width / 2)

    def razor_discs(self):
        """(x, y) of each disc centre."""
        return list(self.razor_disc_xy)

    def razor_plate_extent(self):
        """(x0, x1, half_width) of the deck plate around the discs."""
        r = self.razor_disc_diameter / 2 + 30
        xs = [x for x, _ in self.razor_disc_xy]
        ys = [abs(y) for _, y in self.razor_disc_xy]
        return (min(xs) - r, max(xs) + r, max(ys) + r)

    @property
    def roof_z(self) -> float:
        """Underside of the roof frame."""
        return self.frame_top_z + self.roof_post_h

    def deck_slots(self, config: str):
        """(x, y) centres of the mower decks for a configuration.

        twin: staggered so the cuts overlap by deck_overlap while the round
        housings just clear each other (rear deck right, front deck left).
        """
        dy = (self.deck_cut_width - self.deck_overlap) / 2
        d = self.deck_housing_diameter
        dx = (d**2 - (2 * dy) ** 2) ** 0.5 + 10.0  # +10 mm clearance
        rear_right, front_left = (50.0, -dy), (50.0 + dx, dy)
        if config == "single":
            # v1 uses the twin layout's rear-right slot: the cut reaches within ~16 cm of the
            # robot's right side for edging, and the twin upgrade only adds the front-left deck.
            return [rear_right]
        if config == "twin":
            return [rear_right, front_left]
        if config == "razor":
            return []
        raise ValueError(config)
