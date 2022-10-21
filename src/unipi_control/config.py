import dataclasses
import logging
import re
import socket
import struct
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path
from tempfile import gettempdir
from typing import Final
from typing import List

from superbox_utils.config.exception import ConfigException
from superbox_utils.config.loader import ConfigLoaderMixin
from superbox_utils.config.loader import Validation
from superbox_utils.dict.data_dict import DataDict
from superbox_utils.hass.config import HomeAssistantConfig
from superbox_utils.logging import init_logger
from superbox_utils.logging import stream_handler
from superbox_utils.logging.config import LoggingConfig
from superbox_utils.mqtt.config import MqttConfig
from superbox_utils.yaml.loader import yaml_loader_safe
from unipi_control.logging import LOG_NAME

COVER_TYPES: Final[List[str]] = ["blind", "roller_shutter", "garage_door"]
MODBUS_TYPES: Final[List[str]] = ["meter"]

logger: logging.Logger = init_logger(name=LOG_NAME, level="info", handlers=[stream_handler])


class LogPrefix:
    CONFIG: Final[str] = "[CONFIG]"
    COVER: Final[str] = "[COVER]"
    MODBUS: Final[str] = "[MODBUS]"


@dataclass
class DeviceInfo(ConfigLoaderMixin):
    name: str = field(default=socket.gethostname())
    manufacturer: str = field(default="Unipi technology")

    def _validate_name(self, value: str, _field: dataclasses.Field) -> str:
        if re.search(Validation.ALLOWED_CHARACTERS.regex, value) is None:
            raise ConfigException(
                f"[{self.__class__.__name__.replace('Config', '').upper()}] Invalid value '{value}' in '{_field.name}'. {Validation.ALLOWED_CHARACTERS.error}"
            )

        return value


@dataclass
class FeatureConfig(ConfigLoaderMixin):
    id: str = field(default_factory=str)  # pylint: disable=invalid-name
    invert_state: bool = field(default=False)
    friendly_name: str = field(default_factory=str)
    suggested_area: str = field(default_factory=str)


@dataclass
class CoverConfig(ConfigLoaderMixin):
    id: str = field(default_factory=str)  # pylint: disable=invalid-name
    friendly_name: str = field(default_factory=str)
    suggested_area: str = field(default_factory=str)
    cover_type: str = field(default_factory=str)
    topic_name: str = field(default_factory=str)
    cover_run_time: float = field(default_factory=float)
    tilt_change_time: float = field(default_factory=float)
    circuit_up: str = field(default_factory=str)
    circuit_down: str = field(default_factory=str)

    def validate(self):
        for _field in ("friendly_name", "topic_name", "cover_type", "circuit_up", "circuit_down"):
            if not getattr(self, _field):
                raise ConfigException(f"{LogPrefix.COVER} Required key '{_field}' is missing! {repr(self)}")

        super().validate()

    def _validate_topic_name(self, value: str, _field: dataclasses.Field) -> str:
        value = value.lower()

        if re.search(Validation.ALLOWED_CHARACTERS.regex, value) is None:
            raise ConfigException(
                f"[{self.__class__.__name__.replace('Config', '').upper()}] Invalid value '{value}' in '{_field.name}'. {Validation.ALLOWED_CHARACTERS.error}"
            )

        return value

    def _validate_cover_type(self, value: str, _field: dataclasses.Field) -> str:
        if (value := value.lower()) not in COVER_TYPES:
            raise ConfigException(
                f"{LogPrefix.COVER} Invalid value '{self.cover_type}' in '{_field.name}'. The following values are allowed: {' '.join(COVER_TYPES)}."
            )

        return value


class ModbusParity(Enum):
    EVEN: Final[str] = "E"
    ODD: Final[str] = "O"
    NONE: Final[str] = "N"


@dataclass
class ModbusDeviceInfo(ConfigLoaderMixin):
    manufacturer: str = field(default_factory=str)
    model: str = field(default_factory=str)

    # TODO: Add validations


@dataclass
class ModbusConfig(ConfigLoaderMixin):
    id: str = field(default_factory=str)  # pylint: disable=invalid-name
    friendly_name: str = field(default_factory=str)
    suggested_area: str = field(default_factory=str)
    device: ModbusDeviceInfo = field(default_factory=ModbusDeviceInfo)
    address: int = field(default_factory=int)
    baud_rate: int = field(default_factory=int)
    parity: str = field(default_factory=str)

    # TODO: Add validations

    def _validate_parity(self, value: str, _field: dataclasses.Field) -> str:
        value = value.upper()
        parity_options: List[str] = [parity.name for parity in ModbusParity]

        if value in parity_options:
            raise ConfigException(
                f"[{self.__class__.__name__.replace('Config', '').upper()}] Invalid value '{value}' in '{_field.name}'. "
                f"The following parity options are allowed: {' '.join(parity_options)}."
            )

        return value


