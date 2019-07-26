import spidev


def readADC(channel):
    values = []
    spi = spidev.SpiDev(0, 0)
    spi.max_speed_hz = 100000
    for i in range(0, 18):
        buffer = spi.xfer2([0x06, channel<<6, 0])
        value = ((buffer[1] & 0x0F) << 8) + buffer[2]
        print value
        values.append(value)
    values.remove(max(values))
    values.remove(min(values))

    value = float(sum(values))/len(values)
    spi.close()
    return value


if __name__ == '__main__':
    print ((3.3*(float(readADC(0))/(2**12)))/(0.020*147.14))/2.0
    print ((3.3*(float(readADC(3))/(2**12)))/(0.020*147.77))/2.0

