#define BAUD 9600

#include <stdio.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <util/setbaud.h>
#include <util/crc16.h>

#include "softuart.h"

#define RS485RE PB0
#define RS485REPORT PORTB
#define RS485REDDR DDRB
#define RS485DE PD4
#define RS485DEPORT PORTD
#define RS485DEDDR DDRD

static void ioinit(void);
static int uart_putchar(char c, FILE *stream);
static uint8_t uart_getchar(void);
static int swuart_putchar( char c, FILE *stream );
static FILE mystdout = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);
static FILE suart_stream = FDEV_SETUP_STREAM(swuart_putchar, NULL, _FDEV_SETUP_WRITE );

int main(void)
{
	uint16_t time = 0;
	uint16_t count = 0;
	unsigned char c = 0;
	ioinit();
	fprintf(stderr, "Unit rs485 test listening on rs485...\r\n");
	//DEBUG
	//turn on to rs485
	RS485DEPORT |=_BV(RS485DE); //DE is enabled when high
	fprintf(stderr, "DE on\r\n");
	while(1)
	{

		while (UCSR0A & (1<< RXC0))
		{
			c=UDR0;
			fprintf(stderr, "R: %c\r\n", c);
		}
		if(time >= 50000)
		{
			fprintf(stderr, "UC: %d\r\n", count);
			fprintf(stdout, "UC: %d\r\n", count);
			time=0;
			count++;
		}
		_delay_us(100);
		time++;
	}
}

void ioinit(void)
{
	softuart_init();
	sei(); //enable interupts
	DDRD &=~_BV(PD0); // read on usart RX pin
	DDRD |=_BV(PD1); // output on usart TX pin
	UBRR0H = UBRRH_VALUE;
	UBRR0L = UBRRL_VALUE;
	//UCSR0B = (1 << RXEN0)|(1<<TXEN0)|(1<<RXCIE0);
	UCSR0B = (1 << RXEN0)|(1<<TXEN0);
	stdout = &mystdout;
	stderr = &suart_stream;
	//Set RE and DE to outputs
	RS485REDDR |= _BV(RS485RE);
	RS485DEDDR |= _BV(RS485DE);
	//Enable RE, disable DE
	RS485REPORT &=~_BV(RS485RE); //RE is enabled when low
	RS485DEPORT &=~_BV(RS485DE); //DE is disabled when low
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
	if ( c == '\n' ) {
		softuart_putchar( '\r' );
	}
	softuart_putchar( c );

	return 0;
}
