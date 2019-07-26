//   Copyright 2010-2019 Dan Elliott, Russell Valentine
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.
#include <avr/io.h>
#include <util/delay.h>
#include "thermocouplev2/thermocouple.h"

/** Reading byte from SPI, CS pin should already be toggled. */
uint8_t thermocouple_spi_read8(void)
{
    uint8_t value=0;
    SPDR=0x00;
    while(!(SPSR & (1<<SPIF))){}
    value=SPDR;
    return value;
}

/** Togles CS pin for port and pin, reads 32 bit value from spi. */
int32_t thermocouple_spi_read32(volatile uint8_t *port, uint8_t pin)
{
    int32_t value = 0;
    *port &= ~(1<<pin);
    _delay_us(64);
    value = (int32_t) thermocouple_spi_read8() << 24;
    value |= (int32_t)thermocouple_spi_read8() << 16;
    value |= (int32_t)thermocouple_spi_read8() << 8;
    value |= (int32_t)thermocouple_spi_read8();
    *port |= (1<<pin);
    _delay_us(64);
    if(value & 0x07) {
        return 0;
    }
    if (value & 0x80000000) {
        value = 0xFFFFC000 | ((value >> 18) & 0x00003FFFF);
    } else {
        value >>= 18;
    }
    return value;
}



uint8_t thermocouple_init(void) {
	THERMOCOUPLE_DDR |= (1<<THERMOCOUPLE_PIN); //Output on CS PIN
	THERMOCOUPLE_PORT |= (1<<THERMOCOUPLE_PIN); // HIGH on CS PIN
	return 1;
}

uint16_t thermocouple_read(void) {
	return (uint16_t)thermocouple_spi_read32(&THERMOCOUPLE_PORT, THERMOCOUPLE_PIN);
}
