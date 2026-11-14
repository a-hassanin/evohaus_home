"""Regression tests for parking meter extraction and entity IDs."""

import ast
from html.parser import HTMLParser
import logging
from pathlib import Path
import re
from types import SimpleNamespace
import unittest


class Element:
    def __init__(self):
        self.children = []

    def find_all(self, tag):
        return [child for child in self.children if child.tag == tag]


class Cell:
    tag = "td"

    def __init__(self):
        self.contents = []


class Row(Element):
    tag = "tr"


class TableParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.table = Element()
        self.row = None
        self.cell = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = Row()
            self.table.children.append(self.row)
        elif tag == "td":
            self.cell = Cell()
            self.row.children.append(self.cell)

    def handle_endtag(self, tag):
        if tag == "td":
            self.cell = None
        elif tag == "tr":
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.contents.append(data)


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


class SensorEntity:
    pass


def load_sensor_classes():
    """Run the actual entity classes with Home Assistant interfaces stubbed."""
    path = Path(__file__).resolve().parents[1] / "custom_components/evohaus_home/sensor.py"
    tree = ast.parse(path.read_text())
    classes = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name in ("EvoSensor", "ParkingMeterSensor")
    ]
    module = ast.fix_missing_locations(ast.Module(body=classes, type_ignores=[]))
    namespace = {
        "CoordinatorEntity": CoordinatorEntity,
        "SensorEntity": SensorEntity,
        "callback": lambda func: func,
        "slugify": lambda text: re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_"),
        "re": re,
        "_LOGGER": logging.getLogger("test.parking_sensor"),
        "UnitOfEnergy": SimpleNamespace(KILO_WATT_HOUR="kWh"),
        "SensorDeviceClass": SimpleNamespace(ENERGY="energy"),
        "SensorStateClass": SimpleNamespace(TOTAL_INCREASING="total_increasing"),
    }
    exec(compile(module, str(path), "exec"), namespace)
    return namespace


class ParkingSensorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classes = load_sensor_classes()

    def coordinator(self, html):
        return SimpleNamespace(
            residenceId="H20W18",
            data={"meter": TableParser(html).table},
        )

    def test_extracts_parking_row_and_preserves_existing_id(self):
        coordinator = self.coordinator(
            "<table><tr><th>Fläche</th></tr>"
            "<tr><td>C4.1 Stpl038 Tn 136</td>"
            "<td>Verbrauch Strom C4.1 Stpl038 Tn 136</td>"
            "<td>01885083</td><td>14.11.2026 00:15:00</td>"
            "<td>1.733,69</td><td>kWh</td></tr></table>"
        )
        sensor = self.classes["ParkingMeterSensor"](coordinator)
        self.assertEqual(sensor._extract_parking_meter_data(coordinator.data["meter"]), {
            "state": 1733.69,
            "meter_no": "01885083",
            "parking_number": "136",
            "parking_code": "038",
        })
        self.assertEqual(sensor.entity_id, "sensor.electricity_consumption_parking_136_h20w18")

    def test_missing_parking_meter_has_valid_id_and_warns(self):
        coordinator = self.coordinator(
            "<table><tr><th>Fläche</th></tr>"
            "<tr><td>H20W18</td><td>Verbrauch Strom H20W18</td>"
            "<td>00403414</td><td>14.11.2026 00:15:00</td>"
            "<td>21.062,15</td><td>kWh</td></tr></table>"
        )
        with self.assertLogs("test.parking_sensor", level="WARNING") as logs:
            sensor = self.classes["ParkingMeterSensor"](coordinator)
        self.assertEqual(sensor.entity_id, "sensor.electricity_consumption_parking_h20w18")
        self.assertIn("No matching parking electricity meter", logs.output[0])

    def test_slugifies_name_and_residence(self):
        coordinator = self.coordinator("<table></table>")
        coordinator.residenceId = "H20-W18"
        sensor = self.classes["EvoSensor"](coordinator, "Electricity / Parking ", "mdi:home")
        self.assertEqual(sensor.entity_id, "sensor.electricity_parking_h20_w18")


if __name__ == "__main__":
    unittest.main()
