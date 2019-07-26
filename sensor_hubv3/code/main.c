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

#define BAUD 9600

#include <stdio.h>
#include <stdbool.h>

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <avr/wdt.h>
#include <util/delay.h>
#include <util/setbaud.h>
#include <util/crc16.h>

#include "softuart.h"

#define REPLY_READINGS 1
#define REPLY_EXEC_SUCCESS 2
#define REPLY_PONG 3
#define REPLY_ERROR 4
#define REPLY_VERSION 5
#define REPLY_DONE 170

#define ERROR_BADADDRCOUNT 2
#define ERROR_UNITTIMEOUT 4
#define ERROR_BADCMDCODE 5
#define ERROR_BADCRC 6
#define ERROR_BADUNITRXSIZE 7
#define ERROR_MISSINGFEATURE 10

//Command codes
#define CC_TEMPHUM 1
#define CC_WIND 2
#define CC_TACH 3
#define CC_TTEMP 6
#define CC_PRESSURE 7
#define CC_GUNITREAD 25
#define CC_CALREAD 64
#define CC_CALSET 65
#define CC_CHANGEIP 128
#define CC_CHANGEMAC 129
#define CC_PING 130
#define CC_HUBVERSION 150

//UNIT Sizes for command codes
#define USIZE_TEMPHUM 4
#define USIZE_WIND 2
#define USIZE_TACH 2
#define USIZE_TTEMP 4
#define USIZE_PRESSURE 2

#define USIZE_MAX 8

#define HUB_VERSION 4


//#define DEBUG

#ifdef DEBUG
#define URX_TIMEOUT 40000 // 40000*1us=4s
#define ERX_TIMEOUT 10000 //10000*100us=1s
#else
#define URX_TIMEOUT 40000 // 40000*1us=4s
#define ERX_TIMEOUT 2500 //2500*100us=250ms
#endif

#define MAX_ADDR_COUNT 32 
#define STXBUFSIZE 7 // Standard Unit transmit 4magic+2addr+1cc 
#define GCALTXBUFSIZE 8 // size of get calibration unit transmit 4magic+2addr+1ccA+1ccB
#define SCALTXBUFSIZE_MAX 16 // max size of set calibration unit transmit 4magic+2addr+1ccA+1ccB+8USIZE_MAX
#define MAX_URXBUFSIZE 17   //4magic+2addr+1cc+1s+USIZE_MAX+1crc
#define PREDATA_URXBUFSIZE 8 //No CRC 4 magic + 2 addr+1cc+1s
#define MAX_ADDRS 32
#define MAGIC0 'D'
#define MAGIC1 'E'
#define MAGIC2 'R'
#define MAGIC3 'V'
#define MAGIC_SIZE 4

//RS485 enable pins
//Port 1
#define RSP1RE PC5
#define RSP1REPORT PORTC
#define RSP1REDDR DDRC
#define RSP1DE PC4
#define RSP1DEPORT PORTC
#define RSP1DEDDR DDRC

//Port 2
#define RSP2RE PD2
#define RSP2REPORT PORTD
#define RSP2REDDR DDRD
#define RSP2DE PC3
#define RSP2DEDDR DDRC
#define RSP2DEPORT PORTC

//Port 3
#define RSP3RE PC2
#define RSP3REPORT PORTC
#define RSP3REDDR DDRC
#define RSP3DE PD3
#define RSP3DEPORT PORTD
#define RSP3DEDDR DDRD

//Port 4
#define RSP4RE PC0
#define RSP4REPORT PORTC
#define RSP4REDDR DDRC
#define RSP4DE PC1
#define RSP4DEPORT PORTC
#define RSP4DEDDR DDRC

//Port 5
#define RSP5RE PD7
#define RSP5REPORT PORTD
#define RSP5REDDR DDRD
#define RSP5DE PD6
#define RSP5DEPORT PORTD
#define RSP5DEDDR DDRD

