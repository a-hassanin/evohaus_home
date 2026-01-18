"""Platform for sensor integration."""
import homeassistant
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.const import (
    CURRENCY_EURO,
    CURRENCY_CENT,
    UnitOfEnergy,
    UnitOfVolume
)

import re
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Evohaus sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = [
        EvoSensor(coordinator, "Evohaus Home", "mdi:home", "Evohaus Home"),
        ElectricityPriceSensor(coordinator),
        ElectricityPriceEuroSensor(coordinator),
        ElectricityMeterSensor(coordinator),
        ParkingMeterSensor(coordinator),
        ColdWaterBathMeterSensor(coordinator),
        ColdWaterKitchenMeterSensor(coordinator),
        ColdWaterWashMeterSensor(coordinator),
        WarmWaterBathMeterSensor(coordinator),
        WarmWaterKitchenMeterSensor(coordinator),
    ]

    async_add_entities(sensors, True)


class EvoSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Evo Sensor."""

    def __init__(self, coordinator, name, icon, tech_name="", unit=None, device_class=None, state_class=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_tech_name = tech_name
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unit = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
        self.entity_id = f"sensor.{name.lower().replace(' ', '_') + '_' + coordinator.residenceId.lower()}"

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def native_unit_of_measurement(self):
        return self._attr_unit

    @property
    def extra_state_attributes(self):
        self._attr_extra_state_attributes["updateTime"] = homeassistant.util.dt.now().strftime("%H:%M")
        return self._attr_extra_state_attributes

    @property
    def device_class(self):
        """Device class of this entity."""
        return self._attr_device_class

    @property
    def state_class(self):
        return self._attr_state_class

    @property
    def device_info(self):
        """Return device information about this sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, "evohaus_home")},
            name="Evohaus Home",
            manufacturer="Evohaus",
        )

    @callback
    def _handle_coordinator_update(self):
        self.async_write_ha_state()


class ParkingMeterSensor(EvoSensor):
    def __init__(self, coordinator):
        meter_data_extracted = self._extract_parking_meter_data(coordinator.data["meter"])
        super().__init__(coordinator, "Electricity consumption parking " + meter_data_extracted.get("parking_number"), "mdi:meter-electric-outline", "Verbrauch Strom", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING)

    @callback
    def _handle_coordinator_update(self):
        meter_data_extracted = self._extract_parking_meter_data(self.coordinator.data["meter"])
        state = meter_data_extracted.get("state")

        if state is not None and int(state) > 0 and (self._attr_native_value is None or state > self._attr_native_value):
            self._attr_native_value = state
            self._attr_extra_state_attributes["meter_no"] = meter_data_extracted.get("meter_no")
            self._attr_extra_state_attributes["parking_number"] = meter_data_extracted.get("parking_number")
            self._attr_extra_state_attributes["parking_code"] = meter_data_extracted.get("parking_code")
            super()._handle_coordinator_update()

    def _extract_stellplatz_and_tn(self, input_string):
        result = {
            "stellplatz": "",
            "tn": ""
        }
    
        # Stellplatz: Stpl038, Stlp.242, STPL 12
        stpl_match = re.search(
            r'\bStpl\.?\s*(\d+)\b',
            input_string,
            re.IGNORECASE
        )
    
        # T-Number: Tn 136, TNr 271
        tn_match = re.search(
            r'\bTnR?\s*(\d+)\b',
            input_string,
            re.IGNORECASE
        )
    
        if stpl_match:
            result["stellplatz"] = stpl_match.group(1)
    
        if tn_match:
            result["tn"] = tn_match.group(1)
    
        return result
    
    def _extract_parking_meter_data(self, meter_data):
        rows = meter_data.find_all("tr")
        row = {"state": 0, "meter_no": "", "parking_number": "", "parking_code": ""}

        for raw_row in rows:
            cols = raw_row.find_all("td")
            if not cols:
                continue

            unit = cols[0].contents[0]
            description = cols[1].contents[0].replace(" " + unit, "")
            
            if "Verbrauch Strom" in description:
                parking_data = self._extract_stellplatz_and_tn(unit)
                
                if not bool(parking_data.get("stellplatz") and parking_data.get("tn")):
                    continue
                
                row["state"] = float(
                    cols[4].contents[0].replace(".", "").replace(",", ".")
                )
                row["meter_no"] = cols[2].contents[0]
                row["parking_number"] = parking_data.get("tn")
                row["parking_code"] = parking_data.get("stellplatz")
                return row
            else:
                continue

        return row

