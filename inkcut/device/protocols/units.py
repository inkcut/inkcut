"""Addressing names shared by DM/PL and HP-GL, and their plotter units per inch."""

# Cutter menu order, then Inkcut's 1021-per-inch rate.
ADDRESSING_0_001_INCH = "0.001 inch"
ADDRESSING_0_025_MM = "0.025 mm"
ADDRESSING_0_1_MM = "0.1 mm"
ADDRESSING_0_005_INCH = "0.005 inch"
ADDRESSING_LEGACY = "1021 per inch"

ADDRESSING_ORDER = (
    ADDRESSING_0_001_INCH,
    ADDRESSING_0_025_MM,
    ADDRESSING_0_1_MM,
    ADDRESSING_0_005_INCH,
    ADDRESSING_LEGACY,
)

_UNITS_PER_INCH = {
    ADDRESSING_0_001_INCH: 1000,
    ADDRESSING_0_025_MM: 1016,
    ADDRESSING_0_1_MM: 254,
    ADDRESSING_0_005_INCH: 200,
    ADDRESSING_LEGACY: 1021,
}


def units_per_inch(addressing):
    return _UNITS_PER_INCH[addressing]