//Port 6
#define RSP6RE PB1
#define RSP6REPORT PORTB
#define RSP6REDDR DDRB
#define RSP6DE PB2
#define RSP6DEPORT PORTB
#define RSP6DEDDR DDRB

static void ioinit(void);
static void* mymemcpy(void *dest, const void *src, size_t count);
static int uart_putchar(char c, FILE *stream);
static uint8_t uart_getchar(void);

static void uart_rxflush(void);
static uint8_t uart_kbhit(void);
static int swuart_putchar( char c, FILE *stream );
static bool check_magic(uint8_t c, uint8_t idx);
static void disable_rsports(void);
static void enable_rsport(uint8_t port);
static bool query_unit(uint16_t addr);
static bool good_crc(uint8_t);
static void get_send_sensor_data(uint8_t);
static void send_errors_data(uint8_t errors[], uint16_t errors_size, uint8_t data[], uint16_t data_size);
static void send_error_reply_only(uint8_t code, uint8_t addrIdx);
static void eth_input(uint8_t c);
static void unit_input(uint8_t c, uint16_t addr);
static void send_pong(uint16_t ping);
static void send_version(void);

static FILE mystdout = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);
static FILE suart_stream = FDEV_SETUP_STREAM(swuart_putchar, NULL, _FDEV_SETUP_WRITE );

//Variable for recieving data from unit
static uint8_t volatile urxbuffer[MAX_URXBUFSIZE];
static uint8_t volatile urxidx=0;
static bool volatile urxdone=false;

//Variables from recieving data from ethernet board
static uint8_t volatile cmd_code; //Command code
static uint8_t volatile cmd_codep; //Unit command code for batched commands.
static uint8_t volatile cmd_codeo; //Original command code for batched commands.
static uint8_t volatile cmd_size;
static uint8_t volatile cmd_port;
static uint16_t volatile cmd_addrs[MAX_ADDRS];
static uint8_t volatile cmd_cal_set[USIZE_MAX];
static uint8_t volatile cmd_cal_setcount=0;
static uint8_t volatile erxcount=0;
static uint16_t volatile erxtimeout=0;
static uint8_t volatile erxaddrcount=0;
static bool volatile activate=false;


int main(void)
{
	ioinit();
#ifdef DEBUG
	printf("DEBUG: Starting hub\r\n");
#endif
	for (;;)
	{
		if(activate)
		{
			//XXX: Check cmd_port for other commands besides 1-4
			//DEBUG:
#ifdef DEBUG
			printf("DEBUG: Got activate\r\n");
#endif
			if(cmd_code == CC_TEMPHUM)
			{
				cmd_size = USIZE_TEMPHUM;
				get_send_sensor_data(USIZE_TEMPHUM); 
			} 
			else if(cmd_code == CC_WIND)
			{
				cmd_size = USIZE_WIND;
				get_send_sensor_data(USIZE_WIND); 
			}
			else if(cmd_code == CC_TACH)
			{
				cmd_size = USIZE_TACH;
				get_send_sensor_data(USIZE_TACH); 
			}
			else if(cmd_code == CC_TTEMP)
			{
				cmd_size = USIZE_TTEMP;
				get_send_sensor_data(USIZE_TTEMP); 
			}
			else if(cmd_code == CC_PRESSURE)
			{
				cmd_size = USIZE_PRESSURE;
				get_send_sensor_data(USIZE_PRESSURE); 
			}
			else if(cmd_code == CC_PING)
			{
				send_pong(cmd_addrs[0]);
			} 
			else if(cmd_code == CC_HUBVERSION) {
				send_version();
			}
			else if(cmd_code == CC_GUNITREAD || cmd_code == CC_CALREAD || cmd_code == CC_CALSET)
			{
				cmd_code = cmd_codep;
				get_send_sensor_data(cmd_size);
			}
			else
			{

#ifdef DEBUG
				printf("DEBUG: Got bad command code.\r\n");
#endif
				send_error_reply_only(ERROR_BADCMDCODE, 0);
				erxcount=0;
			}
			activate=false;
		}
		if(erxcount >= MAGIC_SIZE && erxtimeout > ERX_TIMEOUT) //If we got magic but they never finished
		{
#ifdef DEBUG
			printf("DEBUG: Got timeout after magic, erxcount=%d.\r\n", erxcount);
#endif
			send_error_reply_only(ERROR_BADADDRCOUNT, 0);
			erxcount=0;
		}
		if(uart_kbhit())
		{
			eth_input(uart_getchar());
		}
		_delay_us(100);
		wdt_reset(); //Watchdog timer reset
		erxtimeout++;
	}
	return 0;
}

