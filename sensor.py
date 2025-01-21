import logging
import homeassistant

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import STATE_UNKNOWN

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    STATE_CLASS_TOTAL,
)

from homeassistant.const import (
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_PASSWORD,
    CONF_USERNAME,
    CURRENCY_EURO,
    CURRENCY_CENT,
    UnitOfEnergy,
    UnitOfVolume,
)
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from homeassistant.exceptions import PlatformNotReady
from homeassistant.util import Throttle
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)
import requests
import json

from datetime import timedelta
from bs4 import BeautifulSoup
from cachetools import TTLCache

THROTTLE_INTERVAL_SECONDS = 100
ELECTRICITY_PRICE_FIXED = 0.0652

SCAN_INTERVAL = timedelta(minutes=15)
THROTTLE_INTERVAL = timedelta(seconds=THROTTLE_INTERVAL_SECONDS)

DEFAULT_NAME = "evohaus"
ATTR_UPDATA_TIME = "lastUpdateTime"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
    }
)

WARM_WATER_KITCHEN_METER = {
    "name": "warm_water_kitchen_meter",
    "icon": "mdi:countertop",
    "unit": UnitOfVolume.CUBIC_METERS,
    "description": "Verbrauch Warmwasser Küche",
    "device_class": SensorDeviceClass.WATER,
    "state_class": STATE_CLASS_TOTAL_INCREASING,
}
WARM_WATER_BATH_METER = {
    "name": "warm_water_bathroom_meter",
    "icon": "mdi:shower-head",
    "unit": UnitOfVolume.CUBIC_METERS,
    "description": "Verbrauch Warmwasser Bad",
    "device_class": SensorDeviceClass.WATER,
    "state_class": STATE_CLASS_TOTAL_INCREASING,
}
COLD_WATER_BATH_METER = {
    "name": "cold_water_bathroom_meter",
    "icon": "mdi:faucet",
    "unit": UnitOfVolume.CUBIC_METERS,
    "description": "Verbrauch Kaltwasser Bad",
    "device_class": SensorDeviceClass.WATER,
    "state_class": STATE_CLASS_TOTAL_INCREASING,
}
COLD_WATER_KITCHEN_METER = {
    "name": "cold_water_kitchen_meter",
    "icon": "mdi:countertop-outline",
    "unit": UnitOfVolume.CUBIC_METERS,
    "description": "Verbrauch Kaltwasser Küche",
    "device_class": SensorDeviceClass.WATER,
    "state_class": STATE_CLASS_TOTAL_INCREASING,
}
COLD_WATER_WASH_METER = {
    "name": "cold_water_wash_meter",
    "icon": "mdi:washing-machine",
    "unit": UnitOfVolume.CUBIC_METERS,
    "description": "Verbrauch Kaltwasser Waschmaschine",
    "device_class": SensorDeviceClass.WATER,
    "state_class": STATE_CLASS_TOTAL_INCREASING,
}
ELECTRIC_METER = {
    "name": "electricity_meter",
    "icon": "mdi:meter-electric-outline",
    "unit": UnitOfEnergy.KILO_WATT_HOUR,
    "description": "Verbrauch Strom",
    "device_class": SensorDeviceClass.ENERGY,
    "state_class": STATE_CLASS_TOTAL_INCREASING,
}
ELECTRIC_CONSUMPTION = {
    "name": "electricity_consumption",
    "icon": "mdi:solar-power",
    "unit": UnitOfEnergy.KILO_WATT_HOUR,
    "query": "Stromverbrauch",
    "device_class": SensorDeviceClass.ENERGY,
    "state_class": STATE_CLASS_TOTAL,
}
TOTAL_ELECTRIC_CONSUMPTION = {
    "name": "total_electricity_consumption",
    "icon": "mdi:solar-power",
    "unit": UnitOfEnergy.KILO_WATT_HOUR,
    "query": "Stromverbrauch",
    "device_class": SensorDeviceClass.ENERGY,
    "state_class": STATE_CLASS_TOTAL_INCREASING,
}
COLD_WATER_CONSUMPTION = {
    "name": "cold_water_consumption",
    "icon": "mdi:water",
    "unit": UnitOfVolume.CUBIC_METERS,
    "query": "Kaltwasser",
    "device_class": SensorDeviceClass.WATER,
    "state_class": STATE_CLASS_TOTAL,
}
WARM_WATER_CONSUMPTION = {
    "name": "warm_water_consumption",
    "icon": "mdi:shower-head",
    "unit": UnitOfVolume.CUBIC_METERS,
    "query": "Warmwasser",
    "device_class": SensorDeviceClass.WATER,
    "state_class": STATE_CLASS_TOTAL,
}
ELECTRIC_PRICE = {
    "name": "electricity_price",
    "icon": "mdi:currency-eur",
    "unit": f"{CURRENCY_CENT}/{UnitOfEnergy.KILO_WATT_HOUR}",
    "query": "Stromverbrauch",
    "device_class": SensorDeviceClass.MONETARY,
    "state_class": None,
}
ELECTRIC_PRICE_EURO = {
    "name": "electricity_price_euro",
    "icon": "mdi:currency-eur",
    "unit": f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}",
    "query": "Stromverbrauch",
    "device_class": SensorDeviceClass.MONETARY,
    "state_class": None,
}



