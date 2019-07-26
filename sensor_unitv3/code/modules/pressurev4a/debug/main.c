#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#include <avr/io.h>
#include <avr/wdt.h>
#include <avr/pgmspace.h>
#include <avr/interrupt.h>
#include <util/delay.h>

#include "console.h"
#include "i2cmaster/i2cmaster.h"
#include "pressurev4a/pressure.h"

#define DEBUG

static void ioinit(void);
static void print_help(void);
static void process_command(void);
static void* mymemcpy(void *dest, const void *src, size_t count);
static uint8_t twi_address = 238, channel = 0;

int main(void)
{
	ioinit();
#ifdef DEBUG
	printf("DEBUG: Starting Pressure Console\n");
#endif
	putchar(']');
	for (;;)
	{
		if(console_command_ready()) {
			process_command();
		}
		_delay_us(100);
//		wdt_reset(); //Watchdog timer reset
	}
	return 0;
}

void print_help(void) {
	//Address for DS2482 is:
	printf_P(PSTR("COMMANDS:\n\tset_twi_address {address}\n\tpressure_init\n\tpressure_get\n\tpressure_get_full\n"));
#ifdef DEBUG
	printf_P(PSTR("DEBUG COMMANDS:\n\ttwi_start\n\ttwi_stop\n\treadbyte\n\teewrite {hex16addr} {hexwrite}\n\teeread {hex16addr}\n"));
#endif
}

void process_command(void)
{
	char dsaddress_str[3];
	bool found = false;
	uint16_t temperature = 0;
	uint8_t i, dsaddress[8];

	double t;

#ifdef DEBUG
	uint16_t eeaddr = 0;
	uint8_t eedata = 0;
#endif

	char* console_command = get_console_command();
	console_command_reset();
	printf("\n");
	if(strcmp(console_command, "help") == 0) {
		print_help();
	} else if(strncmp(console_command, "set_twi_address", 15) == 0) {
		twi_address = (uint8_t)strtol(&console_command[16], NULL, 10); 
		//ds2482s_set_twi_address(twi_address);
		printf("TWI address set to: %d\n", twi_address);
#ifdef DEBUG
	} else if(strcmp(console_command, "twi_start") == 0) {
		printf("D: twi_start\n");
		printf("twi_start = %d\n", i2c_start(twi_address+I2C_READ));
	} else if(strcmp(console_command, "pressure_init") == 0) {
		printf("D: pressure_init\n");
		printf("pressure_init = %d\n", pressure_init());
	} else if(strcmp(console_command, "pressure_get") == 0) {
		printf("D: pressure_get\n");
		printf("pressure_get = %d\n", pressure_get());
	} else if(strcmp(console_command, "pressure_get_full") == 0) {
		printf("D: pressure_get_full\n");
		printf("pressure_get_full = %lu\n", pressure_get_full());
	} else if(strcmp(console_command, "twi_stop") == 0) {
		printf("D: twi_stop\n");
		i2c_stop();
	} else if(strcmp(console_command, "readbyte") == 0) {
		printf("D: Reading byte.\n");
		i2c_start_wait(twi_address+I2C_READ);
		printf("readbyte: %d\n", i2c_readNak());
		i2c_stop();
	} else if(strlen(console_command) == 7+8 && strncmp(console_command, "eewrite", 7) == 0) {
		eeaddr=(uint8_t)strtol(&console_command[8], NULL, 16);
		eedata=(uint8_t)strtol(&console_command[13], NULL, 16);
		printf("D: eewrite: eeadr=%#x, eedata=%#x\n", eeaddr, eedata); 
		i2c_start_wait(twi_address+I2C_WRITE);
		i2c_write((uint8_t)(eeaddr >> 8));
		i2c_write((uint8_t)(eeaddr & 0xFF));
		i2c_write(eedata);
		i2c_stop();
	} else if(strlen(console_command) == 6+5 && strncmp(console_command, "eeread", 6) == 0) {
		eeaddr=(uint8_t)strtol(&console_command[8], NULL, 16);
		printf("D: eeread: eeadr=%#x\n", eeaddr); 
		eedata=0;
		i2c_start_wait(twi_address+I2C_WRITE);
		i2c_write((uint8_t)(eeaddr >> 8));
		i2c_write((uint8_t)(eeaddr & 0xFF));
		i2c_rep_start(twi_address+I2C_READ);
		eedata = i2c_readNak();
		i2c_stop();
		printf("eeread, read=%#x\n", eedata);
#endif
	}
	putchar(']');
}

void ioinit(void)
{
	//Turn on watch dog
//	wdt_enable(WDTO_8S);
	DDRD &=~_BV(PD0); //Read on hw rx usart 
	DDRD |= _BV(PD1);

	console_ioinit();
	i2c_init();
	sei();
}

//Simple memcpy implementation
void* mymemcpy(void *dest, const void *src, size_t count)
{
	char *d = (char*) dest;
	char *s = (char*) src;
	while(count--)
	{
		*d++=*s++;
	}
	return dest;
}

