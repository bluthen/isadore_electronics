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
/*
* Reads from humidity temperature sensor SHTxx.
* Datasheet: http://www.sensirion.ch/en/pdf/product_information/Datasheet-humidity-sensor-SHT1x.pdf
*/

#include <avr/io.h>
#include <util/delay.h>
#include "sht75.h"


void sht_init(void)
{
	SHT_DDR |= ( 1<< SHT_SCK);
	SHT_DDR |= (1 << SHT_DATA);
	SHT_DATAPORT&=~(1<<SHT_DATA);
	_delay_ms(50); // wait atleast 11ms for sensor powerup
	sht_conn_reset();
#ifndef SHT_LOWRES
	sht_write_status(0x00);
#else
	sht_write_status(0x01);
#endif	
}

/*
 * Wait for sensor ack
 */
void sht_sensor_ack(void)
{
	if(sht_read_bit())
	{
	}
}

/*
 * Send ack
 */
void sht_send_ack(void)
{
	SHT_DATA_LOW();
	SHT_SCK_HIGH();
	SHT_SCK_DELAY();
	SHT_SCK_LOW();
	SHT_SCK_DELAY();
}

/* 
 * Waits till sensor is ready or timelimit exceeded
 * @return 1 if good 0 if sensor didn't respond to being ready.
 */
uint8_t sht_sensor_ready(void)
{
	//max 320ms for 14 bit
	uint8_t counter=0;
	SHT_DATA_INPUT_MODE();
	while(bit_is_set(SHT_DATAPIN, SHT_DATA))
	{
		//if(counter > 32)
		if(counter > 40) //Max 400ms wait
		{
			return 0;
		}
		_delay_ms(10);
		counter++;
	}
	return 1;
}

/*
 * Get some data from cmd.
 */
uint16_t sht_get_data(uint8_t cmd)
{
	uint16_t data=0xFFFF;
	uint8_t crc = 0xFF;
	sht_transmission_start();
	sht_write_byte(cmd);
	if(sht_sensor_ready())
	{
		data = sht_read_byte16();
		crc = sht_read_byte();
	}
	return data;
}

uint8_t sht_get_data8(uint8_t cmd)
{
	uint8_t data=0xFF;
	uint8_t crc = 0xFF;
	sht_transmission_start();
	sht_write_byte(cmd);
	if(sht_sensor_ready())
	{
		data=sht_read_byte();
		crc=sht_read_byte();
	}
	return data;
}

/* 
 * Reads raw humidity value from sensor
 */
uint16_t sht_read_raw_humidity()
{
	return sht_get_data(SHT_CMD_RELHUM);
}

/*
 * Reads raw temperature value from sensor
 */
uint16_t sht_read_raw_temperature()
{
	return sht_get_data(SHT_CMD_TEMP);
}

uint8_t sht_read_status()
{
	uint8_t status=0;
	status = sht_get_data8(SHT_CMD_READSTATUS);
	return status;
}

void sht_write_status(uint8_t status)
{
	sht_transmission_start();
	sht_write_byte(SHT_CMD_WRITESTATUS);
	sht_write_byte(status);
}

/*
 * Reset connection with sensor
 */
void sht_conn_reset(void)
{
	uint8_t i;
	SHT_DATA_HIGH();
	for(i = 0; i < 12; i++)
	{
		SHT_SCK_HIGH();
		SHT_SCK_DELAY();
		SHT_SCK_LOW();
		SHT_SCK_DELAY();
	}
}

/*
 * Sends sensor start sequence
 *              ____     ____
 * SCK   ______/    \___/    \_____
 *           _____         _____
 * Data  ___/     \_______/     \__
 *
 */
void sht_transmission_start(void)
{
	//XXX: I have more delays than I need
	//Transmission start
	SHT_SCK_LOW();
	SHT_DATA_HIGH();
	SHT_SCK_DELAY();
	SHT_SCK_HIGH();
	SHT_SCK_HDELAY();
	SHT_DATA_LOW();
	SHT_SCK_HDELAY();
	SHT_SCK_LOW();

	SHT_SCK_DELAY();

	SHT_SCK_HIGH();
	SHT_SCK_HDELAY();
	SHT_DATA_HIGH();
	SHT_SCK_HDELAY();
	SHT_SCK_LOW();
	SHT_SCK_DELAY();
	SHT_DATA_LOW();
	SHT_SCK_DELAY();
}

/*
 * Send bit to sensor
 * @param bit 0 or 1
 */
void sht_write_bit(uint8_t bit)
{
	if(bit) 
	{
		SHT_DATA_HIGH();
	}
	else
	{
		SHT_DATA_LOW();
	}
	SHT_SCK_HIGH();
	SHT_SCK_DELAY();
	SHT_SCK_LOW();
	SHT_SCK_DELAY();
}

/*
 * Write byte to sensor.
 * @param byte The byte to send to sensor
 */
void sht_write_byte(uint8_t byte)
{
	uint8_t i;
	for(i=0x80; i > 0; i>>=1)
	{
		sht_write_bit(byte&i);
	}
	sht_sensor_ack();
}


/*
 * Read bit from sensor
 * @return value 0 or 1
 */
uint8_t sht_read_bit(void)
{
	uint8_t bit = 0;
	SHT_DATA_INPUT_MODE();
	SHT_SCK_HIGH();
	SHT_SCK_DELAY();
	if(bit_is_set(SHT_DATAPIN, SHT_DATA)) bit = 1;
	SHT_SCK_LOW();
	SHT_SCK_DELAY();
	return bit;
}

/*
 * Read byte from sensor.
 * @return byte value
 */
uint8_t sht_read_byte(void)
{
	uint8_t i = 0, n =0;
	for(i=0x80; i > 0; i>>=1)
	{
		if(sht_read_bit())
		{
			n|=i;
		}
	}
	sht_send_ack();
	return n;
}

/*
 * Ready two bytes from sensor
 */
uint16_t sht_read_byte16(void)
{
	uint16_t n =0xFFFF;
	n=sht_read_byte();
	n = n << 8;
	n += sht_read_byte();
	return n;
}


