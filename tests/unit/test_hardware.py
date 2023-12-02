"""Unit test for hardare."""
from typing import Dict
from typing import List
from unittest.mock import PropertyMock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from tests.conftest import ConfigLoader
from tests.conftest import MockHardwareInfo
from tests.conftest_data import CONFIG_CONTENT
from tests.conftest_data import EXTENSION_HARDWARE_DATA_CONTENT
from tests.conftest_data import HARDWARE_DATA_CONTENT
from tests.unit.test_config_data import EXTENSION_HARDWARE_DATA_INVALID_KEY
from tests.unit.test_config_data import EXTENSION_HARDWARE_DATA_IS_INVALID_YAML
from tests.unit.test_config_data import EXTENSION_HARDWARE_DATA_IS_LIST
from tests.unit.test_config_data import HARDWARE_DATA_INVALID_KEY
from tests.unit.test_config_data import HARDWARE_DATA_IS_INVALID_YAML
from tests.unit.test_config_data import HARDWARE_DATA_IS_LIST
from unipi_control.config import Config
from unipi_control.helpers.exceptions import ConfigError
from unipi_control.modbus.helpers import ModbusClient
from unipi_control.hardware.unipi import Unipi


class TestHappyPathHardware:
    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        "config_loader",
        [
            (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT),
        ],
        indirect=["config_loader"],
    )
    async def test_initialize_hardware(
        self, config_loader: ConfigLoader, modbus_client: ModbusClient, caplog: LogCaptureFixture
    ) -> None:
        """Test initialize internal and external hardware."""
        config: Config = config_loader.get_config()
        config.logging.init()

        unipi: Unipi = Unipi(config=config, modbus_client=modbus_client)
        await unipi.init()

        logs: List[str] = [record.getMessage() for record in caplog.records]
        assert "[CONFIG] 2 hardware definition(s) found." in logs
        assert "[MODBUS] Reading SPI boards" in logs
        assert "[MODBUS] Found board 1 on SPI" in logs
        assert "[MODBUS] Firmware version on board 1 is 0.0" in logs
        assert "[MODBUS] Found board 2 on SPI" in logs
        assert "[MODBUS] Firmware version on board 2 is 0.0" in logs
        assert "[MODBUS] Found board 3 on SPI" in logs
        assert "[MODBUS] Firmware version on board 3 is 0.0" in logs
        assert "[MODBUS] Reading extensions" in logs
        assert "[MODBUS] [RTU] Found device with unit 1 (manufacturer: Eastron, model: SDM120M)" in logs
        assert "[MODBUS] Firmware version on Eastron SDM120 is 202.04" in logs
        assert "[CONFIG] 94 features initialized." in logs


class TestUnhappyHardware:
    @pytest.mark.parametrize(
        ("config_loader", "expected"),
        [
            (
                (CONFIG_CONTENT, HARDWARE_DATA_INVALID_KEY, EXTENSION_HARDWARE_DATA_CONTENT),
                "\nKeyError: 'modbus_register_blocks'",
            ),
            (
                (CONFIG_CONTENT, HARDWARE_DATA_IS_LIST, EXTENSION_HARDWARE_DATA_CONTENT),
                "",
            ),
            (
                (CONFIG_CONTENT, HARDWARE_DATA_IS_INVALID_YAML, EXTENSION_HARDWARE_DATA_CONTENT),
                '\nCan\'t read YAML file!\n  in "<unicode string>", line 1, column 25:\n'
                "    modbus_features: INVALID:\n                            ^",
            ),
        ],
        indirect=["config_loader"],
    )
    def test_invalid_unipi_hardware_definition(
        self, config_loader: ConfigLoader, modbus_client: ModbusClient, expected: str
    ) -> None:
        """Test invalid unipi hardware definition."""
        config: Config = config_loader.get_config()

        with pytest.raises(ConfigError) as error:
            Unipi(config=config, modbus_client=modbus_client)

        assert str(error.value) == f"[CONFIG] Definition is invalid: {config_loader.hardware_data_file}{expected}"

    @pytest.mark.parametrize(
        ("config_loader", "expected"),
        [
            (
                (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_INVALID_KEY),
                "\nKeyError: 'modbus_register_blocks'",
            ),
            (
                (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_IS_LIST),
                "",
            ),
            (
                (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_IS_INVALID_YAML),
                '\nCan\'t read YAML file!\n  in "<unicode string>", line 1, column 22:\n'
                "    manufacturer: INVALID:\n                         ^",
            ),
        ],
        indirect=["config_loader"],
    )
    def test_invalid_extension_hardware_definition(
        self, config_loader: ConfigLoader, modbus_client: ModbusClient, expected: str
    ) -> None:
        """Test invalid extension hardware definition."""
        config: Config = config_loader.get_config()

        with pytest.raises(ConfigError) as error:
            Unipi(config=config, modbus_client=modbus_client)

        assert (
            str(error.value)
            == f"[CONFIG] Definition is invalid: {config_loader.extension_hardware_data_file}{expected}"
        )

    @pytest.mark.parametrize(
        ("config_loader", "hardware_info", "expected"),
        [
            (
                (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT),
                {
                    "name": "unknown",
                    "model": "unknown",
                    "version": "unknown",
                    "serial": "unknown",
                },
                "Hardware is not supported!",
            ),
            (
                (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT),
                {
                    "name": "unknown",
                    "model": "MOCKED_MODEL_NOT_FOUND",
                    "version": "unknown",
                    "serial": "unknown",
                },
                "No valid YAML definition found for this device!",
            ),
        ],
        indirect=["config_loader"],
    )
    def test_hardware_is_supported(
        self,
        config_loader: ConfigLoader,
        modbus_client: ModbusClient,
        hardware_info: Dict[str, str],
        expected: str,
        mocker: MockerFixture,
    ) -> None:
        """Test hardware is supported."""
        mock_hardware_info: PropertyMock = mocker.patch(
            "unipi_control.hardware.map.HardwareInfo", new_callable=PropertyMock()
        )
        mock_hardware_info.return_value = MockHardwareInfo(**hardware_info)

        config: Config = config_loader.get_config()

        with pytest.raises(ConfigError) as error:
            Unipi(config=config, modbus_client=modbus_client)

        assert str(error.value) == expected
