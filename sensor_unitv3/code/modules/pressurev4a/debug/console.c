
#define BAUD 9600

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>

#include <util/delay.h>
#include <util/setbaud.h>

#include "console.h"

static int uart_putchar(char c, FILE *stream);
static FILE mystdout = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);

static uint8_t volatile inputc=0;
static char inputstr[CONSOLE_CMD_LEN];
static char command[CONSOLE_CMD_LEN];
static bool volatile command_ready=false;

bool console_command_ready(void) {
	return command_ready;
}

void console_command_reset(void) {
	command_ready=false;
}

char* get_console_command(void) {
	return command;
}

/*
 * Init ports and RX TX
 */
void console_ioinit(void)
{
#ifdef DEBUG
    printf("DEBUG: Console Intializing IO\n");
#endif
    sei();
    DDRD &=~_BV(PD0); //PORTD (RX on PD0)
    DDRD |= _BV(PD1);

    UBRR0H = UBRRH_VALUE;
    UBRR0L = UBRRL_VALUE;
    UCSR0B = (1<<RXEN0)|(1<<TXEN0)|(1<<RXCIE0);
    stdout = &mystdout;
}

/*
 * Send character to serial
 */
static int uart_putchar(char c, FILE *stream)
{
    if (c == '\n') uart_putchar('\r', stream);

    loop_until_bit_is_set(UCSR0A, UDRE0);
    UDR0 = c;

    return 0;
}

//Input from serial port RX.
SIGNAL(USART_RX_vect)
{
    char c =UDR0;
    if(c=='\n' || c == '\r')
    {
        putchar('\r');
        if(inputc > 0)
        {
            inputstr[inputc]=0;
            strcpy(command, inputstr);
            command_ready=true;
        }
        else
        {
            putchar(']');
        }
        inputc=0;
        return;
    }

    if(inputc >= CONSOLE_CMD_LEN-2)
    {
        putchar('\n');
        inputc=0;
    }
    else
    {
        inputstr[inputc]=c;
        putchar(c);
        inputc++;
    }
}
