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
#include <util/delay.h>
#include <stdio.h>

#include <util/crc16.h>

#include "i2cmaster/i2cmaster.h"
#include "multitemp/ds2482s.h"

#define DS2482_CHAN0		0xF0
#define DS2482_CHAN0_ACK	0xB8
#define DS2482_CHAN1		0xE1
#define DS2482_CHAN1_ACK	0xB1
#define DS2482_CHAN2		0xD2
#define DS2482_CHAN2_ACK	0xAA
#define DS2482_CHAN3		0xC3
#define DS2482_CHAN3_ACK	0xA3
#define DS2482_CHAN4		0xB4
#define DS2482_CHAN4_ACK	0x9C
#define DS2482_CHAN5		0xA5
#define DS2482_CHAN5_ACK	0x95
#define DS2482_CHAN6		0x96
#define DS2482_CHAN6_ACK	0x8E
#define DS2482_CHAN7		0x87
#define DS2482_CHAN7_ACK	0x87

//#define DEBUG

// TODO: Check status register for polling and stuff.

/** Holds twi_address to use. */
static uint8_t ds2482s_twi_address = 0;
static uint8_t ds2482s_channels[] = {DS2482_CHAN0, DS2482_CHAN0_ACK, 
DS2482_CHAN1, DS2482_CHAN1_ACK,
DS2482_CHAN2, DS2482_CHAN2_ACK,
DS2482_CHAN3, DS2482_CHAN3_ACK,
DS2482_CHAN4, DS2482_CHAN4_ACK,
DS2482_CHAN5, DS2482_CHAN5_ACK,
DS2482_CHAN6, DS2482_CHAN6_ACK,
DS2482_CHAN7, DS2482_CHAN7_ACK};


/**
 * Sets thw twi_addrress that all future functions calls should use.
 */
void ds2482s_set_twi_address(uint8_t twi_address) {
	ds2482s_twi_address = twi_address;
}

/**
 * Process a command to the DS2482S.
 */
bool ds2482s_cmd(uint8_t cmd, uint8_t parameter) {
#ifdef DEBUG
	fprintf(stderr, "D: ds2482_cmd %#x, %#x\n", cmd, parameter);
#endif
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);

	if(i2c_write(cmd) != 0){
#ifdef DEBUG
		fprintf(stderr, "D: w1: TWI Write fail\n");
#endif
		return false;
	}
	if(i2c_write(parameter) != 0){
#ifdef DEBUG
		fprintf(stderr, "D: w2: TWI Write fail\n");
#endif
		return false;
	}
	i2c_stop();
	return true;
}

/** Reset the DS2482S. */
bool ds2482s_reset() {
	uint8_t status = 0;
	bool retval;
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);
	retval = i2c_write(DS2482S_CMD_RESET) ==0;
	if(retval) {
		retval = i2c_rep_start(ds2482s_twi_address+I2C_READ) ==0;
	}
	if(retval) {
		status = i2c_readNak();
	}
	i2c_stop();
	return (retval && (status & 0x10) == 0x10);
}

/** Set read point in the DS2482S. */
bool ds2482s_set_read_pointer(uint8_t pointer_location) {
	return ds2482s_cmd(DS2482S_CMD_RPOINTER, pointer_location);
}

/**
 * Sets config for the device, does ones compilment for you.
 */
bool ds2482s_write_config(uint8_t config) {
#ifdef DEBUG
	fprintf(stderr, "D: ds2482_swrite_config\n");
#endif
	bool retval;
	uint8_t nconfig;
	uint8_t rconfig = ((~(config << 4)) & 0xF0) + (config & 0x0F);
	//TODO: Only check if not already set to desired value.
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);
	retval = i2c_write(DS2482S_CMD_WRITE_CONFIG) == 0;
	if (retval) {
		retval = i2c_write(rconfig) == 0;
	}
	if (retval) {
		retval = i2c_rep_start(ds2482s_twi_address+I2C_READ) == 0;
	}
	if(retval) {
		nconfig = i2c_readNak();
	}
	i2c_stop();
	//TODO: Verify write
	if(retval && config == nconfig) {
		return true;
	}
	return retval;
}

