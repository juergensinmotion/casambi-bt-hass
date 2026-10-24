"""Binary Sensor implementation for Casambi."""

import logging
from typing import cast

from CasambiBt import Unit, UnitControlType

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN, CasambiApi
from .entities import CasambiNetworkEntity, CasambiUnitEntity, TypedEntityDescription

_LOGGER = logging.getLogger(__name__)


NETWORK_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="status",
        name="Status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_unload_entry(_hass: HomeAssistant, _entry: ConfigEntry) -> bool:
    """Support unloading of entry."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor."""
    _LOGGER.debug("Setting up binary sensor entities. config_entry: %s", config_entry)
    api: CasambiApi = hass.data[DOMAIN][config_entry.entry_id]
    binary_sensors = []

    # create network sensors
    for description in NETWORK_SENSORS:
        _LOGGER.debug("Adding CasambiBinarySensorEntity for network...")
        binary_sensors.append(CasambiBinarySensorEntity(api, description))

    # create presence sensors for motion detectors (e.g. Tridonic bDW PIR)
    for unit in api.get_units([UnitControlType.PRESENCE]):
        _LOGGER.debug("Adding presence sensor for unit %i", unit.deviceId)
        binary_sensors.append(CasambiPresenceBinarySensor(api, unit))

    if binary_sensors:
        _LOGGER.debug("Adding binary sensor entities...")
        async_add_entities(binary_sensors)
    else:
        _LOGGER.debug("No binary sensor entities available.")


class CasambiBinarySensorEntity(BinarySensorEntity, CasambiNetworkEntity):
    """Defines a Casambi Binary Sensor Entity."""

    def __init__(self, api: CasambiApi, description: BinarySensorEntityDescription):
        """Initialize a Casambi Binary Sensor Entity."""
        super().__init__(api=api, description=description)

    @property
    def is_on(self) -> bool:
        """Getter for state."""
        return self._api.available

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True


class TypedBinarySensorEntityDescription(
    TypedEntityDescription, BinarySensorEntityDescription
):
    """Describes a Casambi unit binary sensor."""


class CasambiPresenceBinarySensor(CasambiUnitEntity, BinarySensorEntity):
    """Presence reported by a Casambi motion detector.

    The unit type exposes a 2-bit PRESENCE control (0 = absent, >=1 = present).
    """

    def __init__(self, api: CasambiApi, unit: Unit) -> None:
        """Initialize the presence sensor."""
        super().__init__(
            api,
            TypedBinarySensorEntityDescription(
                key=str(unit.uuid),
                name="Presence",
                entity_type="presence",
            ),
            unit,
        )
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    @property
    def _presence(self) -> int | None:
        unit = cast("Unit", self._obj)
        if unit.state is None:
            return None
        return unit.state.presence

    @property
    def is_on(self) -> bool | None:
        """Return True if presence is detected."""
        presence = self._presence
        if presence is None:
            return None
        return presence > 0

    @property
    def extra_state_attributes(self) -> dict[str, int | None]:
        """Expose the raw presence level (0-3)."""
        return {"presence_level": self._presence}
