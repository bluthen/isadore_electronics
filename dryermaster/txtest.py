import spidev
import sys


spi = spidev.SpiDev()
spi.open(0, 1)


value = int(sys.argv[1])

hvalue, lvalue = divmod(value, 0x100)

spi.writebytes([hvalue | 0x30, lvalue])

spi.close()