/*
 * Ask a unit for it's data.
 */
bool query_unit(uint16_t addr)
{
	uint8_t stxbuffer[SCALTXBUFSIZE_MAX];
	uint8_t bufsize = STXBUFSIZE;
	uint16_t timeout=0;
#ifdef DEBUG
	printf("DEBUG: Querying addr: %d, cmd_code: %d\r\n", addr, cmd_code);
#endif

	stxbuffer[0]=MAGIC0;
	stxbuffer[1]=MAGIC1;
	stxbuffer[2]=MAGIC2;
	stxbuffer[3]=MAGIC3;
	mymemcpy(&stxbuffer[MAGIC_SIZE], &addr, 2); //Copy i'th address to buffer
	if(cmd_codeo == CC_CALREAD) {
		stxbuffer[6]=cmd_codeo;
		stxbuffer[7]=cmd_code;
		bufsize = GCALTXBUFSIZE;
	} else if(cmd_codeo == CC_CALSET) {
		stxbuffer[6]=cmd_codeo;
		stxbuffer[7]=cmd_code;
		mymemcpy(&stxbuffer[8], (void*)&cmd_cal_set[0], cmd_size);
		bufsize = GCALTXBUFSIZE+cmd_size;
	} else {
		stxbuffer[6]=cmd_code;
		bufsize = STXBUFSIZE;
	}

	//Reset Unit RX variables
	urxdone=false;
	urxidx=0;
	softuart_flush_input_buffer(); //Flush recieve buffer.
	_delay_ms(1);

	fwrite(stxbuffer, bufsize, 1, stderr); //Send request to sensor unit
	while(timeout < URX_TIMEOUT && !urxdone)
	{
		if(softuart_kbhit())
		{
			unit_input(softuart_getchar(), addr);
		}
		_delay_us(100);
		timeout++;
	}

	if(!urxdone)
	{
#ifdef DEBUG
		printf("DEBUG: Unit timedout, idx=%d\r\n", urxidx);
		//fwrite(urxbuffer, urxidx-1, 1, stdout);
#endif
		return false;
	}
	return true;
}

bool good_crc(uint8_t data_size)
{
	uint8_t gcrc=urxbuffer[PREDATA_URXBUFSIZE+data_size];
	uint8_t crc=0;
	uint8_t p=0;

	for( p = 0; p < PREDATA_URXBUFSIZE+data_size; p++)
	{
		crc = _crc_ibutton_update(crc, urxbuffer[p]);
	}
	if(crc != gcrc)
	{
#ifdef DEBUG
		printf("DEBUG: calc_crc=%d, urcr=%d\r\n", crc, gcrc);
#endif
		return false;
	}
	return true;
}

void send_pong(uint16_t ping)
{
	uint8_t txbuffer[3];


#ifdef DEBUG
	printf("DEBUG: send_pong called\r\n");
#endif

	txbuffer[0]=REPLY_PONG;
	ping++;
	mymemcpy(&txbuffer[1], &ping, 2);
	send_errors_data(0, 0, txbuffer, sizeof(txbuffer));
}

void send_version()
{
	uint8_t txbuffer[3];
	uint16_t version = HUB_VERSION;


#ifdef DEBUG
	printf("DEBUG: send_version called\r\n");
#endif

	txbuffer[0]=REPLY_VERSION;
	mymemcpy(&txbuffer[1], &version, 2);
	send_errors_data(0, 0, txbuffer, sizeof(txbuffer));
}



