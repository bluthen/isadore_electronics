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
#ifndef DS2482S_H
#define DS2482S_H

#include <stdbool.h>
#include <stdint.h>

#define DS2482S_CMD_RESET 0xF0
#define DS2482S_CMD_RPOINTER 0xE1
#define DS2482S_CMD_WRITE_CONFIG 0xD2
#define DS2482S_CMD_CHANNEL 0xC3
#define DS2482S_CMD_1WIRE_RESET 0xB4
#define DS2482S_CMD_WRITE_1WIRE_BIT 0x87
#define DS2482S_CMD_WRITE_1WIRE_BYTE 0xA5
#define DS2482S_CMD_READ_1WIRE_BYTE 0x96
#define DS2482S_CMD_1WIRE_TRIPLET 0x78
#define OWIRE_CMD_READROM			0x33
#define OWIRE_CMD_SEARCHROM			0xF0


#define DS2482S_RPOINTER_STATUS 0xF0
#define DS2482S_RPOINTER_DATA 0xE1
#define DS2482S_RPOINTER_CHANNEL 0xD2
#define DS2482S_RPOINTER_CONFIG 0xC3

#define DS2482_CONFIG_APU	0x01
#define DS2482_CONFIG_SPU	0x04
#define DS2482_CONFIG_1WS	0x08


#define DS2482_STATUS_1WB	0x01
#define DS2482_STATUS_SBR	0x20
#define DS2482_STATUS_TSB	0x40
#define DS2482_STATUS_DIR	0x80

bool ds2482s_cmd(uint8_t cmd, uint8_t parameter);
bool ds2482s_reset(void);
bool ds2482s_set_read_pointer(uint8_t pointer_location);
bool ds2482s_write_config(uint8_t config);
void ds2482s_set_twi_address(uint8_t twi_address);
bool ds2482s_set_channel(uint8_t channel);
uint8_t ds2482s_read_byte(void);
bool ds2482s_1wire_reset(void);
void ds2482s_1wire_wait(void);
bool ds2482s_1wire_write_bit(bool high);
bool ds2482s_1wire_write_byte(uint8_t byte);
bool ds2482s_1wire_write_64bit(uint8_t* data_buffer);
bool ds2482s_1wire_read_64bit(uint8_t* fill_buffer);
uint8_t ds2482s_1wire_read_byte(void);
bool ds2482s_1wire_triplet(uint8_t direction_bit_byte);
bool ds2482s_1wire_readrom(uint8_t* address_buffer);


void ds2482s_rom_search_reset(void);
void ds2482s_rom_search_copy(uint8_t* address); 
bool ds2482s_rom_search(void);

//uint8_t OWSearch(uint8_t resetSearch, bool *lastDevice, uint8_t *deviceAddress);

/**
 * Find next device rom address.
 * @param addr The location it will write the found address.
 * @return True if found address, False if no more are found or error.
 */
//bool ds2482s_1wire_search(uint8_t* addr);

/**
 * Resets the search to start over.
 */
//void ds2482s_1wire_reset_search(void);
#endif
