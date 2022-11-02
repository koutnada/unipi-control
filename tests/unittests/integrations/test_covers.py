# pylint: disable=protected-access
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from unipi_control.integrations.covers import Cover
from unipi_control.integrations.covers import CoverMap
from unipi_control.integrations.covers import CoverState
from unipi_control.modbus import ModbusClient
from unittests.conftest import ConfigLoader
from unittests.conftest_data import CONFIG_CONTENT
from unittests.conftest_data import EXTENSION_HARDWARE_DATA_CONTENT
from unittests.conftest_data import HARDWARE_DATA_CONTENT


@dataclass
class CoverOptions:
    cover_type: str
    calibrate_mode: bool = field(default_factory=bool)
    position: Optional[int] = field(default=None)
    current_position: Optional[int] = field(default=None)
    tilt: Optional[int] = field(default=None)
    current_tilt: Optional[int] = field(default=None)
    cover_state: Optional[str] = field(default=None)
    current_cover_state: Optional[str] = field(default=None)


@dataclass
class CoverExpected:
    calibration_started: Optional[bool] = field(default=None)
    calibrate_mode: Optional[bool] = field(default=None)
    position: Optional[int] = field(default=None)
    tilt: Optional[int] = field(default=None)
    current_cover_state: Optional[str] = field(default=None)
    position_cover_state: Optional[str] = field(default=None)
    tilt_cover_state: Optional[str] = field(default=None)
    open_cover_state: Optional[str] = field(default=None)
    close_cover_state: Optional[str] = field(default=None)
    stop_cover_state: Optional[str] = field(default=None)
    position_changed: Optional[bool] = field(default=None)
    tilt_changed: Optional[bool] = field(default=None)


class TestCovers:
    @pytest.fixture(autouse=True)
    def pre(self, _modbus_client: ModbusClient, mocker: MockerFixture):
        mock_response_is_error = MagicMock()
        mock_response_is_error.isError.return_value = False

        _modbus_client.tcp.write_coil.return_value = mock_response_is_error

        mocker.patch("unipi_control.integrations.covers.CoverTimer", new_callable=MagicMock)


