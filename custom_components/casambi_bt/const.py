"""Constants for the Casambi Bluetooth integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "casambi_bt"

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SCENE,
    Platform.SENSOR,
]

# Unit types of battery-less EnOcean switches report this mode string.
KINETIC_SWITCH_MODE: Final = "Kinetic Switch"
# PTM215B/PTM216B/PTM535BZ expose four rocker contacts.
KINETIC_SWITCH_BUTTONS: Final = 4

CONF_IMPORT_GROUPS: Final = "import_groups"

RECONNECT_BACKOFF_START: Final = 2
RECONNECT_BACKOFF_STEP: Final = 2
RECONNECT_BACKOFF_MAX: Final = 300
