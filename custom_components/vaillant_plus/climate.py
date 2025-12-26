|CODE_EDIT_BLOCK|c:/Users/zhen/OneDrive/桌面/vaillant/custom_components/vaillant_plus/climate.py
"""Support for climate."""
from __future__ import annotations

import logging

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import (
    HVACMode,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import (
    CONF_DURATION_CONTROL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .entity import VaillantCoordinator, VaillantEntity

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
HVAC_MODES = [HVACMode.HEAT, HVACMode.OFF]
PRESET_MODES = [PRESET_COMFORT, PRESET_ECO, PRESET_NONE]

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Vaillant climate."""
    coordinator: VaillantCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [VaillantClimate(coordinator, entry.data[CONF_DURATION_CONTROL])]
    async_add_entities(entities, True)

class VaillantClimate(VaillantEntity, ClimateEntity):
    """Vaillant Climate."""

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the name of the climate."""
        return f"{DEFAULT_NAME} Climate"

    @property
    def unique_id(self):
        """Return a unique identifier for the climate."""
        return f"{self.coordinator.system_id}_climate_{self._hc_id}"

    @property
    def _hc_id(self):
        """Return the heating circuit ID."""
        return self.system.system_status.hc_status.hc_id

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        return HVAC_MODES

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        if not self.system.system_status.hc_status.is_heating_allowed:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return PRESET_MODES

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self.system.system_status.hc_status.mode == "eco":
            return PRESET_ECO
        elif self.system.system_status.hc_status.mode == "comfort":
            return PRESET_COMFORT
        return PRESET_NONE

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self.system.system_status.hc_status.room_temperature is not None:
            return self.system.system_status.hc_status.room_temperature
        return None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.system.system_status.hc_status.room_setpoint is not None:
            return self.system.system_status.hc_status.room_setpoint
        return None

    @property
    def hvac_action(self):
        """Return the current running hvac operation."""
        if self.system.system_status.hc_status.is_burning:
            return "heating"
        return "idle"

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 5

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 40

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.coordinator.api.set_room_temperature(
                self.system.system_status.device_id,
                self.coordinator.system_id,
                self._hc_id,
                temperature,
            )
            self.coordinator.set_room_temperature(self._hc_id, temperature)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.api.set_heating_circuit_device_status(
                self.system.system_status.device_id,
                self.coordinator.system_id,
                self._hc_id,
                False,
            )
        else:
            await self.coordinator.api.set_heating_circuit_device_status(
                self.system.system_status.device_id,
                self.coordinator.system_id,
                self._hc_id,
                True,
            )
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        mode = "comfort" if preset_mode == PRESET_COMFORT else "eco" if preset_mode == PRESET_ECO else "normal"
        await self.coordinator.api.set_heating_circuit_operating_mode(
            self.system.system_status.device_id,
            self.coordinator.system_id,
            self._hc_id,
            mode,
        )
        await self.coordinator.async_request_refresh()