def setup_platform(hass, config, add_devices, discovery_info=None):
    user = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    name = config.get(CONF_NAME)

    _LOGGER.info("Initializing Evohaus ...)")

    devices = []
    try:
        evohaus = Evohaus(user, password, hass)
        devices.append(ElectricConsumptionSensor(evohaus))
        devices.append(ElectricTotalConsumptionSensor(evohaus))
        devices.append(ColdWaterSensor(evohaus))
        devices.append(WarmWaterSensor(evohaus))
        devices.append(TrafficLightSensor(evohaus))
        devices.append(ElectricityPriceSensor(evohaus))
        devices.append(ElectricityMeterSensor(evohaus))
        devices.append(ColdWaterBathMeterSensor(evohaus))
        devices.append(ColdWaterWashMeterSensor(evohaus))
        devices.append(ColdWaterKitchenMeterSensor(evohaus))
        devices.append(WarmWaterBathMeterSensor(evohaus))
        devices.append(WarmWaterKitchenMeterSensor(evohaus))

    except HomeAssistantError:
        _LOGGER.exception("Fail to setup Evohaus")
        raise PlatformNotReady

    add_devices(devices)


class Evohaus:
    def __init__(self, user, password, hass):
        self._cookie = None
        self._meter_data = None
        self._user = user
        self._password = password
        # self._domain = "http://0003.evohaus-irq.com:48888/"
        self._domain = "https://ems003.enocoo.com:48889/"
        self.__login()
        self.residenceId = self._get_residence()
        self._data_source = None
        self.cache = TTLCache(maxsize=1, ttl=THROTTLE_INTERVAL_SECONDS)
        self.hass = hass

    def __login(self):
        _LOGGER.debug("Start login....")
        payload = {"user": self._user, "passwort": self._password}
        url = self._domain + "signinForm.php?mode=ok"
        with requests.Session() as s:
            r = s.get(url)
            self._cookie = {"PHPSESSID": r.cookies["PHPSESSID"]}
            s.post(url, data=payload, cookies=self._cookie)
        if self._cookie is None:
            _LOGGER.error("Cannot login")
        else:
            _LOGGER.debug("Login successful")

    def _get_residence(self):
        url = self._domain + "/php/ownConsumption.php"
        with requests.Session() as s:
            r = s.get(url, cookies=self._cookie)
        content = BeautifulSoup(r.content, "html.parser")
        return content.find("label", {"for": "residence"}).parent.find(
            "a", {"class": "pdm"}
        )["id"]

    def sync_meter_data(self):
        if "meter_data" not in self.cache:
            url = self._domain + "/php/newMeterTable.php"
            now = homeassistant.util.dt.now()  # current date and time
            today = now.strftime("%Y-%m-%d")
            payload = {"dateParam": today}

            with requests.Session() as s:
                r = s.post(url, data=payload, cookies=self._cookie)
                if len(r.content) == 0:
                    self.__login()
                    r = s.post(url, data=payload, cookies=self._cookie)
                self.cache["meter_data"] = BeautifulSoup(r.content, "html.parser")
            if self._cookie is None:
                _LOGGER.error("Cannot fetch meter data")
            else:
                _LOGGER.debug(self._meter_data)
        self._meter_data = self.cache["meter_data"]

    def fetch_meter_data(self, meterType):
        rows = self._meter_data.find_all("tr")
        row = {"state": 0, "meter_no": ""}

        for raw_row in rows:
            _LOGGER.debug("row content: " + str(raw_row))
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

    def fetch_traffic_data(self):
        url = self._domain + "/php/getTrafficLightStatus.php"
        with requests.Session() as s:
            r = s.get(url, cookies=self._cookie)
            trafficRaw = json.loads(r.content)
        if self._cookie is None:
            _LOGGER.error("Cannot fetch traffic data")
        else:
            _LOGGER.debug(trafficRaw)
        return trafficRaw

    def fetch_chart_data(self, dataType):
        """Parse data."""
        now = homeassistant.util.dt.now()  # current date and time
        today = now.strftime("%Y-%m-%d")
        url = (
                self._domain
                + "php/getMeterDataWithParam.php?from="
                + today
                + "&intVal=Tag&mClass="
                + dataType
                + "&AreaId="
                + self.residenceId
        )
        data = None
        with requests.Session() as s:
            r = s.get(url, cookies=self._cookie)
            data = json.loads(r.content)
        if data is None or len(data[0]) == 0:
            _LOGGER.error("Cannot fetch data: " + url)
        else:
            _LOGGER.debug(data)
        return data


