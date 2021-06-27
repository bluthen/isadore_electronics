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
//UNITADDR and UNITFEATURES needs to be defined for each unit on compile/load
#define BAUD 9600

#include <stdbool.h>
#include <stdio.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/wdt.h>
#include <avr/eeprom.h>
#include <util/delay.h>
#include <util/setbaud.h>
#include <util/crc16.h>

#ifdef MODULE_TH
#include "./modules/sht75.h"
#endif

#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B) || defined(MODULE_MULTITEMP)
#include "i2cmaster/i2cmaster.h"
#endif

#if defined(MODULE_ANEMOMETER) || defined(MODULE_PRESSUREV1) || defined(MODULE_PRESSUREV5)
#include "adc.h"
#endif

#if defined(MODULE_ANEMOMETER)
#include "anemometer/anemometer.h"
#endif

#if defined(MODULE_ANEMOMETERV2)
#include "anemometerv2/anemometer.h"
#endif

#if defined(MODULE_PRESSUREV1)
#include "pressurev1/pressurev1.h"
#endif

#if defined(MODULE_PRESSUREV5)
#include "pressurev5/pressurev5.h"
#endif

#ifdef MODULE_MULTITEMP
#include "multitemp/multitemp.h"
#endif

#ifdef MODULE_PRESSUREV4A
#include "pressurev4a/pressure.h"
#endif

#ifdef MODULE_PRESSUREV4B
#include "pressurev4b/pressure.h"
#endif

#ifdef MODULE_TACHOMETER
#include "./modules/tachometer.h"
#endif

#ifdef MODULE_THERMOCOUPLE
#include "./modules/thermocouplev2/thermocouple.h"
#endif

//#define DEBUG

#ifdef DEBUG
#include "softuart.h"
#endif

#define MAGIC0 'D'
#define MAGIC1 'E'
#define MAGIC2 'R'
#define MAGIC3 'V'
#define MAGIC_SIZE 4
#define MAX_TXBUF_LEN 17 //MAGIC_SIZE + Addr(2)+cc(1)+s(1)+max_s_value(8)+crc(1)

#define RS485RE PB0
#define RS485REPORT PORTB
#define RS485REDDR DDRB
#define RS485DE PD4
#define RS485DEPORT PORTD
#define RS485DEDDR DDRD

//Command codes
#define CC_TEMP_HUM 1
#define CC_ANEMOMETER 2
#define CC_TACHOMETER 3
#define CC_THERMOCOUPLE 6
#define CC_PRESSURE 7
#define CC_PRESSURE_WIDE 8
#define CC_PRESSURE_WIDE_CALSIZE 4
#define CC_PRESSURE_DIFF_WIDE 14
#define CC_MULTITEMP_RESET 9
#define CC_MULTITEMP_CH1 10
#define CC_MULTITEMP_CH2 11
#define CC_MULTITEMP_CH3 12
#define CC_MULTITEMP_CH4 13
#define CC_MULTITEMP_ADDR_CH1 14
#define CC_MULTITEMP_ADDR_CH2 15
#define CC_MULTITEMP_ADDR_CH3 16
#define CC_MULTITEMP_ADDR_CH4 17
//#define CC_MULTITEMP
#define CC_UNIT_VERSION 63
#define CC_CAL_GET 64
#define CC_CAL_SET 65
#define CC_CHANGE_ADDRESS 200

#define ADAVG_COUNT 5
#define ADAVG_DELAYMS 50 

#define UNIT_VERSION 3


static void ioinit(void);
static int uart_putchar(char c, FILE *stream);
uint8_t uart_kbhit(void);
static uint8_t uart_getchar(void);
static uint8_t calsize(uint8_t findcc);
void hub_input(uint8_t c);
static bool check_magic(uint8_t c);
static void *mymemcpy(void *dest, const void *src, size_t count);

#ifdef DEBUG
static int swuart_putchar( char c, FILE *stream );
#endif

