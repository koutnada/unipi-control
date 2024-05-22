import contextlib
from time import sleep
from time import time

from pymodbus.client import ModbusSerialClient

units = [
    1,
    102,
    201,
    202,
    203,
]

registers = [
    # DI 1.x / RO 1.x
    {"address": 0, "count": 2},
]


def main():
    client = ModbusSerialClient(port="/dev/extcomm/0/0", baudrate=9600)

    while True:
        if not client.connected:
            client.connect()

        start1 = time()

        for unit in units:
            start2 = time()
            for register in registers:
                response = client.read_input_registers(**register, slave=unit)
                # print(response.registers)
            sleep(3.5 * 11 / 9600)
            print("UNIT", unit, time() - start2)
        print("TOTAL", time() - start1)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        main()
