#!/usr/bin/env python3

import argparse
import asyncio
import json
import os
import uuid
from collections import namedtuple
from timeit import default_timer as timer

import paho.mqtt.client as mqtt

from api.devices import (
    DeviceDigitalInput,
    DeviceDigitalOutput,
    DeviceRelay,
)
from api.homeassistant import HomeAssistant
from api.mqtt import MqttMixin
from api.settings import (
    API,
    logger,
)


class UnipiAPI(MqttMixin):
    """Unipi API class for subscribe/publish topics."""

    def __init__(self, client_id: str, debug: bool):
        """Connect to mqtt broker.

        Args:
            client_id (str): unique client id
            debug (bool): enable debug logging
        """
        logger.info(f"Client ID: {client_id}")

        self.debug: bool = debug
        self.client = self.connect(client_id)
        self._devices: dict = {}
        self._publish_timer = None
        self._subscribe_timer = None

        # Init home assistant discovery
        self._ha = HomeAssistant(client=self.client)

    @property
    def devices(self) -> dict:
        """Create devices dict with circuit as name and die device class as key."""
        _devices: dict = {}

        for circuit in os.listdir(API["sysfs"]["devices"]):
            device_path: str = os.path.join(API["sysfs"]["devices"], circuit)
      
            for device_class in [DeviceRelay, DeviceDigitalInput, DeviceDigitalOutput]:
                if device_class.FOLDER_REGEX.match(circuit):
                    device = device_class(device_path)
                    key: str = f"unipi/{device.dev}/{device.dev_type}/{device.circuit}"
                    _devices[key] = device

        return _devices

    async def run(self) -> None:
        """Run publish method in a endless asyncio loop."""
        devices: dict = self.devices

        while True:
            self._publish_timer = timer()
            results: list = await asyncio.gather(*[device.get() for device in devices.values()])

            for device in results:
                if device.changed:
                    self.publish(device)

            await asyncio.sleep(250e-3)

    def on_connect(self, client, userdata, flags, rc: int) -> None:
        super().on_connect(client, userdata, flags, rc)
        self.subscribe()
        
        # Subscribe home assistant discovery
        self._ha.subscribe()

    def on_message_thread(self, message):
        """Run on_message method in a thread.

        Args:
            message (dict): message dict from the mqtt on_message method.
        """
        self._subscribe_timer = timer()

        async def on_message_cb(message):
            key: str = message.topic.removesuffix("/set")
            device = self.devices.get(key)
            
            if device:
                func = getattr(device, "set", None)

                if func:
                    await func(json.loads(message.payload.decode()))
        
        asyncio.run(on_message_cb(message), debug=self.debug)
        logger.debug(f"Subscribe timer: {timer() - self._subscribe_timer}")

        # Message callback for home assistant discovery
        self._ha.on_message(message)

    def subscribe(self) -> None:
        """Subscribe topics for relay devices."""
        for device_name in os.listdir(API["sysfs"]["devices"]):
            device_path: str = os.path.join(API["sysfs"]["devices"], device_name)
            
            for device_class in [DeviceRelay, DeviceDigitalOutput]:
                if device_class.FOLDER_REGEX.match(device_name):
                    device = device_class(device_path)
                    topic: str = f"unipi/{device.dev}/{device.dev_type}/{device.circuit}/set"

                    self.client.subscribe(topic, qos=1)
                    logger.info(f"Subscribe topic `{topic}`")

    def publish(self, device: namedtuple) -> None:
        """Publish topics for all devices.

        Args:
            device (namedtuple): device infos from the device class."
        """
        topic: str = f"unipi/{device.dev}/{device.dev_type}/{device.circuit}/get"
        values: dict = {k: v for k, v in dict(device._asdict()).items() if v is not None}
        values.pop("changed")

        payload: str = json.dumps(values)
        rc, mid = self.client.publish(topic, payload, qos=1)
        logger.debug(f"Publish timer: {timer() - self._publish_timer}")

        if rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Send `{payload}` to topic `{topic}` - Message ID: {mid}")
        else:
            logger.error(f"Failed to send message to topic `{topic}` - Message ID: {mid}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, type=bool, help="Debug")
    args = parser.parse_args()

    try:
        asyncio.run(
            UnipiAPI(
                client_id=f"unipi-{uuid.uuid4()}", 
                debug=args.debug
            ).run(),
            debug=args.debug,
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted")
    except Exception as e:
        print(e)
