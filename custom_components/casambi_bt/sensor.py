"""Sensor platform for Casambi units (illuminance of motion detectors)."""

import logging
from typing import cast

from CasambiBt import Unit, UnitControlType

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import LIGHT_LUX
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CasambiApi
from .const import DOMAIN
from .entities import CasambiUnitEntity, TypedEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Casambi sensor entities."""
    api: CasambiApi = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        CasambiIlluminanceSensor(api, unit)
        for unit in api.get_units([UnitControlType.LUX])
    ]
    _LOGGER.debug("Adding %i illuminance sensor(s)", len(entities))
    async_add_entities(entities)


class TypedSensorEntityDescription(TypedEntityDescription, SensorEntityDescription):
    """Describes a Casambi unit sensor."""


class CasambiIlluminanceSensor(CasambiUnitEntity, SensorEntity):
    """Illuminance reported by a Casambi motion detector (LUX control)."""

    def __init__(self, api: CasambiApi, unit: Unit) -> None:
        """Initialize the illuminance sensor."""
        super().__init__(
            api,
            TypedSensorEntityDescription(
                key=str(unit.uuid),
                name="Illuminance",
                entity_type="illuminance",
            ),
            unit,
        )
        # Set via _attr_*: TypedEntityDescription's __init__ only knows the
        # generic EntityDescription fields.
        self._attr_device_class = SensorDeviceClass.ILLUMINANCE
        self._attr_native_unit_of_measurement = LIGHT_LUX
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the illuminance as reported by the unit."""
        unit = cast("Unit", self._obj)
        if unit.state is None:
            return None
        return unit.state.lux
