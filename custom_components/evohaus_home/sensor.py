"""Platform for sensor integration."""
import homeassistant
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Evohaus sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = [
        TrafficLightSensor(coordinator),
        ElectricityPriceSensor(coordinator),
        ElectricityPriceEuroSensor(coordinator),
        ElectricityMeterSensor(coordinator),
        ColdWaterBathMeterSensor(coordinator),
        ColdWaterKitchenMeterSensor(coordinator),
        ColdWaterWashMeterSensor(coordinator),
        WarmWaterBathMeterSensor(coordinator),
        WarmWaterKitchenMeterSensor(coordinator),
    ]

    async_add_entities(sensors, True)


class EvoSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Evo Sensor."""

    def __init__(self, coordinator, name, icon):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self):
        """Return the state of the device."""
        return self.coordinator.data.get("state")

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return self._attr_extra_state_attributes

    @property
    def device_info(self):
        """Return device information about this sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, "evohaus_home")},
            name="Evohaus Home",
            manufacturer="Evohaus",
        )

class MeterSensor(EvoSensor):
    """Meter Sensor specific implementation."""

    def __init__(self, coordinator, name, icon):
        super().__init__(coordinator, name, icon)
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    async def async_update(self):
        """Get the latest data and update the state."""
        await super().async_update()
        meter_data = await self.coordinator.fetch_meter_data()
        new_state = self.extract_meter_data(meter_data, self._attr_name)
        try:
            if float(new_state['state']) >= float(self._attr_native_value):
                self._attr_native_value = new_state['state']
        except ValueError:  # if history state does not exist
            self._attr_native_value = new_state['state']
        self._attr_extra_state_attributes["meter_no"] = new_state['meter_no']
        self._attr_extra_state_attributes["updateTime"] = homeassistant.util.dt.now().strftime("%H:%M")

    def extract_meter_data(self, meterData, meterType):
        rows = meterData.find_all("tr")
        row = {"state": 0, "meter_no": ""}

        for raw_row in rows:
            cols = raw_row.find_all("td")
            if not cols:
                continue

            unit = cols[0].contents[0]
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


class TrafficLightSensor(EvoSensor):
    """Traffic Light Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Traffic Light", "mdi:traffic-light")

    async def async_update(self):
        """Get the latest data and update the state."""
        await super().async_update()
        self._attr_native_value = 'test'
        self._attr_extra_state_attributes["price"] = round(
            50, 2
        )


class ElectricityPriceSensor(EvoSensor):
    """Electricity Price Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Electricity Price", "mdi:currency-eur")

    async def async_update(self):
        """Get the latest data and update the state."""
        await super().async_update()
        self._attr_native_value = round(50, 2)
        self._attr_extra_state_attributes["traffic_light"] = 'test'


class ElectricityPriceEuroSensor(EvoSensor):
    """Electricity Price Euro Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Electricity Price Euro", "mdi:currency-eur")

    async def async_update(self):
        """Get the latest data and update the state."""
        await super().async_update()
        self._attr_native_value = round(50 / 100, 2)
        self._attr_extra_state_attributes["traffic_light"] = 'test'

class ColdWaterBathMeterSensor(MeterSensor):
    """Cold Water Bath Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Verbrauch Kaltwasser Bad", "mdi:faucet")


class ColdWaterKitchenMeterSensor(MeterSensor):
    """Cold Water Kitchen Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Verbrauch Kaltwasser Küche", "mdi:countertop-outline")


class ColdWaterWashMeterSensor(MeterSensor):
    """Cold Water Wash Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Verbrauch Kaltwasser Waschmaschine", "mdi:washing-machine")


class ElectricityMeterSensor(MeterSensor):
    """Electricity Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Verbrauch Strom", "mdi:meter-electric-outline")


class WarmWaterBathMeterSensor(MeterSensor):
    """Warm Water Bath Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Verbrauch Warmwasser Bad", "mdi:shower-head")


class WarmWaterKitchenMeterSensor(MeterSensor):
    """Warm Water Kitchen Meter Sensor specific implementation."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Verbrauch Warmwasser Küche", "mdi:countertop")