class MeterSensor(EvoSensor):
    def __init__(self, coordinator, name, icon, tech_name, unit, device_class):
        super().__init__(coordinator, name, icon, tech_name, unit, device_class, SensorStateClass.TOTAL_INCREASING)

    @callback
    def _handle_coordinator_update(self):
        meter_data_extracted = self.extract_meter_data(self.coordinator.data["meter"], self._attr_tech_name)
        state = meter_data_extracted.get("state")

        if state is not None and int(state) > 0 and (self._attr_native_value is None or state > self._attr_native_value):
          self._attr_native_value = state
          self._attr_extra_state_attributes["meter_no"] = meter_data_extracted['meter_no']
          
        super()._handle_coordinator_update()

    def extract_meter_data(self, meterData, meterType):
        rows = meterData.find_all("tr")
        row = {"state": 0, "meter_no": ""}

        for raw_row in rows:
            cols = raw_row.find_all("td")
            if not cols:
                continue

            unit = cols[0].contents[0]
            if "Stpl" in unit:
                continue
                
            description = cols[1].contents[0].replace(" " + unit, "")
            if description == meterType:
                row["state"] = float(
                    cols[4].contents[0].replace(".", "").replace(",", ".")
                )
                row["meter_no"] = cols[2].contents[0]
                return row
            else:
                continue

        return row

class WaterMeterSensor(MeterSensor):
    def __init__(self, coordinator, name, icon, tech_name):
        super().__init__(coordinator, name, icon, tech_name, UnitOfVolume.CUBIC_METERS, SensorDeviceClass.WATER)

class ElectricityPriceSensor(EvoSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "Electricity Price", "mdi:currency-eur", "", f"{CURRENCY_CENT}/{UnitOfEnergy.KILO_WATT_HOUR}", SensorDeviceClass.MONETARY)

    @callback
    def _handle_coordinator_update(self):
        traffic = self.coordinator.data.get("traffic")
        raw_value_price = traffic.get("currentEnergyprice")
        traffic_color = traffic.get("color")

        if raw_value_price is not None:
            self._attr_native_value = round(raw_value_price, 2)
            self._attr_extra_state_attributes["traffic_light"] = traffic_color
            super()._handle_coordinator_update()

class ElectricityPriceEuroSensor(EvoSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "Electricity Price Euro", "mdi:currency-eur", "", f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}", SensorDeviceClass.MONETARY)

    @callback
    def _handle_coordinator_update(self):
        traffic = self.coordinator.data.get("traffic")
        raw_value_price = traffic.get("currentEnergyprice")
        traffic_color = traffic.get("color")

        if raw_value_price is not None:
            self._attr_native_value = round(raw_value_price / 100, 2)
            self._attr_extra_state_attributes["traffic_light"] = traffic_color
            super()._handle_coordinator_update()

class ElectricityMeterSensor(MeterSensor):
    def __init__(self, coordinator):
        super().__init__(coordinator, "Electricity consumption", "mdi:meter-electric-outline", "Verbrauch Strom", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY)

class ColdWaterBathMeterSensor(WaterMeterSensor):
    """Cold Water Bath Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Cold water bath consumption", "mdi:faucet", "Verbrauch Kaltwasser Bad")

class ColdWaterKitchenMeterSensor(WaterMeterSensor):
    """Cold Water Kitchen Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Cold water kitchen consumption", "mdi:countertop-outline", "Verbrauch Kaltwasser Küche")

class ColdWaterWashMeterSensor(WaterMeterSensor):
    """Cold Water Wash Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Washing machine water consumption", "mdi:washing-machine", "Verbrauch Kaltwasser Waschmaschine")

class WarmWaterBathMeterSensor(WaterMeterSensor):
    """Warm Water Bath Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Warm water bath consumption", "mdi:shower-head", "Verbrauch Warmwasser Bad")

class WarmWaterKitchenMeterSensor(WaterMeterSensor):
    """Warm Water Kitchen Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Warm water kitchen consumption", "mdi:countertop", "Verbrauch Warmwasser Küche")










