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
#include <math.h>

#include "pressurev4b/BME280_driver/bme280.h"
#include "pressurev4b/pressure.h"
#include "i2cmaster/i2cmaster.h"


static struct bme280_t bme280;
uint32_t EEMEM ee_adjust_p=CAL_PRESSUREV4B_ADJUST_P;
uint32_t EEMEM ee_adjust_t=CAL_PRESSUREV4B_ADJUST_T;
uint32_t EEMEM ee_adjust_rh=CAL_PRESSUREV4B_ADJUST_RH;
static int32_t adjust_p=0; 
static int32_t adjust_t=0; 
static int32_t adjust_rh=0; 


char BME280_I2C_bus_read(unsigned char device_addr, unsigned char reg_addr, unsigned char *reg_data, unsigned char cnt) {
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

char BME280_I2C_bus_write(unsigned char device_addr, unsigned char reg_addr, unsigned char *reg_data, unsigned char cnt) {
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

void BME280_delay_msek(unsigned int msek) { //delay in milliseconds
	unsigned int i;
	for(i = 0; i < msek; i++) {
		_delay_ms(1);
	}
	_delay_ms(1); // Just in case.
}


unsigned char pressure_init(void) {
	adjust_p = (int32_t)eeprom_read_dword(&ee_adjust_p);
	adjust_t = (int32_t)eeprom_read_dword(&ee_adjust_t);
	adjust_rh = (int32_t)eeprom_read_dword(&ee_adjust_rh);
	
	//Init BME280
	bme280.bus_read = BME280_I2C_bus_read;
	bme280.bus_write = BME280_I2C_bus_write;
	bme280.dev_addr = BME280_I2C_ADDRESS1;
	bme280.delay_msec = BME280_delay_msek;

	bme280_init(&bme280);
	bme280_set_power_mode(BME280_NORMAL_MODE);
	bme280_set_oversamp_humidity(BME280_OVERSAMP_16X);
	bme280_set_oversamp_pressure(BME280_OVERSAMP_16X);
	bme280_set_oversamp_temperature(BME280_OVERSAMP_16X);
	bme280_set_standby_durn(BME280_STANDBY_TIME_1_MS);
	//bme280_set_power_mode(BME280_NORMAL_MODE);

	//if (bme280.chip_id != 0x55) {
		//Did not successfully communicate with pressure chip.
	//}
	return bme280.chip_id;
}

uint32_t humidity_adjust(uint32_t bme280_compensated_hum) {
	bme280_compensated_hum =  (uint32_t)((bme280_compensated_hum * 100)/1024 + adjust_rh);
	return bme280_compensated_hum;
}

void pressure_temp_rh_get_full(uint32_t* pres, int32_t* temp, uint32_t* rh) {
	bme280_read_pressure_temperature_humidity(pres, temp, rh);
	*rh = humidity_adjust(*rh);
	*temp += adjust_t;
	*pres += adjust_p;
}

uint16_t pressure_get(void) {
	int16_t retval;
	uint32_t pres, hum;
	int32_t temp;
	pressure_temp_rh_get_full(&pres, &temp, &hum);
	retval = (((pres-50000)*100)/229);
	return retval;
}

uint32_t pressure_get_full(void) {
	uint32_t pres, hum;
	int32_t temp;
	pressure_temp_rh_get_full(&pres, &temp, &hum);
	return pres;
}

uint16_t t_to_shtt(int32_t t) {
	return (uint16_t)((100*t + 401111 + 50)/100);
}

int32_t pressure_get_cal(void) {
	return adjust_p;
}

void pressure_set_cal(int32_t newcal) {
	eeprom_write_dword(&ee_adjust_p, (uint32_t)newcal);
	adjust_p = (int32_t)eeprom_read_dword(&ee_adjust_p);
}
/*

int32_t temperature_get_cal(void) {
	return adjust_t;
}

void temperature_set_cal(int32_t newcal) {
	eeprom_write_dword(&ee_adjust_t, (uint32_t)newcal);
	adjust_t = (int32_t)eeprom_read_dword(&ee_adjust_t);
}

int32_t humidity_get_cal(void) {
	return adjust_rh;
}

void humidity_set_cal(int32_t newcal) {
	eeprom_write_dword(&ee_adjust_rh, (uint32_t)newcal);
	adjust_rh = (int32_t)eeprom_read_dword(&ee_adjust_rh);
}
*/