class TestHappyPathCovers(TestCovers):
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (
                CoverOptions(cover_type="blind", calibrate_mode=True),
                CoverExpected(calibration_started=True, calibrate_mode=False),
            ),
            (
                CoverOptions(cover_type="roller_shutter", calibrate_mode=False),
                CoverExpected(calibration_started=False, calibrate_mode=False),
            ),
        ],
    )
    async def test_calibrate(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        mocker: MockerFixture,
        options: CoverOptions,
        expected: CoverExpected,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = options.calibrate_mode

        mock_monotonic = mocker.patch("unipi_control.integrations.covers.time.monotonic", new_callable=MagicMock)
        mock_monotonic.return_value = 0
        cover_run_time: Optional[float] = await cover.calibrate()

        assert cover._calibration_started is expected.calibration_started

        if cover_run_time is not None:
            mock_monotonic.return_value = cover_run_time

        await cover.stop()

        assert cover.calibrate_mode == expected.calibrate_mode

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (
                CoverOptions(cover_type="blind", position=0),
                CoverExpected(
                    position=100,
                    tilt=100,
                    current_cover_state="closed",
                    open_cover_state="opening",
                    stop_cover_state="open",
                    position_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="blind", position=50),
                CoverExpected(
                    position=100,
                    tilt=100,
                    current_cover_state="stopped",
                    open_cover_state="opening",
                    stop_cover_state="open",
                    position_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="roller_shutter", position=None),
                CoverExpected(
                    position=None,
                    tilt=None,
                    current_cover_state="stopped",
                    open_cover_state="opening",
                    stop_cover_state="stopped",
                    position_changed=False,
                ),
            ),
        ],
    )
    async def test_open(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        mocker: MockerFixture,
        options: CoverOptions,
        expected: CoverExpected,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = False
        cover._current_position = options.position
        cover.position = options.position
        cover._update_state()

        assert cover.state == expected.current_cover_state

        mock_monotonic = mocker.patch("unipi_control.integrations.covers.time.monotonic", new_callable=MagicMock)
        mock_monotonic.return_value = 0

        if (cover_run_time := await cover.open()) is not None:
            mock_monotonic.return_value = cover_run_time

        assert cover.state == expected.open_cover_state

        await cover.stop()
        cover.read_position()

        assert cover.position == expected.position
        assert cover.tilt == expected.tilt
        assert cover.state == expected.stop_cover_state
        assert cover.state_changed is True
        assert cover.position_changed == expected.position_changed

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (
                CoverOptions(cover_type="blind", position=100),
                CoverExpected(
                    position=0,
                    tilt=0,
                    current_cover_state="open",
                    close_cover_state="closing",
                    stop_cover_state="closed",
                    position_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="blind", position=50),
                CoverExpected(
                    position=0,
                    tilt=0,
                    current_cover_state="stopped",
                    close_cover_state="closing",
                    stop_cover_state="closed",
                    position_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="roller_shutter", position=None),
                CoverExpected(
                    position=None,
                    tilt=None,
                    current_cover_state="stopped",
                    close_cover_state="closing",
                    stop_cover_state="stopped",
                    position_changed=False,
                ),
            ),
        ],
    )
    async def test_close(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        mocker: MockerFixture,
        options: CoverOptions,
        expected: CoverExpected,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = False
        cover._current_position = options.position
        cover.position = options.position
        cover._update_state()

        assert cover.state == expected.current_cover_state

        mock_monotonic = mocker.patch("unipi_control.integrations.covers.time.monotonic", new_callable=MagicMock)

        mock_monotonic.return_value = 0
        cover_run_time: Optional[float] = await cover.close()

        assert cover.state == expected.close_cover_state

        if cover_run_time is not None:
            mock_monotonic.return_value = cover_run_time

        await cover.stop()
        cover.read_position()

        assert cover.position == expected.position
        assert cover.tilt == expected.tilt
        assert cover.state == expected.stop_cover_state
        assert cover.state_changed is True
        assert cover.position_changed == expected.position_changed

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (CoverOptions(cover_type="blind", position=0, cover_state=CoverState.CLOSING), "closed"),
            (CoverOptions(cover_type="blind", position=50, cover_state=CoverState.OPENING), "stopped"),
            (CoverOptions(cover_type="blind", position=100, cover_state=CoverState.OPENING), "open"),
        ],
    )
    async def test_stop(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        mocker: MockerFixture,
        options: CoverOptions,
        expected: str,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = False
        cover.position = options.position
        cover.state = options.cover_state

        mock_monotonic = mocker.patch("unipi_control.integrations.covers.time.monotonic", new_callable=MagicMock)
        mock_monotonic.return_value = 0

        await cover.stop()
        assert cover.state == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (
                CoverOptions(cover_type="blind", position=50, current_tilt=50, tilt=25),
                CoverExpected(
                    tilt=25,
                    current_cover_state="stopped",
                    tilt_cover_state="closing",
                    stop_cover_state="stopped",
                    tilt_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="blind", position=50, current_tilt=50, tilt=75),
                CoverExpected(
                    tilt=75,
                    current_cover_state="stopped",
                    tilt_cover_state="opening",
                    stop_cover_state="stopped",
                    tilt_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="roller_shutter", position=None, current_tilt=None, tilt=25),
                CoverExpected(
                    tilt=None,
                    current_cover_state="stopped",
                    tilt_cover_state="stopped",
                    stop_cover_state="stopped",
                    tilt_changed=False,
                ),
            ),
        ],
    )
    async def test_set_tilt(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        mocker: MockerFixture,
        options: CoverOptions,
        expected: CoverExpected,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = False
        cover._current_tilt = options.current_tilt
        cover.tilt = options.current_tilt
        cover._current_position = options.position
        cover.position = options.position
        cover._update_state()

        assert cover.state == expected.current_cover_state

        mock_monotonic = mocker.patch("unipi_control.integrations.covers.time.monotonic", new_callable=MagicMock)
        mock_monotonic.return_value = 0

        assert isinstance(options.tilt, int)

        cover_run_time: Optional[float] = await cover.set_tilt(options.tilt)

        assert cover.state == expected.tilt_cover_state

        if cover_run_time is not None:
            mock_monotonic.return_value = cover_run_time

        await cover.stop()
        cover.read_position()

        assert cover.tilt == expected.tilt
        assert cover.state == expected.stop_cover_state
        assert cover.state_changed is True
        assert cover.tilt_changed == expected.tilt_changed

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (
                CoverOptions(cover_type="blind", current_position=50, tilt=50, position=25),
                CoverExpected(
                    position=25,
                    current_cover_state="stopped",
                    position_cover_state="closing",
                    stop_cover_state="stopped",
                    position_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="blind", current_position=50, tilt=50, position=75),
                CoverExpected(
                    position=75,
                    current_cover_state="stopped",
                    position_cover_state="opening",
                    stop_cover_state="stopped",
                    position_changed=True,
                ),
            ),
            (
                CoverOptions(cover_type="roller_shutter", current_position=None, tilt=None, position=25),
                CoverExpected(
                    position=None,
                    current_cover_state="stopped",
                    position_cover_state="stopped",
                    stop_cover_state="stopped",
                    position_changed=False,
                ),
            ),
        ],
    )
    async def test_set_position(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        mocker: MockerFixture,
        options: CoverOptions,
        expected: CoverExpected,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = False
        cover._current_tilt = options.tilt
        cover.tilt = options.tilt
        cover._current_position = options.current_position
        cover.position = options.current_position
        cover._update_state()

        assert cover.state == expected.current_cover_state

        mock_monotonic = mocker.patch("unipi_control.integrations.covers.time.monotonic", new_callable=MagicMock)
        mock_monotonic.return_value = 0

        assert isinstance(options.position, int)

        cover_run_time: Optional[float] = await cover.set_position(options.position)

        assert cover.state == expected.position_cover_state

        if cover_run_time is not None:
            mock_monotonic.return_value = cover_run_time

        await cover.stop()
        cover.read_position()

        assert cover.position == expected.position
        assert cover.state == expected.stop_cover_state
        assert cover.state_changed is True
        assert cover.position_changed == expected.position_changed

    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (CoverOptions(cover_type="blind"), "MOCKED_FRIENDLY_NAME - BLIND"),
            (CoverOptions(cover_type="roller_shutter"), "MOCKED_FRIENDLY_NAME - ROLLER SHUTTER"),
        ],
    )
    def test_friendly_name(self, _config_loader: ConfigLoader, _covers: CoverMap, options: CoverOptions, expected: str):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))

        assert str(cover) == expected

    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (CoverOptions(cover_type="blind", current_cover_state="stopped", cover_state="close"), True),
            (CoverOptions(cover_type="blind", current_cover_state="closed", cover_state="closed"), False),
        ],
    )
    def test_state_changed(
        self, _config_loader: ConfigLoader, _covers: CoverMap, options: CoverOptions, expected: bool
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover._current_state = options.current_cover_state
        cover.state = options.cover_state

        assert cover.state_changed == expected

    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (CoverOptions(cover_type="blind", current_position=0, position=50), True),
            (CoverOptions(cover_type="blind", current_position=50, position=50), False),
            (CoverOptions(cover_type="roller_shutter", current_position=None, position=None), False),
        ],
    )
    def test_position_changed(
        self, _config_loader: ConfigLoader, _covers: CoverMap, options: CoverOptions, expected: bool
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover._current_position = options.current_position
        cover.position = options.position

        assert cover.position_changed == expected


class TestUnhappyPathCovers(TestCovers):
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize("options, expected", [(CoverOptions(cover_type="blind"), 105)])
    async def test_open_with_invalid_position(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        options: CoverOptions,
        expected: int,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = False
        cover._current_position = expected
        cover.position = expected

        cover_run_time: Optional[float] = await cover.open()

        assert cover_run_time is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize("options, expected", [(CoverOptions(cover_type="blind"), 50)])
    async def test_open_with_calibrate_mode(
        self, _config_loader: ConfigLoader, _covers: CoverMap, options: CoverOptions, expected: int
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = True
        cover._current_position = expected
        cover.position = expected

        cover_run_time: Optional[float] = await cover.open()

        assert cover_run_time is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize("options, expected", [(CoverOptions(cover_type="blind"), 50)])
    async def test_close_with_calibrate_mode(
        self, _config_loader: ConfigLoader, _covers: CoverMap, options: CoverOptions, expected: int
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = True
        cover._current_position = expected
        cover.position = expected

        cover_run_time: Optional[float] = await cover.close()

        assert cover_run_time is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    @pytest.mark.parametrize(
        "options, expected",
        [
            (
                CoverOptions(cover_type="blind", calibrate_mode=True),
                CoverExpected(calibration_started=True, calibrate_mode=True),
            ),
            (
                CoverOptions(cover_type="roller_shutter", calibrate_mode=False),
                CoverExpected(calibration_started=False, calibrate_mode=False),
            ),
        ],
    )
    async def test_calibrate_stopped(
        self,
        _config_loader: ConfigLoader,
        _covers: CoverMap,
        mocker: MockerFixture,
        options: CoverOptions,
        expected: CoverExpected,
    ):
        cover: Cover = next(_covers.by_cover_types([options.cover_type]))
        cover.calibrate_mode = options.calibrate_mode

        mock_monotonic = mocker.patch("unipi_control.integrations.covers.time.monotonic", new_callable=MagicMock)
        mock_monotonic.return_value = 0
        cover_run_time: Optional[float] = await cover.calibrate()

        assert cover._calibration_started is expected.calibration_started

        if cover_run_time is not None:
            mock_monotonic.return_value = cover_run_time / 2

        await cover.stop()

        assert cover.calibrate_mode == expected.calibrate_mode