static FILE mystdout = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);
#ifdef DEBUG
static FILE suart_stream = FDEV_SETUP_STREAM(swuart_putchar, NULL, _FDEV_SETUP_WRITE );
#endif
static uint8_t rxcount=0;
static uint16_t rxaddr=0;
static uint16_t chaddr=0;
static uint8_t cc=0;
static uint8_t cal_cc=0;
static uint8_t cal_val[8];
uint16_t EEMEM ee_addr=UNITADDR;
static uint16_t myaddr=0;
static uint8_t volatile activate=0;
static unsigned char txbuffer[MAX_TXBUF_LEN];

int main(void)
{
	uint8_t crc = 0, i=0, ch = 0;
	uint8_t s = 0;
	uint16_t t=0, h=0;
	uint32_t t2=0;
	uint32_t pres=0;
	int32_t it2=0;
	uint8_t t8[8];
	double convert=0.0,convert2=0.0;
	myaddr = eeprom_read_word(&ee_addr);
	ioinit();
	//TXBUFFER=Magic(4b),Address(2b),CC(1b),S(1b),Data(Sb),CRC8(1b)
	txbuffer[0]=MAGIC0;
	txbuffer[1]=MAGIC1;
	txbuffer[2]=MAGIC2;
	txbuffer[3]=MAGIC3;
	mymemcpy(&txbuffer[MAGIC_SIZE], &myaddr, 2);
#ifdef DEBUG
			fprintf(stderr, "D: Unit addr=%d.\r\n", myaddr);
#endif
	while(1)
	{
		if(activate)
		{
#ifdef DEBUG
			//fprintf(stderr, "D: go\r\n");
#endif
			activate = 0;
			txbuffer[MAGIC_SIZE+2]=cc;
			if(cc == CC_UNIT_VERSION) {
				s = 2;
				txbuffer[MAGIC_SIZE+3]=s;
				t = UNIT_VERSION;
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
			}
#ifdef MODULE_TH
			else if(cc == CC_TEMP_HUM)
			{
				s = 4;
				txbuffer[MAGIC_SIZE+3]=s; //S
				t = sht_read_raw_temperature();
				h = sht_read_raw_humidity();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
				mymemcpy(&txbuffer[MAGIC_SIZE+6], &h, 2);
			} 
#endif
#if defined(MODULE_ANEMOMETER) || defined(MODULE_ANEMOMETERV2)
			else if (cc == CC_ANEMOMETER)
			{
				s=2;
				txbuffer[MAGIC_SIZE+3]=s; //S
				//Get wind speed reading.
				t=anemometer_mph();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
			}
#endif
#ifdef MODULE_PRESSUREV4A
			else if (cc == CC_PRESSURE)
			{
				s=2;
				txbuffer[MAGIC_SIZE+3]=s; //S
				//Get pressure.
				t=pressure_get();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
			}
			else if (cc == CC_PRESSURE_WIDE)
			{
				s=4;
				txbuffer[MAGIC_SIZE+3]=s; //S
				//Get full pressure.
				t2=pressure_get_full();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t2, 4);
			}
#endif
#ifdef MODULE_PRESSUREV4B
			else if(cc == CC_TEMP_HUM)
			{
				s = 4;
				txbuffer[MAGIC_SIZE+3]=s; //S
				pressure_temp_rh_get_full(&pres, &it2, &t2);
				t = t_to_shtt(it2);
				h = (uint16_t)(t2);
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
				mymemcpy(&txbuffer[MAGIC_SIZE+6], &h, 2);
			} 
			else if (cc == CC_PRESSURE)
			{
				s=2;
				txbuffer[MAGIC_SIZE+3]=s; //S
				//Get pressure.
				t=pressure_get();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
			}
			else if (cc == CC_PRESSURE_WIDE)
			{
				s=4;
				txbuffer[MAGIC_SIZE+3]=s; //S
				//Get full pressure.
				t2=pressure_get_full();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t2, 4);
			}
#endif
#ifdef MODULE_PRESSUREV1
			else if (cc == CC_PRESSURE)
			{
				s=2;
				txbuffer[MAGIC_SIZE+3]=s; //S
				t=pressurev1_get();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
			}
			else if (cc == CC_PRESSURE_WIDE)
			{
				s=4;
				txbuffer[MAGIC_SIZE+3]=s; //S
				t2=pressurev1_get_wide();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t2, 4);
			}
