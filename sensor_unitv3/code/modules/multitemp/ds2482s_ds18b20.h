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
#ifndef DS2482S_DS18B20_H
#define DS2482S_DS18B20_H

#include <stdint.h>

#define DS18B20_CMD_CONVERTTEMP		0x44
#define DS18B20_CMD_RSCRATCHPAD		0xbe
#define DS18B20_CMD_WSCRATCHPAD		0x4e
#define DS18B20_CMD_CPYSCRATCHPAD	0x48
#define DS18B20_CMD_RECEEPROM		0xb8
#define DS18B20_CMD_RPWRSUPPLY		0xb4
#define DS18B20_CMD_SEARCHROM		0xf0
#define DS18B20_CMD_READROM			0x33
#define DS18B20_CMD_MATCHROM		0x55
#define DS18B20_CMD_SKIPROM			0xcc
#define DS18B20_CMD_ALARMSEARCH		0xec
#define DS18B20_DECIMAL_STEPS_12BIT	625 //0.0625

#define DS2482S_DS18B20_ERROR_TWI 0x02
#define DS2482S_DS18B20_ERROR_CRC 0x01

uint8_t ds2482s_ds18b20_get_error(void);
uint16_t ds2482s_ds18b20_read_temperature(uint8_t* ds18b20_addr);

#endif
