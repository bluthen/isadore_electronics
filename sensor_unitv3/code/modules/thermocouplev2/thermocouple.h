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
#ifndef __THERMOCOUPLE_H
#define __THERMOCOUPLE_H


#define THERMOCOUPLE_DDR DDRB
#define THERMOCOUPLE_PORT PORTB
#define THERMOCOUPLE_PIN PB2

#define SPI_DDR DDRB
#define SPI_PORT PORTB
#define SPI_SCK PB5
#define SPI_MISO PB4
#define SPI_MOSI PB3

/**
 * Initialize thermocouple
 */
uint8_t thermocouple_init(void);

/**
 * Read thermocouple value
 */
uint16_t thermocouple_read(void);

#endif