@dataclass
class Config(ConfigLoaderMixin):
    device_info: DeviceInfo = field(default=DeviceInfo())
    mqtt: MqttConfig = field(default_factory=MqttConfig)
    homeassistant: HomeAssistantConfig = field(default_factory=HomeAssistantConfig)
    features: dict = field(init=False, default_factory=dict)
    covers: list = field(init=False, default_factory=list)
    modbus: list = field(init=False, default_factory=list)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    config_base_path: Path = field(default=Path("/etc/unipi"))
    systemd_path: Path = field(default=Path("/etc/systemd/system"))
    temp_path: Path = field(default=Path(gettempdir()) / "unipi")
    sys_bus: Path = field(default=Path("/sys/bus/i2c/devices"))

    @property
    def hardware_path(self) -> Path:
        return self.config_base_path / "hardware"

    def __post_init__(self):
        self.temp_path.mkdir(exist_ok=True)
        self.update_from_yaml_file(config_path=self.config_base_path / "control.yaml")
        self.logging.update_level(name=LOG_NAME)

    def validate(self):
        super().validate()

        for circuit, feature_data in self.features.items():
            feature_config: FeatureConfig = FeatureConfig()
            feature_config.update(feature_data)
            self.features[circuit] = feature_config

        for index, cover_data in enumerate(self.covers):
            cover_config: CoverConfig = CoverConfig()
            cover_config.update(cover_data)
            self.covers[index] = cover_config

        for index, modbus_data in enumerate(self.modbus):
            modbus_config: ModbusConfig = ModbusConfig()
            modbus_config.update(modbus_data)
            self.modbus[index] = modbus_config

        self._validate_covers_circuits()

    def get_cover_circuits(self) -> List[str]:
        """Get all circuits that are defined in the cover config."""
        circuits: List[str] = []

        for cover in self.covers:
            circuit_up: str = cover.circuit_up
            circuit_down: str = cover.circuit_down

            if circuit_up:
                circuits.append(circuit_up)

            if circuit_down:
                circuits.append(circuit_down)

        return circuits

    def _validate_covers_circuits(self):
        circuits: List[str] = self.get_cover_circuits()

        for circuit in circuits:
            if circuits.count(circuit) > 1:
                raise ConfigException(
                    f"{LogPrefix.COVER} Duplicate circuits found in 'covers'. "
                    f"Driving both signals up and down at the same time can damage the motor!"
                )


@dataclass
class HardwareInfo:
    sys_bus: Path
    name: str = field(default="unknown")
    model: str = field(default="unknown", init=False)
    version: str = field(default="unknown", init=False)
    serial: str = field(default="unknown", init=False)

    def __post_init__(self):
        unipi_1: Path = self.sys_bus / "1-0050/eeprom"
        unipi_patron: Path = self.sys_bus / "2-0057/eeprom"
        unipi_neuron_1: Path = self.sys_bus / "1-0057/eeprom"
        unipi_neuron_0: Path = self.sys_bus / "0-0057/eeprom"

        if unipi_1.is_file():
            with open(unipi_1, "rb") as _file:
                ee_bytes = _file.read(256)

                if ee_bytes[226] == 1 and ee_bytes[227] == 1:
                    self.name = "Unipi"
                    self.version = "1.1"
                elif ee_bytes[226] == 11 and ee_bytes[227] == 1:
                    self.name = "Unipi Lite"
                    self.version = "1.1"
                else:
                    self.name = "Unipi"
                    self.version = "1.0"

                self.serial = struct.unpack("i", ee_bytes[228:232])[0]
        elif unipi_patron.is_file():
            with open(unipi_patron, "rb") as _file:
                ee_bytes = _file.read(128)

                self.name = "Unipi Patron"
                self.model = f"{ee_bytes[106:110].decode()}"
                self.version = f"{ee_bytes[99]}.{ee_bytes[98]}"
                self.serial = struct.unpack("i", ee_bytes[100:104])[0]
        elif unipi_neuron_1.is_file():
            with open(unipi_neuron_1, "rb") as _file:
                ee_bytes = _file.read(128)

                self.name = "Unipi Neuron"
                self.model = f"{ee_bytes[106:110].decode()}"
                self.version = f"{ee_bytes[99]}.{ee_bytes[98]}"
                self.serial = struct.unpack("i", ee_bytes[100:104])[0]
        elif unipi_neuron_0.is_file():
            with open(unipi_neuron_0, "rb") as _file:
                ee_bytes = _file.read(128)

                self.name = "Unipi Neuron"
                self.model = f"{ee_bytes[106:110].decode()}"
                self.version = f"{ee_bytes[99]}.{ee_bytes[98]}"
                self.serial = struct.unpack("i", ee_bytes[100:104])[0]


class HardwareData(DataDict):
    def __init__(self, config: Config):
        super().__init__()

        self.config = config

        self.data: dict = {
            "neuron": asdict(HardwareInfo(sys_bus=config.sys_bus)),
            "definitions": {
                "neuron": {},
                "extension": {},
                "third_party": {},
            },
        }

        self._model: str = self.data["neuron"]["model"]

        if self._model is None:
            raise ConfigException("Hardware is not supported!")

        # self._read_definitions()
        self._read_neuron_definition()

    def _read_definitions(self):
        for definition in ("extension", "third_party"):
            try:
                for extension_file in Path(f"{self.config.hardware_path}/{definition}").iterdir():
                    if extension_file.suffix == ".yaml":
                        self.data["definitions"][f"{definition}_{extension_file.stem}"] = yaml_loader_safe(
                            extension_file
                        )
                        logger.debug("%s YAML definition loaded: %s", LogPrefix.CONFIG, extension_file)
            except FileNotFoundError as error:
                logger.info("%s %s", LogPrefix.CONFIG, str(error))

    def _read_neuron_definition(self):
        definition_file: Path = Path(f"{self.config.hardware_path}/neuron/{self._model}.yaml")

        if definition_file.is_file():
            self.data["definitions"]["neuron"] = yaml_loader_safe(definition_file)
            logger.debug("%s YAML neuron definition loaded: %s", LogPrefix.CONFIG, definition_file)
        else:
            raise ConfigException(f"No valid YAML definition for active Neuron device! Device name is {self._model}")
