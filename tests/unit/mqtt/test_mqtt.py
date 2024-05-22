"""Unit tests MQTT for input and output features."""

import asyncio
from asyncio import Task
from contextlib import AsyncExitStack
from typing import Any
from typing import Iterator
from typing import List
from typing import Set
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from unittest.mock import call
import pytest
from _pytest.logging import LogCaptureFixture
from aiomqtt import Client as MqttClient
from aiomqtt import MqttError
from pytest_mock import MockerFixture

from tests.conftest import ConfigLoader
from tests.conftest import MockMQTTMessages
from tests.conftest_data import CONFIG_CONTENT
from tests.conftest_data import EXTENSION_HARDWARE_DATA_CONTENT
from tests.conftest_data import HARDWARE_DATA_CONTENT
from unipi_control.hardware.unipi import Unipi
from unipi_control.helpers.exceptions import UnexpectedError
from unipi_control.integrations.covers import CoverMap
from unipi_control.mqtt.helpers import MqttHelper


class AwaitableMock(AsyncMock):
    def __await__(self) -> Iterator[Any]:
        self.await_count += 1
        return iter([])


class AsyncContextManagerMock(MagicMock):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        ...


class TestHappyPathMqtt:
    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    async def test_connect_to_mqtt_broker(
        self, mocker: MockerFixture, config_loader: ConfigLoader, unipi: Unipi, caplog: LogCaptureFixture
    ) -> None:
        """Test connect/reconnect to MQTT broker"""
        mock_mqtt_client: MagicMock = mocker.patch(
            "unipi_control.mqtt.helpers.MqttClient", new_callable=AsyncContextManagerMock
        )

        mock_mqtt_discovery: MagicMock = mocker.patch.object(MqttHelper, "discovery")
        mock_mqtt_subscribe: MagicMock = mocker.patch.object(MqttHelper, "subscribe")
        mock_mqtt_publish: MagicMock = mocker.patch.object(MqttHelper, "publish")
        mock_covers_mqtt_helper: MagicMock = mocker.patch("unipi_control.mqtt.helpers.CoversMqttHelper")

        MqttHelper.MQTT_RUNNING = PropertyMock(side_effect=[True, False])

        await MqttHelper(unipi=unipi).run()

        # Connect/reconnect
        assert mock_mqtt_client.return_value.__aenter__.call_count == 1

        # MQTT client
        mock_mqtt_client.assert_called_once()

        # Home Assistant MQTT disovery only called once (first loop)
        mock_mqtt_discovery.assert_called_once()

        # One call per loop
        assert mock_mqtt_subscribe.call_count == 1

        # Two call per loop
        assert mock_mqtt_publish.call_count == 2

        # One call per loop
        assert mock_covers_mqtt_helper.call_count == 1

        logs: List[str] = [record.getMessage() for record in caplog.records]

        assert "[MQTT] Initialize Home Assistant discovery" in logs
        assert "[MQTT] Connected to localhost:1883" in logs

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    async def test_publish_tcp(self, mocker: MockerFixture, config_loader: ConfigLoader, unipi: Unipi) -> None:
        """Test MQTT publish with Modbus TCP"""
        mock_mqtt_client: AsyncMock = mocker.patch("unipi_control.mqtt.helpers.MqttClient", new_callable=AsyncMock)
        MqttHelper.PUBLISH_RUNNING = PropertyMock(side_effect=[True, False])

        await MqttHelper(unipi=unipi).publish(
            client=mock_mqtt_client,
            feature_types=MqttHelper.publish_tcp_feature_types,
            scan_callback=unipi.modbus_helper.scan_tcp,
            scan_interval=unipi.config.modbus_tcp.scan_interval,
        )

        assert unipi.config.modbus_tcp.scan_interval == 0.5

        assert mock_mqtt_client.mock_calls == [
            call.publish(topic="mocked_unipi/input/di_1_01/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_1_02/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_1_03/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_1_04/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_01/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_02/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_03/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_04/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_05/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_06/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_07/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_08/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_09/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_10/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_11/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_12/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_13/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_14/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_15/get", payload="ON", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_2_16/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_01/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_02/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_03/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_04/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_05/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_06/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_07/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_08/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_09/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_10/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_11/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_12/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_13/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_14/get", payload="ON", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_15/get", payload="ON", qos=1, retain=True),
            call.publish(topic="mocked_unipi/input/di_3_16/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/do_1_01/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/do_1_02/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/do_1_03/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/do_1_04/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_01/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_02/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_03/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_04/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_05/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_06/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_07/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_08/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_09/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_10/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_11/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_12/get", payload="ON", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_13/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_2_14/get", payload="ON", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_01/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_02/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_03/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_04/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_05/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_06/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_07/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_08/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_09/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_10/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_11/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_12/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_13/get", payload="OFF", qos=1, retain=True),
            call.publish(topic="mocked_unipi/relay/ro_3_14/get", payload="ON", qos=1, retain=True),
        ]

        assert len(mock_mqtt_client.mock_calls) == 68

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    async def test_publish_serial(self, mocker: MockerFixture, config_loader: ConfigLoader, unipi: Unipi) -> None:
        """Test MQTT publish with Modbus RTU"""
        mock_mqtt_client: AsyncMock = mocker.patch("unipi_control.mqtt.helpers.MqttClient", new_callable=AsyncMock)
        MqttHelper.PUBLISH_RUNNING = PropertyMock(side_effect=[True, False])

        await MqttHelper(unipi=unipi).publish(
            client=mock_mqtt_client,
            feature_types=MqttHelper.publish_serial_feature_types,
            scan_callback=unipi.modbus_helper.scan_serial,
            scan_interval=unipi.config.modbus_serial.scan_interval,
        )

        assert unipi.config.modbus_serial.scan_interval == 0.5

        assert mock_mqtt_client.mock_calls == [
            call.publish(topic="mocked_unipi/meter/voltage_1/get", payload=235.2, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/current_1/get", payload=0.29, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/active_power_1/get", payload=37.7, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/apparent_power_1/get", payload=41.12, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/reactive_power_1/get", payload=-16.3, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/power_factor_1/get", payload=0.92, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/phase_angle_1/get", payload=0.0, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/frequency_1/get", payload=50.04, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/import_active_energy_1/get", payload=4.42, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/export_active_energy_1/get", payload=0.0, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/import_reactive_energy_1/get", payload=0.3, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/export_reactive_energy_1/get", payload=2.74, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/total_system_power_demand_1/get", payload=37.27, qos=1, retain=True),
            call.publish(
                topic="mocked_unipi/meter/maximum_total_system_power_demand_1/get", payload=81.04, qos=1, retain=True
            ),
            call.publish(
                topic="mocked_unipi/meter/import_system_power_demand_1/get", payload=37.27, qos=1, retain=True
            ),
            call.publish(
                topic="mocked_unipi/meter/maximum_import_system_power_demand_1/get", payload=81.04, qos=1, retain=True
            ),
            call.publish(topic="mocked_unipi/meter/export_system_power_demand_1/get", payload=0.0, qos=1, retain=True),
            call.publish(
                topic="mocked_unipi/meter/maximum_export_system_power_demand_1/get", payload=0.03, qos=1, retain=True
            ),
            call.publish(topic="mocked_unipi/meter/current_demand_1/get", payload=0.29, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/maximum_current_demand_1/get", payload=0.71, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/total_active_energy_1/get", payload=4.42, qos=1, retain=True),
            call.publish(topic="mocked_unipi/meter/total_reactive_energy_1/get", payload=3.03, qos=1, retain=True),
        ]

        assert len(mock_mqtt_client.mock_calls) == 22

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    async def test_discovery(self, mocker: MockerFixture, config_loader: ConfigLoader, unipi: Unipi) -> None:
        """Test Home Assistant MQTT discovery"""
        mock_mqtt_client: AsyncMock = mocker.patch("unipi_control.mqtt.helpers.MqttClient", new_callable=AsyncMock)
        MqttHelper.PUBLISH_RUNNING = PropertyMock(side_effect=[True, False])

        await MqttHelper(unipi=unipi).discovery(client=mock_mqtt_client)

        assert mock_mqtt_client.mock_calls == [
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/mocked_id_di_1_01/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - DI_1_01", "unique_id": "mocked_unipi_mocked_id_di_1_01", "state_topic": "mocked_unipi/input/di_1_01/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "mocked_id_di_1_01", "icon": "mdi:power-standby", "payload_on": "OFF", "payload_off": "ON"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/mocked_id_di_1_02/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - DI_1_02", "unique_id": "mocked_unipi_mocked_id_di_1_02", "state_topic": "mocked_unipi/input/di_1_02/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "mocked_id_di_1_02", "device_class": "heat"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_1_03/config",
                payload='{"name": "Digital Input 1.03", "unique_id": "mocked_unipi_di_1_03", "state_topic": "mocked_unipi/input/di_1_03/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_1_03"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_1_04/config",
                payload='{"name": "Digital Input 1.04", "unique_id": "mocked_unipi_di_1_04", "state_topic": "mocked_unipi/input/di_1_04/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_1_04"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_01/config",
                payload='{"name": "Digital Input 2.01", "unique_id": "mocked_unipi_di_2_01", "state_topic": "mocked_unipi/input/di_2_01/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_01"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_02/config",
                payload='{"name": "Digital Input 2.02", "unique_id": "mocked_unipi_di_2_02", "state_topic": "mocked_unipi/input/di_2_02/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_02"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_03/config",
                payload='{"name": "Digital Input 2.03", "unique_id": "mocked_unipi_di_2_03", "state_topic": "mocked_unipi/input/di_2_03/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_03"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_04/config",
                payload='{"name": "Digital Input 2.04", "unique_id": "mocked_unipi_di_2_04", "state_topic": "mocked_unipi/input/di_2_04/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_04"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_05/config",
                payload='{"name": "Digital Input 2.05", "unique_id": "mocked_unipi_di_2_05", "state_topic": "mocked_unipi/input/di_2_05/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_05"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_06/config",
                payload='{"name": "Digital Input 2.06", "unique_id": "mocked_unipi_di_2_06", "state_topic": "mocked_unipi/input/di_2_06/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_06"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_07/config",
                payload='{"name": "Digital Input 2.07", "unique_id": "mocked_unipi_di_2_07", "state_topic": "mocked_unipi/input/di_2_07/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_07"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_08/config",
                payload='{"name": "Digital Input 2.08", "unique_id": "mocked_unipi_di_2_08", "state_topic": "mocked_unipi/input/di_2_08/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_08"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_09/config",
                payload='{"name": "Digital Input 2.09", "unique_id": "mocked_unipi_di_2_09", "state_topic": "mocked_unipi/input/di_2_09/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_09"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_10/config",
                payload='{"name": "Digital Input 2.10", "unique_id": "mocked_unipi_di_2_10", "state_topic": "mocked_unipi/input/di_2_10/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_10"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_11/config",
                payload='{"name": "Digital Input 2.11", "unique_id": "mocked_unipi_di_2_11", "state_topic": "mocked_unipi/input/di_2_11/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_11"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_12/config",
                payload='{"name": "Digital Input 2.12", "unique_id": "mocked_unipi_di_2_12", "state_topic": "mocked_unipi/input/di_2_12/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_12"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_13/config",
                payload='{"name": "Digital Input 2.13", "unique_id": "mocked_unipi_di_2_13", "state_topic": "mocked_unipi/input/di_2_13/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_13"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_14/config",
                payload='{"name": "Digital Input 2.14", "unique_id": "mocked_unipi_di_2_14", "state_topic": "mocked_unipi/input/di_2_14/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_14"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_15/config",
                payload='{"name": "Digital Input 2.15", "unique_id": "mocked_unipi_di_2_15", "state_topic": "mocked_unipi/input/di_2_15/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_15"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_2_16/config",
                payload='{"name": "Digital Input 2.16", "unique_id": "mocked_unipi_di_2_16", "state_topic": "mocked_unipi/input/di_2_16/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_2_16"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/mocked_friendly_name_di_3_01/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - DI_3_01", "unique_id": "mocked_unipi_mocked_friendly_name_di_3_01", "state_topic": "mocked_unipi/input/di_3_01/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "mocked_friendly_name_di_3_01"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/mocked_friendly_name_di_3_02/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - DI_3_02", "unique_id": "mocked_unipi_mocked_friendly_name_di_3_02", "state_topic": "mocked_unipi/input/di_3_02/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "mocked_friendly_name_di_3_02"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_03/config",
                payload='{"name": "Digital Input 3.03", "unique_id": "mocked_unipi_di_3_03", "state_topic": "mocked_unipi/input/di_3_03/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_03"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_04/config",
                payload='{"name": "Digital Input 3.04", "unique_id": "mocked_unipi_di_3_04", "state_topic": "mocked_unipi/input/di_3_04/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_04"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_05/config",
                payload='{"name": "Digital Input 3.05", "unique_id": "mocked_unipi_di_3_05", "state_topic": "mocked_unipi/input/di_3_05/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_05"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_06/config",
                payload='{"name": "Digital Input 3.06", "unique_id": "mocked_unipi_di_3_06", "state_topic": "mocked_unipi/input/di_3_06/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_06"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_07/config",
                payload='{"name": "Digital Input 3.07", "unique_id": "mocked_unipi_di_3_07", "state_topic": "mocked_unipi/input/di_3_07/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_07"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_08/config",
                payload='{"name": "Digital Input 3.08", "unique_id": "mocked_unipi_di_3_08", "state_topic": "mocked_unipi/input/di_3_08/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_08"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_09/config",
                payload='{"name": "Digital Input 3.09", "unique_id": "mocked_unipi_di_3_09", "state_topic": "mocked_unipi/input/di_3_09/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_09"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_10/config",
                payload='{"name": "Digital Input 3.10", "unique_id": "mocked_unipi_di_3_10", "state_topic": "mocked_unipi/input/di_3_10/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_10"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_11/config",
                payload='{"name": "Digital Input 3.11", "unique_id": "mocked_unipi_di_3_11", "state_topic": "mocked_unipi/input/di_3_11/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_11"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_12/config",
                payload='{"name": "Digital Input 3.12", "unique_id": "mocked_unipi_di_3_12", "state_topic": "mocked_unipi/input/di_3_12/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_12"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_13/config",
                payload='{"name": "Digital Input 3.13", "unique_id": "mocked_unipi_di_3_13", "state_topic": "mocked_unipi/input/di_3_13/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_13"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_14/config",
                payload='{"name": "Digital Input 3.14", "unique_id": "mocked_unipi_di_3_14", "state_topic": "mocked_unipi/input/di_3_14/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_14"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_15/config",
                payload='{"name": "Digital Input 3.15", "unique_id": "mocked_unipi_di_3_15", "state_topic": "mocked_unipi/input/di_3_15/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_15"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/binary_sensor/mocked_unipi/di_3_16/config",
                payload='{"name": "Digital Input 3.16", "unique_id": "mocked_unipi_di_3_16", "state_topic": "mocked_unipi/input/di_3_16/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "di_3_16"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/do_1_01/config",
                payload='{"name": "Digital Output 1.01", "unique_id": "mocked_unipi_do_1_01", "command_topic": "mocked_unipi/relay/do_1_01/set", "state_topic": "mocked_unipi/relay/do_1_01/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "do_1_01"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/do_1_02/config",
                payload='{"name": "Digital Output 1.02", "unique_id": "mocked_unipi_do_1_02", "command_topic": "mocked_unipi/relay/do_1_02/set", "state_topic": "mocked_unipi/relay/do_1_02/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "do_1_02"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/do_1_03/config",
                payload='{"name": "Digital Output 1.03", "unique_id": "mocked_unipi_do_1_03", "command_topic": "mocked_unipi/relay/do_1_03/set", "state_topic": "mocked_unipi/relay/do_1_03/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "do_1_03"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/do_1_04/config",
                payload='{"name": "Digital Output 1.04", "unique_id": "mocked_unipi_do_1_04", "command_topic": "mocked_unipi/relay/do_1_04/set", "state_topic": "mocked_unipi/relay/do_1_04/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "do_1_04"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/mocked_id_ro_2_01/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - RO_2_01", "unique_id": "mocked_unipi_mocked_id_ro_2_01", "command_topic": "mocked_unipi/relay/ro_2_01/set", "state_topic": "mocked_unipi/relay/ro_2_01/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "mocked_id_ro_2_01", "payload_on": "OFF", "payload_off": "ON"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/mocked_id_ro_2_02/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - RO_2_02", "unique_id": "mocked_unipi_mocked_id_ro_2_02", "command_topic": "mocked_unipi/relay/ro_2_02/set", "state_topic": "mocked_unipi/relay/ro_2_02/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "mocked_id_ro_2_02", "icon": "mdi:power-standby", "device_class": "switch"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_03/config",
                payload='{"name": "Relay 2.03", "unique_id": "mocked_unipi_ro_2_03", "command_topic": "mocked_unipi/relay/ro_2_03/set", "state_topic": "mocked_unipi/relay/ro_2_03/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_03"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_04/config",
                payload='{"name": "Relay 2.04", "unique_id": "mocked_unipi_ro_2_04", "command_topic": "mocked_unipi/relay/ro_2_04/set", "state_topic": "mocked_unipi/relay/ro_2_04/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_04"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_05/config",
                payload='{"name": "Relay 2.05", "unique_id": "mocked_unipi_ro_2_05", "command_topic": "mocked_unipi/relay/ro_2_05/set", "state_topic": "mocked_unipi/relay/ro_2_05/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_05"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_06/config",
                payload='{"name": "Relay 2.06", "unique_id": "mocked_unipi_ro_2_06", "command_topic": "mocked_unipi/relay/ro_2_06/set", "state_topic": "mocked_unipi/relay/ro_2_06/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_06"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_07/config",
                payload='{"name": "Relay 2.07", "unique_id": "mocked_unipi_ro_2_07", "command_topic": "mocked_unipi/relay/ro_2_07/set", "state_topic": "mocked_unipi/relay/ro_2_07/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_07"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_08/config",
                payload='{"name": "Relay 2.08", "unique_id": "mocked_unipi_ro_2_08", "command_topic": "mocked_unipi/relay/ro_2_08/set", "state_topic": "mocked_unipi/relay/ro_2_08/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_08"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_09/config",
                payload='{"name": "Relay 2.09", "unique_id": "mocked_unipi_ro_2_09", "command_topic": "mocked_unipi/relay/ro_2_09/set", "state_topic": "mocked_unipi/relay/ro_2_09/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_09"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_10/config",
                payload='{"name": "Relay 2.10", "unique_id": "mocked_unipi_ro_2_10", "command_topic": "mocked_unipi/relay/ro_2_10/set", "state_topic": "mocked_unipi/relay/ro_2_10/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_10"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_11/config",
                payload='{"name": "Relay 2.11", "unique_id": "mocked_unipi_ro_2_11", "command_topic": "mocked_unipi/relay/ro_2_11/set", "state_topic": "mocked_unipi/relay/ro_2_11/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_11"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_12/config",
                payload='{"name": "Relay 2.12", "unique_id": "mocked_unipi_ro_2_12", "command_topic": "mocked_unipi/relay/ro_2_12/set", "state_topic": "mocked_unipi/relay/ro_2_12/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_12"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_13/config",
                payload='{"name": "Relay 2.13", "unique_id": "mocked_unipi_ro_2_13", "command_topic": "mocked_unipi/relay/ro_2_13/set", "state_topic": "mocked_unipi/relay/ro_2_13/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_13"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_2_14/config",
                payload='{"name": "Relay 2.14", "unique_id": "mocked_unipi_ro_2_14", "command_topic": "mocked_unipi/relay/ro_2_14/set", "state_topic": "mocked_unipi/relay/ro_2_14/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_2_14"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_05/config",
                payload='{"name": "Relay 3.05", "unique_id": "mocked_unipi_ro_3_05", "command_topic": "mocked_unipi/relay/ro_3_05/set", "state_topic": "mocked_unipi/relay/ro_3_05/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_05"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_06/config",
                payload='{"name": "Relay 3.06", "unique_id": "mocked_unipi_ro_3_06", "command_topic": "mocked_unipi/relay/ro_3_06/set", "state_topic": "mocked_unipi/relay/ro_3_06/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_06"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_07/config",
                payload='{"name": "Relay 3.07", "unique_id": "mocked_unipi_ro_3_07", "command_topic": "mocked_unipi/relay/ro_3_07/set", "state_topic": "mocked_unipi/relay/ro_3_07/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_07"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_08/config",
                payload='{"name": "Relay 3.08", "unique_id": "mocked_unipi_ro_3_08", "command_topic": "mocked_unipi/relay/ro_3_08/set", "state_topic": "mocked_unipi/relay/ro_3_08/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_08"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_09/config",
                payload='{"name": "Relay 3.09", "unique_id": "mocked_unipi_ro_3_09", "command_topic": "mocked_unipi/relay/ro_3_09/set", "state_topic": "mocked_unipi/relay/ro_3_09/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_09"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_10/config",
                payload='{"name": "Relay 3.10", "unique_id": "mocked_unipi_ro_3_10", "command_topic": "mocked_unipi/relay/ro_3_10/set", "state_topic": "mocked_unipi/relay/ro_3_10/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_10"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_11/config",
                payload='{"name": "Relay 3.11", "unique_id": "mocked_unipi_ro_3_11", "command_topic": "mocked_unipi/relay/ro_3_11/set", "state_topic": "mocked_unipi/relay/ro_3_11/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_11"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_12/config",
                payload='{"name": "Relay 3.12", "unique_id": "mocked_unipi_ro_3_12", "command_topic": "mocked_unipi/relay/ro_3_12/set", "state_topic": "mocked_unipi/relay/ro_3_12/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_12"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_13/config",
                payload='{"name": "Relay 3.13", "unique_id": "mocked_unipi_ro_3_13", "command_topic": "mocked_unipi/relay/ro_3_13/set", "state_topic": "mocked_unipi/relay/ro_3_13/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_13"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/switch/mocked_unipi/ro_3_14/config",
                payload='{"name": "Relay 3.14", "unique_id": "mocked_unipi_ro_3_14", "command_topic": "mocked_unipi/relay/ro_3_14/set", "state_topic": "mocked_unipi/relay/ro_3_14/get", "qos": 2, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "sw_version": "6.18", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "object_id": "ro_3_14"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/voltage_1/config",
                payload='{"name": "Voltage", "unique_id": "mocked_unipi_voltage_1", "state_topic": "mocked_unipi/meter/voltage_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "voltage_1", "device_class": "voltage", "state_class": "measurement", "unit_of_measurement": "V"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/current_1/config",
                payload='{"name": "Current", "unique_id": "mocked_unipi_current_1", "state_topic": "mocked_unipi/meter/current_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "current_1", "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/active_power_1/config",
                payload='{"name": "Active Power", "unique_id": "mocked_unipi_active_power_1", "state_topic": "mocked_unipi/meter/active_power_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "active_power_1", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/mocked_id_apparent_power/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - APPARENT_POWER", "unique_id": "mocked_unipi_mocked_id_apparent_power", "state_topic": "mocked_unipi/meter/apparent_power_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "mocked_id_apparent_power", "icon": "mdi:power-standby", "device_class": "apparent_power", "state_class": "measurement", "unit_of_measurement": "VA"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/reactive_power_1/config",
                payload='{"name": "Reactive Power", "unique_id": "mocked_unipi_reactive_power_1", "state_topic": "mocked_unipi/meter/reactive_power_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "reactive_power_1", "device_class": "power", "state_class": "total", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/power_factor_1/config",
                payload='{"name": "Power Factor", "unique_id": "mocked_unipi_power_factor_1", "state_topic": "mocked_unipi/meter/power_factor_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "power_factor_1", "device_class": "power_factor", "state_class": "measurement"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/phase_angle_1/config",
                payload='{"name": "Phase Angle", "unique_id": "mocked_unipi_phase_angle_1", "state_topic": "mocked_unipi/meter/phase_angle_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "phase_angle_1", "state_class": "measurement"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/frequency_1/config",
                payload='{"name": "Frequency", "unique_id": "mocked_unipi_frequency_1", "state_topic": "mocked_unipi/meter/frequency_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "frequency_1", "device_class": "frequency", "state_class": "measurement", "unit_of_measurement": "Hz"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/import_active_energy_1/config",
                payload='{"name": "Import Active Energy", "unique_id": "mocked_unipi_import_active_energy_1", "state_topic": "mocked_unipi/meter/import_active_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "import_active_energy_1", "device_class": "energy", "state_class": "total", "unit_of_measurement": "kWh"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/export_active_energy_1/config",
                payload='{"name": "Export Active Energy", "unique_id": "mocked_unipi_export_active_energy_1", "state_topic": "mocked_unipi/meter/export_active_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "export_active_energy_1", "device_class": "energy", "state_class": "measurement", "unit_of_measurement": "kWh"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/import_reactive_energy_1/config",
                payload='{"name": "Import Reactive Energy", "unique_id": "mocked_unipi_import_reactive_energy_1", "state_topic": "mocked_unipi/meter/import_reactive_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "import_reactive_energy_1", "state_class": "total", "unit_of_measurement": "kvarh"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/export_reactive_energy_1/config",
                payload='{"name": "Export Reactive Energy", "unique_id": "mocked_unipi_export_reactive_energy_1", "state_topic": "mocked_unipi/meter/export_reactive_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "export_reactive_energy_1", "state_class": "total", "unit_of_measurement": "kvarh"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/total_system_power_demand_1/config",
                payload='{"name": "Total System Power Demand", "unique_id": "mocked_unipi_total_system_power_demand_1", "state_topic": "mocked_unipi/meter/total_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "total_system_power_demand_1", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/maximum_total_system_power_demand_1/config",
                payload='{"name": "Maximum Total System Power Demand", "unique_id": "mocked_unipi_maximum_total_system_power_demand_1", "state_topic": "mocked_unipi/meter/maximum_total_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "maximum_total_system_power_demand_1", "device_class": "power", "state_class": "total", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/import_system_power_demand_1/config",
                payload='{"name": "Import System Power Demand", "unique_id": "mocked_unipi_import_system_power_demand_1", "state_topic": "mocked_unipi/meter/import_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "import_system_power_demand_1", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/maximum_import_system_power_demand_1/config",
                payload='{"name": "Maximum Import System Power Demand", "unique_id": "mocked_unipi_maximum_import_system_power_demand_1", "state_topic": "mocked_unipi/meter/maximum_import_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "maximum_import_system_power_demand_1", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/export_system_power_demand_1/config",
                payload='{"name": "Export System Power Demand", "unique_id": "mocked_unipi_export_system_power_demand_1", "state_topic": "mocked_unipi/meter/export_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "export_system_power_demand_1", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/maximum_export_system_power_demand_1/config",
                payload='{"name": "Maximum Export System Power Demand", "unique_id": "mocked_unipi_maximum_export_system_power_demand_1", "state_topic": "mocked_unipi/meter/maximum_export_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "maximum_export_system_power_demand_1", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/current_demand_1/config",
                payload='{"name": "Current Demand", "unique_id": "mocked_unipi_current_demand_1", "state_topic": "mocked_unipi/meter/current_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "current_demand_1", "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/maximum_current_demand_1/config",
                payload='{"name": "Maximum Current Demand", "unique_id": "mocked_unipi_maximum_current_demand_1", "state_topic": "mocked_unipi/meter/maximum_current_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "maximum_current_demand_1", "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/total_active_energy_1/config",
                payload='{"name": "Total Active Energy", "unique_id": "mocked_unipi_total_active_energy_1", "state_topic": "mocked_unipi/meter/total_active_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "total_active_energy_1", "device_class": "energy", "state_class": "total", "unit_of_measurement": "kWh"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/sensor/mocked_unipi/total_reactive_energy_1/config",
                payload='{"name": "Total Reactive Energy", "unique_id": "mocked_unipi_total_reactive_energy_1", "state_topic": "mocked_unipi/meter/total_reactive_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "mocked_eastron_sdm120m_workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "object_id": "total_reactive_energy_1", "state_class": "total", "unit_of_measurement": "kvarh"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/cover/mocked_unipi/mocked_blind_topic_name/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - BLIND", "unique_id": "mocked_unipi_mocked_blind_topic_name", "object_id": "mocked_blind_topic_name", "device_class": "blind", "command_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/set", "state_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/state", "qos": 2, "optimistic": false, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}, "position_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/position", "set_position_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/position/set", "tilt_status_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/tilt", "tilt_command_topic": "mocked_unipi/mocked_blind_topic_name/cover/blind/tilt/set"}',
                qos=2,
                retain=True,
            ),
            call.publish(
                topic="homeassistant/cover/mocked_unipi/mocked_shutter_topic_name/config",
                payload='{"name": "MOCKED_FRIENDLY_NAME - SHUTTER", "unique_id": "mocked_unipi_mocked_shutter_topic_name", "object_id": "mocked_shutter_topic_name", "device_class": "shutter", "command_topic": "mocked_unipi/mocked_shutter_topic_name/cover/shutter/set", "state_topic": "mocked_unipi/mocked_shutter_topic_name/cover/shutter/state", "qos": 2, "optimistic": false, "device": {"name": "MOCKED UNIPI", "identifiers": "mocked_unipi", "model": "MOCKED_NAME MOCKED_MODEL", "manufacturer": "Unipi technology", "suggested_area": "MOCKED AREA"}}',
                qos=2,
                retain=True,
            ),
        ]

        assert len(mock_mqtt_client.mock_calls) == 88