/*
 * Get sensor data from port and send it to ethernet board.
 */
void get_send_sensor_data(uint8_t ex_dsize)
{

	uint8_t txbuffer[4+ex_dsize*erxaddrcount];
	uint8_t i=0;
	uint16_t addr;

	bool error=false;
	uint8_t error_count=0;
	uint8_t txerrors[2+MAX_ADDR_COUNT*2];
	uint8_t rxdata_size = 0;

#ifdef DEBUG
	printf("DEBUG: get_send_sensor_data called\r\n");
#endif

	txbuffer[0]=REPLY_READINGS;  // Reply code
	txbuffer[1]=erxaddrcount * ex_dsize + 1; // S
	if(cmd_codeo == 64 || cmd_codeo == 65) {
		txbuffer[2]=cmd_codeo;
	} else {
		txbuffer[2]=cmd_code;   // CC
	}

	txbuffer[3]=erxaddrcount; // N
	txerrors[0]=REPLY_ERROR; // Reply code

	enable_rsport(cmd_port);
	//For each address send a sensor request and listen for reply.
	for(i=0; i < erxaddrcount; i++)
	{
		error=false;

		addr=cmd_addrs[i];
		if(!query_unit(addr))
		{
			//UNIT timed out
			txerrors[2+error_count*2]=ERROR_UNITTIMEOUT;
			txerrors[2+error_count*2+1]=(i+1);
			error_count++;
			error=true;
		} else {
			rxdata_size = urxbuffer[7];
		}

		//Check crc
		if(!error)
		{
			if(!good_crc(rxdata_size))
			{
				//CRC Error
#ifdef DEBUG
				printf("DEBUG: Bad crc\r\n");
#endif
				txerrors[2+error_count*2]=ERROR_BADCRC;
				txerrors[2+error_count*2+1]=(i+1);
				error_count++;
				error=true;
			}
		}

		if(!error)
		{
			if(rxdata_size == 0) 
			{
				//bad feature
#ifdef DEBUG
				printf("DEBUG: Unit missing feature\r\n");
#endif
				txerrors[2+error_count*2]=ERROR_MISSINGFEATURE;
				txerrors[2+error_count*2+1]=(i+1);
				error_count++;
				error=true;
			}
		}


		if(!error)
		{
			if(rxdata_size != ex_dsize) 
			{
				//Bad unit rx size
#ifdef DEBUG
				printf("DEBUG: Bad unit rx size\r\n");
#endif
				txerrors[2+error_count*2]=ERROR_BADUNITRXSIZE;
				txerrors[2+error_count*2+1]=(i+1);
				error_count++;
				error=true;
			}
		}

		if(!error)
		{
			//Add data to send package
			mymemcpy(&txbuffer[4+i*ex_dsize], (void*)&urxbuffer[8], ex_dsize);
		}
		else //There was a error, set data to zeros for that unit.
		{
#ifdef DEBUG
			printf("DEBUG: Zeroing unit data because of errors.\n\r");
#endif
			for(int n = 0; n < ex_dsize; n++)
			{
				txbuffer[4+i*ex_dsize+n]=0;
			}
		}
		wdt_reset(); //Reset watchdog timer
	}
	disable_rsports(); //We are done with the Port

	//Send any errors
	if(error_count)
	{
		txerrors[1]=error_count;
	}
	//Bytes in txerrors
	if(error_count > 0)
	{
		error_count=2+2*error_count;
	}
	//Send error and data
	send_errors_data(txerrors, error_count, txbuffer, sizeof(txbuffer));
}

/**
 * Send error and other data reply.
 */
void send_errors_data(uint8_t errors[], uint16_t errors_size, uint8_t data[], uint16_t data_size)
{
	uint16_t s = errors_size+data_size+2;

#ifdef DEBUG
	printf("DEBUG: send_errors_data called\r\n");
#endif
	fwrite(&s, sizeof(s), 1, stdout);
	if(errors_size)
	{
		fwrite(errors, errors_size, 1, stdout);
	}
	if(data_size)
	{
		fwrite(data, data_size, 1, stdout);
	}
}