class EvoSensor(SensorEntity):
    def __init__(self, evohaus, config):
        self._updateTime = "unknown"
        self._state = STATE_UNKNOWN
        self._evohaus = evohaus
        self._config = config
        self._total = 0
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._config["name"]

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._config["icon"]

    @property
    def native_value(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._config["unit"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = {"updateTime": self._updateTime}
        return attrs

    @Throttle(THROTTLE_INTERVAL)
    def update(self):
        """Get the latest data and updates the states."""
        self._evohaus.sync_meter_data()
        self.parse_data()

    @property
    def native_unit_of_measurement(self) -> str:
        """Return percentage."""
        return self._config["unit"]

    @property
    def state_class(self):
        return self._config["state_class"]

    @property
    def device_class(self):
        """Device class of this entity."""
        return self._config["device_class"]


class MeterSensor(EvoSensor):
    def __init__(self, evohaus, config):
        super().__init__(evohaus, config)

    @property
    def state_class(self):
        return self._config["state_class"]
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = super().extra_state_attributes
        attrs["meter_no"] = self._meter_no
        return attrs

    def parse_data(self):
        meter_data = self._evohaus.fetch_meter_data(self._config["description"])
        new_state = meter_data["state"]
        try:
            if float(new_state) >= float(self._state):
                self._state = new_state
        except ValueError:  # if history state does not exists
            self._state = new_state
        self._meter_no = meter_data["meter_no"]
        self._updateTime = homeassistant.util.dt.now().strftime("%H:%M")


class ColdWaterBathMeterSensor(MeterSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, COLD_WATER_BATH_METER)


class ColdWaterKitchenMeterSensor(MeterSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, COLD_WATER_KITCHEN_METER)


class ColdWaterWashMeterSensor(MeterSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, COLD_WATER_WASH_METER)


class ElectricityMeterSensor(MeterSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, ELECTRIC_METER)


class WarmWaterBathMeterSensor(MeterSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, WARM_WATER_BATH_METER)


class WarmWaterKitchenMeterSensor(MeterSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, WARM_WATER_KITCHEN_METER)

class ElectricTotalConsumptionSensor(EvoSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, TOTAL_ELECTRIC_CONSUMPTION)
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = super().extra_state_attributes
        attrs["total_cost_today"] = self._total_cost
        return attrs

    def parse_data(self):
        electric_data = self._evohaus.fetch_chart_data(self._config["query"])
        self._state = 0
        self._total_cost = 0
        
        for i in range(len(electric_data[1])):
            if i % 4 == 0:
                minute = "00"
            else:
                minute = str(int(i % 4 * 15))
            
            if electric_data[0][i] != None:
                self._state += electric_data[0][i]
                self._total_cost += electric_data[0][i] * (electric_data[2][i] + ELECTRICITY_PRICE_FIXED)
                self._updateTime = str(electric_data[1][i]) + ":" + minute
        
class ElectricConsumptionSensor(EvoSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, ELECTRIC_CONSUMPTION)
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = super().extra_state_attributes
        return attrs

    def parse_data(self):
        electric_data = self._evohaus.fetch_chart_data(self._config["query"])
        self._state = 0
        
        for i in range(len(electric_data[1])):
            if i % 4 == 0:
                minute = "00"
            else:
                minute = str(int(i % 4 * 15))
            
            self._state = 0
            
            if electric_data[0][i] != None and i % 4 == 0 and i > 0:
                self._state = electric_data[0][i-1] + electric_data[0][i-2] + electric_data[0][i-3] + electric_data[0][i-4]
                self._updateTime = str(electric_data[1][i]) + ":" + minute


class ColdWaterSensor(EvoSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, COLD_WATER_CONSUMPTION)
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = super().extra_state_attributes
        attrs["total_consumption_today"] = self._total
        attrs["current_consumption"] = self._current_consumption
        return attrs

    def parse_data(self):
        water_data = self._evohaus.fetch_chart_data(self._config["query"])
        self._state = 0
        self._current_consumption = 0
        self._total = 0
        
        for i in range(len(water_data[1])):
            if i % 4 == 0:
                minute = "00"
            else:
                minute = str(int(i % 4 * 15))
                
            update_string = str(water_data[1][i]) + ":" + minute
            self._current_consumption = 0
            
            if water_data[0][i] != None:
                self._total += water_data[0][i]
                self._updateTime = update_string
                
                if i % 4 == 0 and i > 0:
                  self._current_consumption = water_data[0][i-1] + water_data[0][i-2] + water_data[0][i-3] + water_data[0][i-4]
                
        self._state = self._current_consumption


class WarmWaterSensor(EvoSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, WARM_WATER_CONSUMPTION)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = super().extra_state_attributes
        attrs["total_consumption_today"] = self._total
        attrs["current_consumption"] = self._current_consumption
        return attrs

    def parse_data(self):
        water_data = self._evohaus.fetch_chart_data(self._config["query"])
        self._state = 0
        self._current_consumption = 0
        self._total = 0
        
        for i in range(len(water_data[1])):
            if i % 4 == 0:
                minute = "00"
            else:
                minute = str(int(i % 4 * 15))
                
            update_string = str(water_data[1][i]) + ":" + minute
            self._current_consumption = 0
            
            if water_data[0][i] != None:
                self._total += water_data[0][i]
                self._updateTime = update_string
                
                if i % 4 == 0 and i > 0:
                  self._current_consumption = water_data[0][i-1] + water_data[0][i-2] + water_data[0][i-3] + water_data[0][i-4]
                
        self._state = self._current_consumption

class ElectricityPriceSensor(EvoSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, ELECTRIC_PRICE_EURO)
        
    def parse_data(self):
        self._updateTime = homeassistant.util.dt.now().strftime("%H:%M")
        raw_data = self._evohaus.fetch_traffic_data()
        self._traffic_light = raw_data["color"]
        self._state = round((raw_data["currentEnergyprice"] + ELECTRICITY_PRICE_FIXED)/100, 2)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = super().extra_state_attributes
        attrs["traffic_light"] = self._traffic_light
        return attrs

class TrafficLightSensor(EvoSensor):
    def __init__(self, evohaus):
        super().__init__(evohaus, ELECTRIC_PRICE)
        
    def parse_data(self):
        self._updateTime = homeassistant.util.dt.now().strftime("%H:%M")
        raw_data = self._evohaus.fetch_traffic_data()
        self._traffic_light = raw_data["color"]
        self._state = round(raw_data["currentEnergyprice"] + ELECTRICITY_PRICE_FIXED, 2)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = super().extra_state_attributes
        attrs["traffic_light"] = self._traffic_light
        return attrs
