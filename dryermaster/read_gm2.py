import spidev
import RPi.GPIO as GPIO


# BCM Pin 4 if voltage divider click is in slot 1
# BCM Pin 13 if voltage divider click is in slot 2

RELAY_PIN = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.IN)

def read_relay():
    return GPIO.input(RELAY_PIN)


def read4_20(slot):
    """"@returns value between ~800 - 4095"""
    spi = spidev.SpiDev()
    spi.open(0, slot)

    values = []

    for i in range(0, 18):
        adc_raw = spi.readbytes(2)
        #print adc_raw
        adc_raw[0] = adc_raw[0] & 0x1F
        adc_raw = ( (adc_raw[0] << 8) | adc_raw[1] ) >> 1
        # adc_raw = adc_raw/100
        values.append( adc_raw )

    values.remove(max(values))
    values.remove(min(values))

    value = float(sum(values))/len(values)
    value += value/100.0 # Correction from shunt resistor
    return value

