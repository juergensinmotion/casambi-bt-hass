"""Event platform for battery-less EnOcean switches paired to a Casambi network."""

import logging
from typing import Any, cast

from CasambiBt import Unit

from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CasambiApi
from .const import DOMAIN, KINETIC_SWITCH_BUTTONS, KINETIC_SWITCH_MODE
from .entities import CasambiUnitEntity, TypedEntityDescription

_LOGGER = logging.getLogger(__name__)

# Names of CasambiBt.ButtonEventType, lower-cased for Home Assistant.
EVENT_TYPES: list[str] = ["press", "release", "hold", "release_after_hold"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one event entity per button of every kinetic switch."""
    api: CasambiApi = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[CasambiSwitchButtonEvent] = []
    for unit in api.get_units():
        if unit.unitType.mode != KINETIC_SWITCH_MODE:
            continue
        _LOGGER.debug(
            "Adding %i button event entities for switch unit %i (%s)",
            KINETIC_SWITCH_BUTTONS,
            unit.deviceId,
            unit.unitType.model,
        )
        entities.extend(
            CasambiSwitchButtonEvent(api, unit, button)
            for button in range(1, KINETIC_SWITCH_BUTTONS + 1)
        )
    async_add_entities(entities)


class TypedEventEntityDescription(TypedEntityDescription, EventEntityDescription):
    """Describes a Casambi switch button event."""


class CasambiSwitchButtonEvent(CasambiUnitEntity, EventEntity):
    """One button (rocker contact) of an EnOcean switch.

    Fed by CasambiBt switch events, so it only fires while the network
    connection is up. The raw events are also fired on the bus as
    ``casambi_bt_switch_event``.
    """

    def __init__(self, api: CasambiApi, unit: Unit, button: int) -> None:
        """Initialize the button event entity."""
        self._button = button
        super().__init__(
            api,
            TypedEventEntityDescription(
                key=f"{unit.uuid}-button-{button}",
                name=f"Button {button}",
                entity_type=f"button_{button}",
            ),
            unit,
        )
        self._attr_device_class = EventDeviceClass.BUTTON
        self._attr_event_types = EVENT_TYPES

    @property
    def available(self) -> bool:
        """Kinetic switches have no radio of their own; follow the network."""
        return self._api.available

    @callback
    def _switch_event(self, event: Any) -> None:
        if getattr(event, "button", None) != self._button:
            return
        action = getattr(event, "event", None)
        event_type = (getattr(action, "name", None) or str(action)).lower()
        if event_type not in EVENT_TYPES:
            _LOGGER.debug("Ignoring switch event type %s", event_type)
            return
        self._trigger_event(event_type)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register for switch events of this unit."""
        await super().async_added_to_hass()
        unit = cast("Unit", self._obj)
        self._api.register_switch_listener(unit.deviceId, self._switch_event)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister from switch events."""
        unit = cast("Unit", self._obj)
        self._api.unregister_switch_listener(unit.deviceId, self._switch_event)
        await super().async_will_remove_from_hass()
