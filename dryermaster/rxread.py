import spidev


spi = spidev.SpiDev()
spi.open(0, 0)


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
value += value/100.0
print str(value)