#endif
#ifdef MODULE_PRESSUREV5
			else if (cc == CC_PRESSURE_DIFF_WIDE)
			{
				s=4;
				txbuffer[MAGIC_SIZE+3]=s; //S
				t2=pressurev5_get_wide();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t2, 4);
			}
#endif
#ifdef MODULE_MULTITEMP
			else if (cc == CC_MULTITEMP_RESET) 
			{
				multitemp_reset();
				s = 1;
				txbuffer[MAGIC_SIZE+3]=s; //S
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &s, 1);
			}
			else if (cc >= CC_MULTITEMP_CH1 && cc <= CC_MULTITEMP_CH4)
			{
				s=2;
				txbuffer[MAGIC_SIZE+3]=s; //S
				ch = cc - CC_MULTITEMP_CH1 + 1;
				t = multitemp_get(ch);
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
			}
			else if (cc >= CC_MULTITEMP_ADDR_CH1 && cc <= CC_MULTITEMP_ADDR_CH4)
			{
				s=8;
				txbuffer[MAGIC_SIZE+3]=s; //S
				ch = cc - CC_MULTITEMP_ADDR_CH1 + 1;
				multitemp_get_addr(ch, t8);
				mymemcpy(&txbuffer[MAGIC_SIZE+4], t8, 8);
			}
#endif
#ifdef MODULE_THERMOCOUPLE
			else if (cc == CC_THERMOCOUPLE) {
				s = 4;
				txbuffer[MAGIC_SIZE+3]=s; //S
				t = thermocouple_read();
				h = 0;
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
				mymemcpy(&txbuffer[MAGIC_SIZE+6], &h, 2);
			}
#endif
#ifdef MODULE_TACHOMETER
			else if (cc == CC_TACHOMETER) {
				s=2;
				txbuffer[MAGIC_SIZE+3]=s; //S
				t=tachometer_rpm();
				mymemcpy(&txbuffer[MAGIC_SIZE+4], &t, 2);
			}
#endif
			else if (cc == CC_CAL_GET && (false
#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B)
				|| cal_cc == CC_PRESSURE_WIDE
#endif
				)
			) {
				if(false) {
				}
#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B)
				else if(cal_cc == CC_PRESSURE_WIDE) {
					s=sizeof(it2);
					txbuffer[MAGIC_SIZE+3]=s; //S
					it2 = pressure_get_cal();
					mymemcpy(&txbuffer[MAGIC_SIZE+4], &it2, sizeof(it2));
				}
#endif
			}
			else if (cc == CC_CAL_SET && (false 
#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B)
				|| cal_cc == CC_PRESSURE_WIDE
#endif
				)
			) {
				if(false) {
				}
#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B)
				else if(cal_cc == CC_PRESSURE_WIDE) {
					it2=0;
					for(i = 0; i < 4; i++) {
#ifdef DEBUG
			fprintf(stderr, "D: cal_val=%d.\r\n", cal_val[i]);
#endif
						it2+=(uint32_t)cal_val[i] << (i*8);
					}
					pressure_set_cal(it2);
					s=sizeof(it2);
					txbuffer[MAGIC_SIZE+3]=s; //S
					it2 = pressure_get_cal();
					mymemcpy(&txbuffer[MAGIC_SIZE+4], &it2, sizeof(it2));
				}
#endif
			}
			else
			{
				s=0;
				txbuffer[MAGIC_SIZE+3]=s; // S
				//Not a feature supported 0 data.
			}

			//calculate crc