class TestUnhappyPathMqtt:
    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    async def test_connect_to_mqtt_broker(
        self, mocker: MockerFixture, config_loader: ConfigLoader, unipi: Unipi, caplog: LogCaptureFixture
    ) -> None:
        """Test connect/reconnect to MQTT broker"""
        mock_mqtt_client: MagicMock = mocker.patch(
            "unipi_control.mqtt.helpers.MqttClient", new_callable=AsyncContextManagerMock
        )
        mock_mqtt_client.return_value.__aenter__.side_effect = [
            MqttError("MOCKED MQTT ERROR"),
            MqttError("MOCKED MQTT ERROR"),
        ]

        MqttHelper.MQTT_RUNNING = PropertyMock(side_effect=[True, True, False])

        with pytest.raises(UnexpectedError) as error:
            await MqttHelper(unipi=unipi).run()

        assert str(error.value) == "Shutdown, due to too many MQTT connection attempts."

        # Connect/reconnect
        assert mock_mqtt_client.return_value.__aenter__.call_count == 2

        logs: List[str] = [record.getMessage() for record in caplog.records]

        assert "[MQTT] Error 'MOCKED MQTT ERROR'. Connecting attempt #1. Reconnecting in 2 seconds." in logs
        assert "[MQTT] Error 'MOCKED MQTT ERROR'. Connecting attempt #2. Reconnecting in 2 seconds." in logs
