import asyncio
import contextlib
from time import time

from pymodbus.client import AsyncModbusSerialClient

units = [
    1,
]

registers = [
    # DI 1.x / RO 1.x
    {"address": 0, "count": 2},
]


async def main():
    client = AsyncModbusSerialClient(port="/dev/extcomm/0/0", baudrate=9600)

    while True:
        if not client.connected:
            print("connect")
            await client.connect()

        start1 = time()

        for unit in units:
            start2 = time()

            for register in registers:
                response = await client.read_input_registers(**register, slave=unit)
                # print(response.registers)
            await asyncio.sleep(3.5 * 11 / 9600)

            print("UNIT", unit, time() - start2)
        print("TOTAL", time() - start1)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
