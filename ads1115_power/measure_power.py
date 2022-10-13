import asyncio
import board
import busio
import struct
import numpy as np
from adafruit_bus_device.i2c_device import I2CDevice


# This function getting data same way as function below, except using asyncio.sleep() instead time.sleep()
def measure(channel, samples, gain, voltage, pf):
    currents = []

    i2c = busio.I2C(board.SCL, board.SDA)
    i2c_device = I2CDevice(i2c, 0x48)

    pin = channel + 0x04

    config = 0
    config |= (pin & 0x07) << 12
    config |= 0x0200
    config |= 0x0000
    config |= 0x0080
    config |= 0x0003

    buf = bytearray(3)
    buf[0] = 0x01
    buf[1] = (config >> 8) & 0xFF
    buf[2] = config & 0xFF
    with i2c_device as i2c:
        i2c.write(buf)

    asyncio.sleep(2 / 128)  # Fixed detection of blocking call

    buf = bytearray(3)
    with i2c_device as i2c:
        i2c.write_then_readinto(bytearray([0x00]), buf, in_end=2)

    last_result = buf[0] << 8 | buf[1]
    raw_adc = last_result.to_bytes(2, "big")
    value = struct.unpack(">h", raw_adc)[0]

    volts = value * 4.096 / 32767
    currents.append((volts / 200) * 1000)

    while len(currents) < samples:
        buf = bytearray(3)
        with i2c_device as i2c:
            i2c.readinto(buf, end=2)

        last_result = buf[0] << 8 | buf[1]
        raw_adc = last_result.to_bytes(2, "big")
        value = struct.unpack(">h", raw_adc)[0]

        volts = value * 4.096 / 32767
        currents.append((volts / 200) * 1000)

    currents = np.array(currents)
    current_rms = np.sqrt(np.mean(currents ** 2))
    watt = (current_rms * voltage) * pf

    return watt


# import board
# import busio
# import adafruit_ads1x15.ads1115 as ads1115
# from adafruit_ads1x15.analog_in import AnalogIn
# import numpy as np
#
#
# def measure(channel, samples, gain, voltage, pf):
#     i2c = busio.I2C(board.SCL, board.SDA)
#     ads = ads1115.ADS1115(i2c)
#     ads.gain = gain
#     ads.mode = ads1115.Mode.CONTINUOUS
#
#     currents = []
#     while len(currents) < samples:
#         channel_data = AnalogIn(ads, int(channel))
#         currents.append((channel_data.voltage / 200) * 1000)
#
#     currents = np.array(currents)
#     current_rms = np.sqrt(np.mean(currents ** 2))
#     watt = (current_rms * voltage) * pf
#
#     return watt