/** Set active channel. */
bool ds2482s_set_channel(uint8_t channel) {
	uint8_t readcheck=0;
	bool retval;
#ifdef DEBUG
	fprintf(stderr, "D: ds2482_set_channel\n");
#endif
	if(channel > 7) {
#ifdef DEBUG
		fprintf(stderr, "D: illegal channel\n");
#endif
		return false;
	}
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);
	retval = i2c_write(DS2482S_CMD_CHANNEL) ==0;
	if (retval) {
		retval = i2c_write(ds2482s_channels[2*channel]) ==0;
	}
	if(retval) {
		retval = i2c_rep_start(ds2482s_twi_address+I2C_READ) == 0;
	}

	readcheck = i2c_readNak();
	i2c_stop();
	if(retval && readcheck == ds2482s_channels[channel*2+1]) {
		return true;
	} else {
#ifdef DEBUG
		fprintf(stderr, "D: error in channel check %#x != %#x\n", readcheck, ds2482s_channels[channel*2+1]);
#endif
		return false;
	}
}

/** Read byte. Must reset/check TWI last error to see if successful. */
uint8_t ds2482s_read_byte() {
	uint8_t retval;
#ifdef DEBUG
	fprintf(stderr, "D: ds2472s_read_byte\n");
#endif
	i2c_start_wait(ds2482s_twi_address+I2C_READ);
	retval = i2c_readNak();
	i2c_stop();
	return retval;
}

/** Reset 1wire devices on channel. */
bool ds2482s_1wire_reset() {
	bool retval;
	uint8_t status;
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);
	retval = i2c_write(DS2482S_CMD_1WIRE_RESET) ==0;
	if(retval) {
		ds2482s_1wire_wait();
	}
	i2c_rep_start(ds2482s_twi_address+I2C_READ);
	status = i2c_readNak();
	i2c_stop();
	if(!(status & 0x02)) {
		return false;
	}
	return retval;
}

/** Write bit to 1wire device. */
bool ds2482s_1wire_write_bit(bool high) {
	bool retval;
	uint8_t bit_byte;
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);
	retval = i2c_write(DS2482S_CMD_WRITE_1WIRE_BIT) == 0;
	if(retval) {
		if (high) { 
			bit_byte = 0xFF;
		} else {
			bit_byte = 0x7F;
		}
		retval = i2c_write(bit_byte) == 0;
	}
	if(retval) {
		ds2482s_1wire_wait();
	}
	i2c_stop();
	return retval;
}

/** Wait for 1 wire to be idle, does not stop i2c */
void ds2482s_1wire_wait(void) {
	uint8_t status;
	i2c_rep_start(ds2482s_twi_address+I2C_READ);
	status = i2c_readAck();
	while((status & DS2482_STATUS_1WB)) {
		status = i2c_readAck();
	}
	i2c_readNak();
}

/** Write byte to 1wire device. */
bool ds2482s_1wire_write_byte(uint8_t byte) {
	bool retval;
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);
	retval = i2c_write(DS2482S_CMD_WRITE_1WIRE_BYTE) == 0;
	if(retval) {
		retval = i2c_write(byte) ==0;
	}
	if(retval) {
		ds2482s_1wire_wait();
	}
	i2c_stop();
	return retval;
}

/** Write 64 bits to 1wire device. */
bool ds2482s_1wire_write_64bit(uint8_t* data_buffer) {
	uint8_t i;
	for(i = 0; i < 8; i++) {
		if(!ds2482s_1wire_write_byte( data_buffer[i] )) {
			return false;
		}
	}
	return true;
}

bool ds2482s_1wire_read_64bit(uint8_t* fill_buffer) {
	uint8_t i;
	for(i = 0; i < 8; i++) {
		fill_buffer[i] = ds2482s_1wire_read_byte();
#ifdef DEBUG
		fprintf(stderr, "D: r64 %d - %d\n", i, fill_buffer[i]);
#endif
	}
	return true;
}