/**
 * Send single error reply, then done.
 */
void send_error_reply_only(uint8_t code, uint8_t addrIdx)
{
	uint8_t error_buf[4];
	uint8_t d[1];

#ifdef DEBUG
	printf("DEBUG: send_error_reply_only called\r\n");
#endif

	error_buf[0]=REPLY_ERROR; //Reply Code
	error_buf[1]=1; //L
	error_buf[2]=code; //C_X
	error_buf[3]=code; //A_X
	send_errors_data(error_buf, 4, d, 0);
}


//Input from HW RX USART, from Ethernet board
void eth_input(uint8_t c)
{

	if(!activate)
	{
		if(erxcount < MAGIC_SIZE && check_magic(c, erxcount))
		{
			erxcount++;
			erxtimeout=0;
			return;
		}
		else if(erxcount < MAGIC_SIZE && erxcount != 0)
		{
			erxcount = 0;
			eth_input(c);
			return;
		}
		if(erxcount == MAGIC_SIZE)
		{
			cmd_codeo=c;
			cmd_code=c;
			erxcount++;
			erxtimeout=0;
			return;
		}

		if(cmd_code != CC_GUNITREAD && cmd_code != CC_CALREAD && cmd_code != CC_CALSET && erxcount >= MAGIC_SIZE+1)
		{
			if(cmd_code >= 1 && cmd_code <= 63) //Port Readings
			{
				if(erxcount == MAGIC_SIZE+1)
				{
					cmd_port=c;
					erxcount++;
					erxtimeout=0;
					return;
				}
					
				if(erxcount == MAGIC_SIZE+2)
				{
					erxaddrcount=c;
					if(erxaddrcount == 0 || erxaddrcount > MAX_ADDR_COUNT)
					{
						send_error_reply_only(ERROR_BADADDRCOUNT, 0);
						erxcount=0;
					}
					else
					{
						erxcount++;
					}
				}
				else if(erxcount >= MAGIC_SIZE+3 && ((erxcount-(MAGIC_SIZE+3))%2) == 0)
				{
					cmd_addrs[(erxcount-(MAGIC_SIZE+3))/2] = c;
					erxcount++;
				}
				else if(erxcount >= MAGIC_SIZE+3 && ((erxcount-(MAGIC_SIZE+3))%2) == 1)
				{
					cmd_addrs[(erxcount-(MAGIC_SIZE+3))/2] +=c <<8;
					erxcount++;
				}

				if(erxcount >= erxaddrcount*2+MAGIC_SIZE+3)
				{	
					activate=true;
					erxcount=0;
				}
				erxtimeout=0;
			}
			else if(cmd_code == CC_PING || cmd_code == CC_HUBVERSION) //PING
			{
				if(erxcount == MAGIC_SIZE+1)
				{
					cmd_addrs[0]=c;
					erxcount++;
				}
				else if(erxcount == MAGIC_SIZE+2)
				{
					cmd_addrs[0] += c << 8;
					activate = true;
					erxcount = 0;
				}
				erxtimeout=0;
			}
		}
		else if((cmd_code == CC_GUNITREAD || cmd_code == CC_CALREAD || cmd_code == CC_CALSET) && erxcount == MAGIC_SIZE+1)
		{
			cmd_codep=c;
			erxcount++;
			erxtimeout=0;
			return;
		}
		else if((cmd_code == CC_GUNITREAD || cmd_code == CC_CALREAD || cmd_code == CC_CALSET) && erxcount == MAGIC_SIZE+2)
		{
			cmd_size=c;
			erxtimeout=0;
			if(cmd_size > USIZE_MAX) {
				erxcount=0;
			} else {
				erxcount++;
			}
			return;
		}
		else if(cmd_code == CC_CALSET)
		{
			if(erxcount == MAGIC_SIZE+3)
			{
				cmd_port=c;
				cmd_cal_setcount=0;
			} else if (erxcount == MAGIC_SIZE+4) {
				erxaddrcount=1;
				cmd_addrs[0] = c;
			} else if (erxcount == MAGIC_SIZE+5) {
				cmd_addrs[0] +=c <<8;
			} else if (erxcount > MAGIC_SIZE+5) {
				//get until cmd_size amount then done
				cmd_cal_set[cmd_cal_setcount]=c;
				cmd_cal_setcount++;
				if(cmd_cal_setcount == cmd_size) {
					activate=true;
					erxcount=0;
					return;
				}
			}
			erxcount++;
			erxtimeout=0;
		}
		else if((cmd_code == CC_GUNITREAD || cmd_code == CC_CALREAD) && erxcount >= MAGIC_SIZE+3)
		{
			if(cmd_codep >= 1 && cmd_codep <= 63) //Port Readings
			{
				if(erxcount == MAGIC_SIZE+3)
				{
					cmd_port=c;
					erxcount++;
					erxtimeout=0;
					return;
				}
					
				if(erxcount == MAGIC_SIZE+4)
				{
					erxaddrcount=c;
					if(erxaddrcount == 0 || erxaddrcount > MAX_ADDR_COUNT)
					{
						send_error_reply_only(ERROR_BADADDRCOUNT, 0);
						erxcount=0;
					}
					else
					{
						erxcount++;
					}
				}
				else if(erxcount >= MAGIC_SIZE+5 && ((erxcount-(MAGIC_SIZE+5))%2) == 0)
				{
					cmd_addrs[(erxcount-(MAGIC_SIZE+5))/2] = c;
					erxcount++;
				}
				else if(erxcount >= MAGIC_SIZE+5 && ((erxcount-(MAGIC_SIZE+5))%2) == 1)
				{
					cmd_addrs[(erxcount-(MAGIC_SIZE+5))/2] +=c <<8;
					erxcount++;
				}

				if(erxcount >= erxaddrcount*2+MAGIC_SIZE+5)
				{	
					activate=true;
					erxcount=0;
				}
				erxtimeout=0;
			}
		}
	}
}

