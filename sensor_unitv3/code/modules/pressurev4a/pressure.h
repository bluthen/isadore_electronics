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
#ifndef __PRESSURE_H
#define __PRESSURE_H


/** Functions for bmp180 code to use. */
char BMP180_I2C_bus_read(unsigned char device_addr, unsigned char reg_addr, unsigned char *reg_data, unsigned char cnt);
char BMP180_I2C_bus_write(unsigned char device_addr, unsigned char reg_addr, unsigned char *reg_data, unsigned char cnt);
void BMP180_delay_msek(unsigned int msek); //delay in milliseconds

/**
 * Initializes i2c hardware and bmp180 code.
 */
unsigned char pressure_init(void);
/**
 * Returns D where pressure in kPa could be calculated as:
 *     P = 0.0022888*D+50
 */
uint16_t pressure_get(void);
/**
 * Returns D where D is in units Pa.
 */
uint32_t pressure_get_full(void);
/**
 * Get current pressure calibration value.
 */
int32_t pressure_get_cal(void);
/**
 * Set pressure calibration value to eeprom.
 */
void pressure_set_cal(int32_t newcal);

#endif