/** Sends command to read Read byte from 1wire device. Then reads it from ds2482s. */
uint8_t ds2482s_1wire_read_byte() {
	uint8_t retval;
	//TODO: Set error
	i2c_start_wait(ds2482s_twi_address+I2C_WRITE);
	if(i2c_write(DS2482S_CMD_READ_1WIRE_BYTE) != 0) {
#ifdef DEBUG
		fprintf(stderr, "D: 1wrb - 1\n");
#endif
		i2c_stop();
		return 0;
	}
	ds2482s_1wire_wait();
	if(i2c_rep_start(ds2482s_twi_address+I2C_WRITE) !=0) {
#ifdef DEBUG
		fprintf(stderr, "D: 1wrb - 2\n");
#endif
		i2c_stop();
		return 0;
	}
	if(i2c_write(DS2482S_CMD_RPOINTER) != 0) {
#ifdef DEBUG
		fprintf(stderr, "D: 1wrb - 3\n");
#endif
		i2c_stop();
		return 0;
	}
	if(i2c_write(DS2482S_RPOINTER_DATA) != 0) {
#ifdef DEBUG
		fprintf(stderr, "D: 1wrb - 4\n");
#endif
		i2c_stop();
		return 0;
	}
	if(i2c_rep_start(ds2482s_twi_address+I2C_READ) != 0) {
#ifdef DEBUG
		fprintf(stderr, "D: 1wrb - 5\n");
#endif
		i2c_stop();
		return 0;
	}
	retval = i2c_readNak();
	i2c_stop();
	return retval;
}

bool ds2482s_1wire_readrom(uint8_t* address_buffer) {
	bool retval;
	uint8_t crc = 0, i;
	retval = ds2482s_1wire_reset();
	if (retval) {
		retval = ds2482s_1wire_write_byte(OWIRE_CMD_READROM);
	}
	if (retval) {
		retval = ds2482s_1wire_read_64bit(address_buffer);
	}
	ds2482s_1wire_reset();

	for (i = 0; i < 7; i++) {
		crc = _crc_ibutton_update(crc, address_buffer[i]);
	}

	if (crc != address_buffer[7]) {
#ifdef DEBUG
		fprintf(stderr, "D: read rom bad crc.\n");
#endif
		return false;
	}
	return retval;
}

// Modified from Maxim app note AN3684
// http://www.maximintegrated.com/app-notes/index.mvp/id/3684

// Search state
uint8_t ROM_NO[8];
uint8_t LastDiscrepancy;
uint8_t LastFamilyDiscrepancy;
bool LastDeviceFlag;
uint8_t ds2482s_search_triplet(uint8_t search_direction);

// Copies last found rom into buffer
void ds2482s_rom_search_copy(uint8_t* address) 
{
	uint8_t i;
	for(i = 0; i < 8; i++) {
		address[i] = ROM_NO[i];
	}
}

//--------------------------------------------------------------------------
// Resets rom search
void ds2482s_rom_search_reset(void)
{
	// reset the search state
	LastDiscrepancy = 0;
	LastDeviceFlag = false;
	LastFamilyDiscrepancy = 0;
}

