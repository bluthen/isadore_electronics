#include <avr/io.h>
/**
 * Reads 16 bit value from adc using admux to set adc pin.
 */
uint16_t read_adc16(uint8_t admux)
{
	uint16_t value;
	//wdt_reset();
	ADMUX = admux;
	ADCSRA|=0x40;
	//Wait for next ADC conversion
	while((ADCSRA & 0x40) != 0){}
	value = ADCW;
	//wdt_reset();
	return value;
}

