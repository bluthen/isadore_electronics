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
#include <stdio.h>
#include <util/delay.h>
#include <util/crc16.h>

#include "multitemp/ds2482s.h"
#include "multitemp/ds2482s_ds18b20.h"

//#define DEBUG

static uint8_t ds2482s_ds18b20_error = 0;

uint8_t ds2482s_ds18b20_get_error(void) {
	return ds2482s_ds18b20_error;
}

/**
 * Read temperature. 
 * @param ds18b20_addr The address of the DS18B20; If NULL then skiprom should 
 * only be used if only one sensor on channel.
 * @return Temperature data.
 */
uint16_t ds2482s_ds18b20_read_temperature(uint8_t* ds18b20_addr) {
	uint8_t i, scratchpad[9], crc=0;
	uint16_t temperature;

#ifdef DEBUG
	if(ds18b20_addr != NULL) {
		fprintf(stderr, "D: read_temp addr %#x %#x %#x %#x %#x %#x %#x %#x\n",
			ds18b20_addr[0], ds18b20_addr[1], ds18b20_addr[2], ds18b20_addr[3],
			ds18b20_addr[4], ds18b20_addr[5], ds18b20_addr[6], ds18b20_addr[7]
		);
	} else {
	}
#endif

#ifdef DEBUG
	fprintf(stderr, "D: read_temp: reset\n");
#endif
	if(!ds2482s_1wire_reset()) {
	   	ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
		return 0;
	}

	if (ds18b20_addr != NULL) {
#ifdef DEBUG
		fprintf(stderr, "D: read_temp: matchrom\n");
#endif
		if(!ds2482s_1wire_write_byte(DS18B20_CMD_MATCHROM) ||
		   !ds2482s_1wire_write_64bit(ds18b20_addr)) {
	   		ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
			return 0;
		}
	} else {
#ifdef DEBUG
		fprintf(stderr, "D: read_temp: skiprom\n");
#endif
		if(!ds2482s_1wire_write_byte(DS18B20_CMD_SKIPROM)) {
	   		ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
			return 0;
		}
	}

#ifdef DEBUG
	fprintf(stderr, "D: read_temp: convert temp\n");
#endif
	if (!ds2482s_1wire_write_byte(DS18B20_CMD_CONVERTTEMP)) {

		ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
		return 0;
	}
	//Wait while conversion happens
	//need at least 750ms for 12 bit mode.
	_delay_ms(800);

#ifdef DEBUG
	fprintf(stderr, "D: read_temp: reset\n");
#endif
	// Reset, skip ROM and send command to read Scratchpad
	if (!ds2482s_1wire_reset()) {
		ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
		return 0;
	}

	if (ds18b20_addr != NULL) {
#ifdef DEBUG
		fprintf(stderr, "D: read_temp: matchrom\n");
#endif
		if (!ds2482s_1wire_write_byte(DS18B20_CMD_MATCHROM) ||
		    !ds2482s_1wire_write_64bit(ds18b20_addr) ) {
			ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
			return 0;
		}
	} else {
#ifdef DEBUG
		fprintf(stderr, "D: read_temp: skiprom\n");
#endif
		if (!ds2482s_1wire_write_byte(DS18B20_CMD_SKIPROM)) {
			ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
			return 0;
		}
	}

#ifdef DEBUG
	fprintf(stderr, "D: read_temp: cmd read scratch\n");
#endif
	if(!ds2482s_1wire_write_byte(DS18B20_CMD_RSCRATCHPAD)) {
		ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_TWI; 
		return 0;
	}

#ifdef DEBUG
	fprintf(stderr, "D: read_temp: read bytes\n");
#endif
	for(i = 0; i < 9; i++ ){
		scratchpad[i] = ds2482s_1wire_read_byte();
		#ifdef DEBUG
			fprintf(stderr, "D: read_temp: %d - %d\n", i, scratchpad[i]);
		#endif
	}


#ifdef DEBUG
	fprintf(stderr, "D: read_temp: reset\n");
#endif
	ds2482s_1wire_reset();

	temperature  = scratchpad[1] << 8;
	temperature += scratchpad[0];

	// CRC Check
	for (i = 0; i < 8; i++) {
		crc = _crc_ibutton_update(crc, scratchpad[i]);
	}

	if (crc != scratchpad[8]) {
		// CRC ERROR
		ds2482s_ds18b20_error = DS2482S_DS18B20_ERROR_CRC; 
#ifdef DEBUG
		fprintf(stderr, "D: read_temp: crc error: %d, %d\n", scratchpad[8], crc);
#endif
		return 0;
	}

#ifdef DEBUG
	fprintf(stderr, "DRT: 9\n");
#endif

	return temperature;
}