//--------------------------------------------------------------------------
// The 'ds2482s_rom_search' function does a general search. This function
// continues from the previous search state. The search state
// can be reset by using the 'OWFirst' function.
// This function contains one parameter 'alarm_only'.
// When 'alarm_only' is true (1) the find alarm command
// 0xEC is sent instead of the normal search command 0xF0.
// Using the find alarm command 0xEC will limit the search to only
// 1-Wire devices that are in an 'alarm' state.
//
// Returns:   true (1) : when a 1-Wire device was found and its
//                       Serial Number placed in the global ROM
//            false (0): when no new device was found.  Either the
//                       last search was the last device or there
//                       are no devices on the 1-Wire Net.
//
bool ds2482s_rom_search(void)
{
	uint8_t i, id_bit_number;
	uint8_t last_zero, rom_byte_number;
	bool search_result;
	uint8_t id_bit, cmp_id_bit;
	uint8_t rom_byte_mask, search_direction, status, crc;

	// initialize for search
	id_bit_number = 1;
	last_zero = 0;
	rom_byte_number = 0;
	rom_byte_mask = 1;
	search_result = false;

	// if the last call was not the last one
	if (!LastDeviceFlag)
	{
		// 1-Wire reset
		if (!ds2482s_1wire_reset())
		{
			// reset the search
			LastDiscrepancy = 0;
			LastDeviceFlag = false;
			LastFamilyDiscrepancy = 0;
			return false;
		}

		// issue the search command
		ds2482s_1wire_write_byte(0xF0);

		// loop to do the search
		do
		{
			// if this discrepancy if before the Last Discrepancy
			// on a previous next then pick the same as last time
			if (id_bit_number < LastDiscrepancy)
			{
				if ((ROM_NO[rom_byte_number] & rom_byte_mask) > 0)
					search_direction = 1;
				else
					search_direction = 0;
			}
			else
			{
				// if equal to last pick 1, if not then pick 0
				if (id_bit_number == LastDiscrepancy)
					search_direction = 1;
				else
					search_direction = 0;
			}

			// Perform a triple operation on the DS2482 which will perform
			// 2 read bits and 1 write bit
			status = ds2482s_search_triplet(search_direction);

			// check bit results in status byte
			id_bit = ((status & DS2482_STATUS_SBR) == DS2482_STATUS_SBR);
			cmp_id_bit = ((status & DS2482_STATUS_TSB) == DS2482_STATUS_TSB);
			search_direction =
				((status & DS2482_STATUS_DIR) == DS2482_STATUS_DIR) ? (uint8_t)1 : (uint8_t)0;

			// check for no devices on 1-Wire
			if ((id_bit) && (cmp_id_bit))
				break;
			else
			{
				if ((!id_bit) && (!cmp_id_bit) && (search_direction == 0))
				{
					last_zero = id_bit_number;

					// check for Last discrepancy in family
					if (last_zero < 9)
						LastFamilyDiscrepancy = last_zero;
				}

				// set or clear the bit in the ROM byte rom_byte_number
				// with mask rom_byte_mask
				if (search_direction == 1)
					ROM_NO[rom_byte_number] |= rom_byte_mask;
				else
					ROM_NO[rom_byte_number] &= (uint8_t)~rom_byte_mask;

				// increment the byte counter id_bit_number
				// and shift the mask rom_byte_mask
				id_bit_number++;
				rom_byte_mask <<= 1;

				// if the mask is 0 then go to new SerialNum byte rom_byte_number
				// and reset mask
				if (rom_byte_mask == 0)
				{
					rom_byte_number++;
					rom_byte_mask = 1;
				}
			}
		}
		while(rom_byte_number < 8);  // loop until through all ROM bytes 0-7

		// if the search was successful then
		if (!(id_bit_number < 65)) {
			// search successful so set LastDiscrepancy,LastDeviceFlag
			// search_result
			LastDiscrepancy = last_zero;

			// check for last device
			if (LastDiscrepancy == 0)
				LastDeviceFlag = true;

			search_result = true;
		
			crc = 0;
			for (i = 0; i < 7; i++) {
				crc = _crc_ibutton_update(crc, ROM_NO[i]);
			}
			if (crc != ROM_NO[7]) {
				return false;
			}
		}
	}

	// if no device found then reset counters so next
	// 'search' will be like a first

	if (!search_result || (ROM_NO[0] == 0))
	{
		LastDiscrepancy = 0;
		LastDeviceFlag = false;
		LastFamilyDiscrepancy = 0;
		search_result = false;
	}

	return search_result;
}

//--------------------------------------------------------------------------
// Use the DS2482 help command '1-Wire triplet' to perform one bit of a
//1-Wire search.
//This command does two read bits and one write bit. The write bit
// is either the default direction (all device have same bit) or in case of
// a discrepancy, the 'search_direction' parameter is used.
//
// Returns ? The DS2482 status byte result from the triplet command
//
uint8_t ds2482s_search_triplet(uint8_t search_direction)
{
	uint8_t status;

	// 1-Wire Triplet (Case B)
	//   S AD,0 [A] 1WT [A] SS [A] Sr AD,1 [A] [Status] A [Status] A\ P
	//                                         \--------/
	//                           Repeat until 1WB bit has changed to 0
	//  [] indicates from slave
	//  SS indicates byte containing search direction bit value in msbit

	i2c_start_wait(ds2482s_twi_address | I2C_WRITE);
	i2c_write(DS2482S_CMD_1WIRE_TRIPLET);
	i2c_write(search_direction ? 0x80 : 0x00);
	i2c_rep_start(ds2482s_twi_address | I2C_READ);

	// loop checking 1WB bit for completion of 1-Wire operation
	// abort if poll limit reached
	status = i2c_readAck();
	do
	{
		status = i2c_readAck();
	}
	while ((status & DS2482_STATUS_1WB));
	i2c_readNak();
	i2c_stop();

	// return status byte
	return status;
}