//Recieves input from UNIT
void unit_input(uint8_t c, uint16_t addr)
{
	if(!urxdone)
	{
		if(urxidx < 4 && check_magic(c, urxidx))
		{
			urxidx++;
			return;
		}
		else if(urxidx < 4 && urxidx != 0)
		{
			urxidx = 0;
			unit_input(c, addr);
		}
		if(urxidx >= 4 )
		{
			if(urxidx == 4)
			{
				urxbuffer[0]=MAGIC0;
				urxbuffer[1]=MAGIC1;
				urxbuffer[2]=MAGIC2;
				urxbuffer[3]=MAGIC3;
			}

			urxbuffer[urxidx]=c;
			urxidx++;
			if(urxidx == 8) {
				if(urxbuffer[7] > USIZE_MAX) {
					urxidx=0;
					urxdone=true;
				}
			}
			if(urxidx > 8 && urxidx == 9+urxbuffer[7])
			{
				//Check if correct address, if not keep listening from the beginning
				if( ((uint16_t)(urxbuffer[5]) << 8) + urxbuffer[4] == addr)
				{
					urxdone=true;
					urxidx=0;
				}
				else
				{
					urxidx=0;
				}
			}
		}
	}
}


void ioinit(void)
{
	softuart_init();
	softuart_turn_rx_on();
	//Turn on watch dog
	wdt_enable(WDTO_8S);
	sei(); //Enable interrupts
	DDRD &=~_BV(PD0); //Read on hw rx usart 
	DDRD |= _BV(PD1);

	//Hardware USART
	UBRR0H = UBRRH_VALUE;
	UBRR0L = UBRRL_VALUE;
	//UCSR0B = (1<<RXEN0)|(1<<TXEN0)|(1<<RXCIE0);
	UCSR0B = (1<<RXEN0)|(1<<TXEN0);
	stdout = &mystdout;
	stderr = &suart_stream;
	//Init RS485 RE DE ports
	//Output on RE and DE pins
	RSP1REDDR |= _BV(RSP1RE);
	RSP1DEDDR |= _BV(RSP1DE);
	RSP2REDDR |= _BV(RSP2RE);
	RSP2DEDDR |= _BV(RSP2DE);
	RSP3REDDR |= _BV(RSP3RE);
	RSP3DEDDR |= _BV(RSP3DE);
	RSP4REDDR |= _BV(RSP4RE);
	RSP4DEDDR |= _BV(RSP4DE);
	RSP5REDDR |= _BV(RSP5RE);
	RSP5DEDDR |= _BV(RSP5DE);
	RSP6REDDR |= _BV(RSP6RE);
	RSP6DEDDR |= _BV(RSP6DE);
	disable_rsports();
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

// interface between avr-libc stdio and the modified Fleury uart-lib:
static int swuart_putchar( char c, FILE *stream )
{
	//if ( c == '\n' ) {
	//softuart_putchar( '\r' );
	//}
	softuart_putchar( c );

	return 0;
}

void uart_rxflush(void)
{
	while(uart_kbhit())
	{
		uart_getchar();
	}
}

/**
 * Is there a character in buffer?
 */
uint8_t uart_kbhit(void)
{
	return (UCSR0A & (1<<RXC0));
}


/*
 * Get character from serial
 */
uint8_t uart_getchar(void)
{
	while( !(UCSR0A & (1<<RXC0)) );
	return(UDR0);
}

/*
 * Keeps track if magic bytes were sent
 * return true if we recieved all magic bytes.
 */
bool check_magic(uint8_t c, uint8_t idx)
{
	//Change if you change MAGIC_SIZE
	if((idx == 0 && c != MAGIC0) || (idx == 1 && c != MAGIC1) || 
			(idx == 2 && c != MAGIC2) || (idx == 3 && c != MAGIC3) )
	{
		return false;
	}
	return true;
}



/*
 * Disable RE and DE on all RS485 chips.
 */
void disable_rsports(void)
{
	//High is Disabled for RE
	RSP1REPORT |= _BV(RSP1RE);
	RSP1DEPORT &= ~_BV(RSP1DE);

	RSP2REPORT |= _BV(RSP2RE);
	RSP2DEPORT &= ~_BV(RSP2DE);

	RSP3REPORT |= _BV(RSP3RE);
	RSP3DEPORT &= ~_BV(RSP3DE);

	RSP4REPORT |= _BV(RSP4RE);
	RSP4DEPORT &= ~_BV(RSP4DE);

	RSP5REPORT |= _BV(RSP5RE);
	RSP5DEPORT &= ~_BV(RSP5DE);

	RSP6REPORT |= _BV(RSP6RE);
	RSP6DEPORT &= ~_BV(RSP6DE);

}

/*
 * Enable RE and DE for just port.
 */
void enable_rsport(uint8_t port)
{
	disable_rsports();

#ifdef DEBUG
	printf("DEBUG: enable_rsport %d\r\n", port);
#endif

	//Low is enable for RE
	//High is enable for DE
	if(port == 1)
	{
		RSP1REPORT &= ~_BV(RSP1RE);
		RSP1DEPORT |= _BV(RSP1DE);
	}
	else if(port == 2)
	{
		RSP2REPORT &= ~_BV(RSP2RE);
		RSP2DEPORT |= _BV(RSP2DE);
	}
	else if(port == 3)
	{
		RSP3REPORT &= ~_BV(RSP3RE);
		RSP3DEPORT |= _BV(RSP3DE);
	}
	else if(port == 4)
	{
		RSP4REPORT &= ~_BV(RSP4RE);
		RSP4DEPORT |= _BV(RSP4DE);
	}
	else if(port == 5)
	{
		RSP5REPORT &= ~_BV(RSP5RE);
		RSP5DEPORT |= _BV(RSP5DE);
	}
	else if(port == 6)
	{
		RSP6REPORT &= ~_BV(RSP6RE);
		RSP6DEPORT |= _BV(RSP6DE);
	}
}

