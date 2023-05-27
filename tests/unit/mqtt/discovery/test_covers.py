"""Test MQTT for Home Assistant covers."""

import asyncio
from asyncio import Task
from contextlib import AsyncExitStack
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from unittest.mock import AsyncMock

import pytest
from _pytest.logging import LogCaptureFixture  # pylint: disable=import-private-name
from asyncio_mqtt import Client

from tests.unit.conftest_data import CONFIG_CONTENT
from tests.unit.conftest_data import EXTENSION_HARDWARE_DATA_CONTENT
from tests.unit.conftest_data import HARDWARE_DATA_CONTENT
from unipi_control.config import DEVICE_CLASSES
from unipi_control.integrations.covers import CoverMap
from unipi_control.mqtt.discovery.covers import HassCoversMqttPlugin
from unipi_control.neuron import Neuron


class TestHappyPathHassCoversMqttPlugin:
    @pytest.mark.parametrize(
        "config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    def test_init_tasks(self, neuron: Neuron, covers: CoverMap, caplog: LogCaptureFixture) -> None:
        """Test MQTT output after initialize Home Assistant covers."""

        async def run() -> None:
            mock_mqtt_client: AsyncMock = AsyncMock(spec=Client)
            plugin: HassCoversMqttPlugin = HassCoversMqttPlugin(
                neuron=neuron, mqtt_client=mock_mqtt_client, covers=covers
            )

            async with AsyncExitStack() as stack:
                tasks: Set[Task] = set()

                await stack.enter_async_context(mock_mqtt_client)
                await plugin.init_tasks(tasks)
                await asyncio.gather(*tasks)

                for task in tasks:
                    assert task.done() is True

            logs: List[str] = [record.getMessage() for record in caplog.records]
            assert (
                "[MQTT] [homeassistant/cover/mocked_unipi_mocked_blind_topic_name/config] "
                "Publishing message: {"
                '"name": "MOCKED_FRIENDLY_NAME - BLIND", '
                '"unique_id": "mocked_unipi_mocked_blind_topic_name", '
                '"command_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/set", '
                '"state_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/state", '
                '"qos": 2, '
                '"optimistic": false, '
                '"device": {'
                '"name": "MOCKED UNIPI", '
                '"identifiers": "MOCKED UNIPI", '
                '"model": "MOCKED_NAME MOCKED_MODEL", '
                '"manufacturer": "Unipi technology"}, '
                '"object_id": "mocked_blind_topic_name", '
                '"position_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/position", '
                '"set_position_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/position/set", '
                '"tilt_status_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/tilt", '
                '"tilt_command_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/tilt/set"'
                "}" in logs
            )
            assert (
                "[MQTT] [homeassistant/cover/mocked_unipi_mocked_roller_shutter_topic_name/config] "
                "Publishing message: {"
                '"name": "MOCKED_FRIENDLY_NAME - ROLLER SHUTTER", '
                '"unique_id": "mocked_unipi_mocked_roller_shutter_topic_name", '
                '"command_topic": "mocked_unipi/mocked_roller_shutter_topic_name/cover/roller_shutter/set", '
                '"state_topic": "mocked_unipi/mocked_roller_shutter_topic_name/cover/roller_shutter/state", '
                '"qos": 2, '
                '"optimistic": false, '
                '"device": {'
                '"name": "MOCKED UNIPI - MOCKED AREA", '
                '"identifiers": "MOCKED UNIPI - MOCKED AREA", '
                '"model": "MOCKED_NAME MOCKED_MODEL", '
                '"manufacturer": "Unipi technology", '
                '"suggested_area": "MOCKED AREA", '
                '"via_device": "MOCKED UNIPI"'
                "}, "
                '"object_id": "mocked_roller_shutter_topic_name"'
                "}" in logs
            )
            assert len(logs) == 2

        loop = asyncio.new_event_loop()
        loop.run_until_complete(run())

    @pytest.mark.parametrize(
        ("config_loader", "expected"),
        [
            (
                (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT),
                [
                    {
                        "message": {
                            "name": "MOCKED_FRIENDLY_NAME - BLIND",
                            "unique_id": "mocked_unipi_mocked_blind_topic_name",
                            "command_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/set",
                            "state_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/state",
                            "qos": 2,
                            "optimistic": False,
                            "device": {
                                "name": "MOCKED UNIPI",
                                "identifiers": "MOCKED UNIPI",
                                "model": "MOCKED_NAME MOCKED_MODEL",
                                "manufacturer": "Unipi technology",
                            },
                            "object_id": "mocked_blind_topic_name",
                            "position_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/position",
                            "set_position_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/position/set",
                            "tilt_status_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/tilt",
                            "tilt_command_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/tilt/set",
                        },
                        "topic": "homeassistant/cover/mocked_unipi_mocked_blind_topic_name/config",
                    },
                    {
                        "message": {
                            "name": "MOCKED_FRIENDLY_NAME - ROLLER SHUTTER",
                            "unique_id": "mocked_unipi_mocked_roller_shutter_topic_name",
                            "command_topic": "mocked_unipi/mocked_roller_shutter_topic_name/cover/roller_shutter/set",
                            "state_topic": "mocked_unipi/mocked_roller_shutter_topic_name/cover/roller_shutter/state",
                            "qos": 2,
                            "optimistic": False,
                            "device": {
                                "name": "MOCKED UNIPI - MOCKED AREA",
                                "identifiers": "MOCKED UNIPI - MOCKED AREA",
                                "model": "MOCKED_NAME MOCKED_MODEL",
                                "manufacturer": "Unipi technology",
                                "suggested_area": "MOCKED AREA",
                                "via_device": "MOCKED UNIPI",
                            },
                            "object_id": "mocked_roller_shutter_topic_name",
                        },
                        "topic": "homeassistant/cover/mocked_unipi_mocked_roller_shutter_topic_name/config",
                    },
                ],
            ),
        ],
        indirect=["config_loader"],
    )
    def test_discovery_message(self, neuron: Neuron, covers: CoverMap, expected: List[Dict[str, Any]]) -> None:
        """Test MQTT topic and message when publish a feature."""
        mock_mqtt_client: AsyncMock = AsyncMock(spec=Client)
        plugin: HassCoversMqttPlugin = HassCoversMqttPlugin(neuron=neuron, mqtt_client=mock_mqtt_client, covers=covers)

        for index, cover in enumerate(covers.by_device_classes(DEVICE_CLASSES)):
            topic, message = plugin.hass.get_discovery(cover)

            assert message == expected[index]["message"]
            assert topic == expected[index]["topic"]
