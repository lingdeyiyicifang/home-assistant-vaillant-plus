|CODE_EDIT_BLOCK|c:/Users/zhen/OneDrive/桌面/vaillant/custom_components/vaillant_plus/water_heater.py
"""Support for water heaters."""
from __future__ import annotations

import logging

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
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

SUPPORT_FLAGS = WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.OPERATION_MODE
OPERATION_LIST = ["off", "eco", "comfort"]

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Vaillant water heater."""
    coordinator: VaillantCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [VaillantWaterHeater(coordinator, entry.data[CONF_DURATION_CONTROL])]
    async_add_entities(entities, True)

class VaillantWaterHeater(VaillantEntity, WaterHeaterEntity):
    """Vaillant Water Heater."""

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the name of the water heater."""
        return f"{DEFAULT_NAME} Water Heater"

    @property
    def unique_id(self):
        """Return a unique identifier for the water heater."""
        return f"{self.coordinator.system_id}_water_heater"

    @property
    def current_operation(self):
        """Return current operation."""
        if not self.system.system_status.dhw_status:
            return "off"
        elif self.system.system_status.dhw_status.mode == "eco":
            return "eco"
        else:
            return "comfort"

    @property
    def operation_list(self):
        """List of available operation modes."""
        return OPERATION_LIST

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self.system.system_status.dhw_temperature is not None:
            return self.system.system_status.dhw_temperature
        return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        if self.system.system_status.dhw_setpoint is not None:
            return self.system.system_status.dhw_setpoint
        return None

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 30

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 80

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.coordinator.api.set_hot_water_setpoint(
                self.system.system_status.device_id,
                self.coordinator.system_id,
                int(temperature),
            )
            self.coordinator.set_hot_water_setpoint(int(temperature))
            await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        if operation_mode == "off":
            await self.coordinator.api.set_hot_water_device_status(
                self.system.system_status.device_id,
                self.coordinator.system_id,
                False,
            )
        else:
            await self.coordinator.api.set_hot_water_operating_mode(
                self.system.system_status.device_id,
                self.coordinator.system_id,
                operation_mode,
            )
            await self.coordinator.async_request_refresh()