#ifdef DEBUG
			//fprintf(stderr, "D: crc\r\n");
#endif
			wdt_reset();
			crc=0;
			for( i = 0; i < (MAGIC_SIZE+4+s); i++)
			{
				crc = _crc_ibutton_update(crc, txbuffer[i]);
			}
			txbuffer[MAGIC_SIZE+4+s] = crc;
			RS485DEPORT |=_BV(RS485DE); //set data out enabled

			fwrite(txbuffer, MAGIC_SIZE+4+s+1, 1, stdout); //Send data
			UCSR0A|=(1<<TXC0); //Reset TXC0 bit
			loop_until_bit_is_set(UCSR0A, TXC0); //Wait till done transmitting
			RS485DEPORT &= ~_BV(RS485DE); //Turn off data out enable
#ifdef DEBUG
			fprintf(stderr, "D: Sent CRC=0x%x\r\n", crc);
			//fwrite(txbuffer, sizeof(txbuffer), 1, stderr);
#endif
		}
		if(uart_kbhit())
		{
			hub_input(uart_getchar());
		}
		_delay_us(100);
		wdt_reset();
	}
}

uint8_t calsize(uint8_t findcc) {
#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B)
	if(findcc == CC_PRESSURE_WIDE) {
		return CC_PRESSURE_WIDE_CALSIZE;
	}
#endif
	return 0;
}

//Input from RX USART
void hub_input(uint8_t c)
{
	if(rxcount < MAGIC_SIZE && check_magic(c))
	{
		rxcount++;
		return;
	}
	else if(rxcount < MAGIC_SIZE && rxcount != 0)
	{
		rxcount = 0;
		hub_input(c);
		return;
	}
	if(rxcount >= MAGIC_SIZE )
	{
		if(rxcount == MAGIC_SIZE)
		{
			rxaddr=c;
			rxcount++;
		}
		else if(rxcount == MAGIC_SIZE+1)
		{
			rxaddr+= c << 8;
			rxcount++;
		}
		else if(rxcount == MAGIC_SIZE+2)
		{
			cc=c;
			if ( (cc == CC_CHANGE_ADDRESS && rxaddr == 0 ) || 
			     (rxaddr == myaddr && (cc == CC_CAL_SET || cc == CC_CAL_GET)) )
			{
				rxcount++;
			}
			else
			{
				rxcount = 0;
				if(rxaddr == myaddr)
				{
					activate=1;
				}
			}
		}
		else if(cc == CC_CAL_GET && rxcount == MAGIC_SIZE+3) 
		{
			cal_cc = c;
			if(calsize(cal_cc) != 0) {
				rxcount = 0;
				activate = 1;
			} else {
				rxcount = 0;
			}
		}
		else if(cc == CC_CAL_SET)
		{
			if(rxcount == MAGIC_SIZE+3)
			{
				cal_cc = c;
				rxcount++;
			} else if(rxcount <= MAGIC_SIZE+3+calsize(cal_cc)) {
				cal_val[rxcount-(MAGIC_SIZE+4)] = c;
				rxcount++;
				if(rxcount-(MAGIC_SIZE+4) == calsize(cal_cc)) {
					rxcount = 0;
					activate = 1;
				}
			}
		}
		else if(cc == CC_CHANGE_ADDRESS)
		{
			if(rxcount == MAGIC_SIZE+3)
			{
				chaddr = c;
				rxcount++;
			}
			else if(rxcount == MAGIC_SIZE+4)
			{
				chaddr+= c<<8;
				eeprom_write_word(&ee_addr, chaddr);
				myaddr = chaddr;
				mymemcpy(&txbuffer[MAGIC_SIZE], &myaddr, 2);
				rxcount = 0;
			}
		}
	}
}

/*
 * Keeps track if magic bytes were sent
 * return true if we recieved all magic bytes.
 */
