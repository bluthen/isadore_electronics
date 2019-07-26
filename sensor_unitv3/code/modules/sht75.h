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

#ifndef SHT75_H
#define SHT75_H

#include <avr/io.h>
#include <util/delay.h>


//#define DEBUG   //Output debug info to serial
//#define SHT_LOWRES  //if using 8bit/12bit instead of 12bit/14bit
#define SHT_SCK_DELAY() _delay_us(150) // Longer delay for longer cables to sensor
#define SHT_SCK_HDELAY() _delay_us(75)

//Microcontrol pin to sensor SCK
#define SHT_SCK PC0
#define SHT_SCKPORT PORTC
#define SHT_DATA PC1
//Microcontroller pin to sensor DATA
#define SHT_DATAPIN PINC
#define SHT_DATAPORT PORTC
#define SHT_DDR DDRC

#define SHT_DATA_INPUT_MODE()  SHT_DDR&=~(1<<SHT_DATA)
#define SHT_DATA_OUTPUT_MODE() SHT_DDR|=(1<<SHT_DATA)
//Just change modes since we use a pullup resistor
#define SHT_DATA_LOW()         SHT_DATA_OUTPUT_MODE();
#define SHT_DATA_HIGH()        SHT_DATA_INPUT_MODE();

#define SHT_SCK_LOW()       SHT_SCKPORT&=~(1<<SHT_SCK)
#define SHT_SCK_HIGH()      SHT_SCKPORT|=(1<<SHT_SCK)

//Sensor commands
#define SHT_CMD_TEMP 0x03
#define SHT_CMD_RELHUM 0x05
#define SHT_CMD_READSTATUS 0x07
#define SHT_CMD_WRITESTATUS 0x06
#define SHT_CMD_SOFTRESET 0x1E //Wait >=11ms before next command after this one

void sht_init(void);
void sht_sensor_ack(void);
void sht_send_ack(void);
uint8_t sht_sensor_ready(void);
void sht_conn_reset(void);

uint16_t sht_read_raw_humidity(void);
uint16_t sht_read_raw_temperature(void);
void sht_transmission_start(void);
uint8_t sht_read_status(void);
void sht_write_status(uint8_t);

uint16_t sht_get_data(uint8_t cmd);
uint8_t sht_get_data8(uint8_t cmd);
void sht_write_bit(uint8_t bit);
void sht_write_byte(uint8_t byte);
uint8_t sht_read_bit(void);
uint8_t sht_read_byte(void);
uint16_t sht_read_byte16(void);

#endif
