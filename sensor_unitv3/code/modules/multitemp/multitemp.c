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

#include "multitemp/multitemp.h"
#include "multitemp/ds2482s_ds18b20.h"
#include "multitemp/ds2482s.h"


#define MULTITEMP_TWI_ADDRESS 0x30
#define MULTITEMP_NO_ROM 0xFFFF
#define MULTITEMP_ADDR_NO_ROM 0xFFFFFFFF

static uint8_t _ch=4;
static uint8_t _chmap[] = {4, 0, 1, 2};
static bool end_of_sensors = false;


void multitemp_init(void) {
	ds2482s_set_twi_address(MULTITEMP_TWI_ADDRESS);
	multitemp_reset();
}

uint16_t multitemp_get(uint8_t channel) {
	uint8_t dsaddress[8];
	bool found;

	if( channel > 0 && channel < 5 && (channel -1) != _ch) {
		multitemp_reset();
		_ch = channel -1;
		ds2482s_set_channel(_chmap[channel-1]);
	}
	if(end_of_sensors) {
		return MULTITEMP_NO_ROM; 
	}
	found = ds2482s_rom_search();
	if(!found) {
		end_of_sensors = true;
		return MULTITEMP_NO_ROM; 
	}

	ds2482s_rom_search_copy(dsaddress);
	return ds2482s_ds18b20_read_temperature(dsaddress);
}

bool multitemp_get_addr(uint8_t channel, uint8_t* dsaddress) {
	bool found;

	if( channel > 0 && channel < 5 && (channel -1) != _ch) {
		multitemp_reset();
		_ch = channel -1;
		ds2482s_set_channel(_chmap[channel-1]);
	}
	dsaddress[0] = 0xFF;
	dsaddress[1] = 0xFF;
	dsaddress[2] = 0xFF;
	dsaddress[3] = 0xFF;
	dsaddress[4] = 0xFF;
	dsaddress[5] = 0xFF;
	dsaddress[6] = 0xFF;
	dsaddress[7] = 0xFF;
	if(end_of_sensors) {
		return false;
	}
	found = ds2482s_rom_search();
	if(!found) {
		end_of_sensors = true;
		return false;
	}

	ds2482s_rom_search_copy(dsaddress);
	return true;
}


void multitemp_reset(void) {
	ds2482s_rom_search_reset();
	end_of_sensors = false;
}