bool check_magic(uint8_t c)
{
	//Change if MAGIC_SIZE changes
	if((rxcount == 0 && c == MAGIC0) || (rxcount == 1 && c == MAGIC1) ||
			(rxcount == 2 && c == MAGIC2) || (rxcount == 3 && c == MAGIC3) )
	{
		return true;
	}
	return false;
}

void ioinit(void)
{
#ifdef DEBUG
	softuart_init();
#endif
	wdt_enable(WDTO_8S);
	wdt_reset();
	sei(); //enable interupts
	DDRD &=~_BV(PD0); // read on usart RX pin
	DDRD |=_BV(PD1); // output on usart TX pin
	UBRR0H = UBRRH_VALUE;
	UBRR0L = UBRRL_VALUE;
	UCSR0B = (1 << RXEN0)|(1<<TXEN0); 
	//UCSR0B = (1 << RXEN0)|(1<<TXEN0)|(1<<TXCIE0); //TX interrupt to clear flag so when know when we are done transmitting.
	stdout = &mystdout;
#ifdef DEBUG
	stderr = &suart_stream;
#endif
	//Make sure RE and DE are outputs
	RS485REDDR |=_BV(RS485RE); // set to output
	RS485REPORT &=~_BV(RS485RE); //low is enable for RE
	RS485DEDDR |=_BV(RS485DE); //set to output
	RS485DEPORT &=~_BV(RS485DE); //DE off low is disable for DE

	_delay_ms(10); //Delay on startup needed for some sensors
#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B) || defined(MODULE_MULTITEMP)
	i2c_init();
#endif
#ifdef MODULE_MULTITEMP
	multitemp_init();
#endif
#if defined(MODULE_PRESSUREV4A) || defined(MODULE_PRESSUREV4B)
	pressure_init();
#endif

#ifdef MODULE_TH
	sht_init();
#endif
#if defined(MODULE_PRESSUREV1) || defined(MODULE_PRESSUREV5)
	//Enable ADC, 32 clock prescale for ADC clock of 4Mhz/16=125kHz
	//ADC clock needs to be between 50kHz-200kHz
	ADCSRA=0xC5; // ADC 128 clock prescaller
#endif
#if defined(MODULE_ANEMOMETER) || defined(MODULE_ANEMOMETERV2)
	anemometer_ioinit();
#endif
#ifdef MODULE_TACHOMETER
	tachometer_ioinit();
#endif
#ifdef MODULE_THERMOCOUPLE
	//SPI
	thermocouple_init();
	SPI_DDR |= (1<<SPI_SCK); //Output on SCK
	SPI_DDR |= (1<<SPI_MOSI); //Output on MOSI TODO: Is this needed?
	SPI_DDR &= ~(1<<SPI_MISO); //Input on MISO
	// Enable SPI, Master, clock rate fcpu/128
	SPCR = (1<<SPE)|(1<<MSTR)|(1<<SPR1)|(1<<SPR0);
#endif

}


//Simple memcpy implementation
void *mymemcpy(void *dest, const void *src, size_t count)
{
	char *d = (char*) dest;
	char *s = (char*) src;
	while(count--)
	{
		*d++=*s++;
	}
	return dest;
}

/*
 * Get character from serial
 */
uint8_t uart_getchar(void)
{
	while( !(UCSR0A & (1<<RXC0)) );
	return(UDR0);
}


/**
 * Is there a character in buffer?
 */
uint8_t uart_kbhit(void)
{
	return (UCSR0A & (1<<RXC0));
}


/*
 * Send character to serial
 */
static int uart_putchar(char c, FILE *stream)
{
	//if (c == '\n') uart_putchar('\r', stream);

	loop_until_bit_is_set(UCSR0A, UDRE0);
	UDR0 = c;

	return 0;
}

#ifdef DEBUG
// interface between avr-libc stdio and the modified Fleury uart-lib:
static int swuart_putchar( char c, FILE *stream )
{
	if ( c == '\n' ) {
		softuart_putchar( '\r' );
	}
	softuart_putchar( c );

	return 0;
}

#endif
