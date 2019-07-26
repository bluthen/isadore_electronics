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
#include <avr/eeprom.h>

#include "pressurev4a/bmp180.h"
#include "pressurev4a/pressure.h"
#include "i2cmaster/i2cmaster.h"


static struct bmp180_t bmp180;
uint32_t EEMEM ee_pressure_adjust=CAL_PRESSUREV4A_ADJUST;
static int32_t pressure_adjust=0; 


char BMP180_I2C_bus_read(unsigned char device_addr, unsigned char reg_addr, unsigned char *reg_data, unsigned char cnt) {
	unsigned char i;
	signed char comres =0;
	i2c_start((device_addr<<1)+I2C_WRITE);
	comres = i2c_write(reg_addr);
	comres += i2c_rep_start((device_addr<<1)+I2C_READ);
	for (i=0; i < cnt; i++) {
		if(i == cnt-1) {
			*(reg_data+i) = i2c_readNak();
		} else {
			*(reg_data+i) = i2c_readAck();
		}
	}
	i2c_stop();
	return comres;
}

char BMP180_I2C_bus_write(unsigned char device_addr, unsigned char reg_addr, unsigned char *reg_data, unsigned char cnt) {
	unsigned char i, c;
	signed char comres;	
	i2c_start((device_addr<<1)+I2C_WRITE);
	comres = i2c_write(reg_addr);
	for(i = 0; i < cnt; i++) {
		c = (*reg_data+i);
		comres+=i2c_write(c);
	}
	i2c_stop();
	return comres;
}

void BMP180_delay_msek(unsigned int msek) { //delay in milliseconds
	unsigned int i;
	for(i = 0; i < msek; i++) {
		_delay_ms(1);
	}
	_delay_ms(1); // Just in case.
}


unsigned char pressure_init(void) {
	pressure_adjust = (int32_t)eeprom_read_dword(&ee_pressure_adjust);
	
	//Init BMP180
	bmp180.bus_read = BMP180_I2C_bus_read;
	bmp180.bus_write = BMP180_I2C_bus_write;
	bmp180.delay_msec = BMP180_delay_msek;

	bmp180_init(&bmp180);

	bmp180.oversampling_setting = 3;
	bmp180.sw_oss = 1;

	//if (bmp180.chip_id != 0x55) {
		//Did not successfully communicate with pressure chip.
	//}
	return bmp180.chip_id;
}

uint16_t pressure_get(void) {
	int32_t p;
	int16_t retval;
	bmp180_get_temperature(bmp180_get_ut());
	p = bmp180_get_pressure(bmp180_get_up()) + pressure_adjust;
	retval = (p-50000.0)/2.2888;
	return retval;
}

uint32_t pressure_get_full(void) {
	int32_t p;
	bmp180_get_temperature(bmp180_get_ut());
	p = bmp180_get_pressure(bmp180_get_up()) + pressure_adjust;
	return p;
}

int32_t pressure_get_cal(void) {
	return pressure_adjust;
}

void pressure_set_cal(int32_t newcal) {
	eeprom_write_dword(&ee_pressure_adjust, (uint32_t)newcal);
	pressure_adjust = (int32_t)eeprom_read_dword(&ee_pressure_adjust);
}

