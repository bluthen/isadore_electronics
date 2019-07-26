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
#include <stdbool.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/wdt.h>
#include "anemometer.h"

#define DATA_SIZE 30


static volatile uint16_t counter = 0;
static volatile bool even = true;

static volatile uint16_t data[DATA_SIZE];
static volatile uint8_t idx = 0;
static volatile bool index_wrap = false;
static volatile bool throw_out = false;

ISR(INT0_vect) {
	if(even) {
		++counter;
	}
	even = !even;
}

ISR(TIMER1_COMPA_vect) {
	if(!throw_out) {
		data[idx]=counter;
		++idx;
		counter = 0;
		if(idx == DATA_SIZE) {
			idx=0;
			index_wrap = true;
		}
	} else {
		counter = 0;
		throw_out = false;
	}
}

uint16_t anemometer_mph(void)
{
	uint32_t sum = 0;
	uint8_t data_size = DATA_SIZE;
	uint16_t i = 0;
	cli();
	throw_out = true;
	if(!index_wrap) {
		data_size=idx;
	}
	for(i=0; i < data_size; i++) {
		sum+=data[i];
	}
	sei();
	//return (uint16_t)sum;
	//return (uint16_t)100;
	return (uint16_t)((100.0*((double)(sum))*(2.25/data_size)) + 0.5);
}

void anemometer_ioinit(void)
{
	DDRD &=~_BV(PD2); // read on PD2 
	PORTD |= _BV(PD2); //Enable internal pullup resistor 

	TCCR1B |=(1<<WGM12); // Timer 1 CTC mode
	TIMSK1 |= (1 << OCIE1A); // Enable CTC interrupt
	OCR1A = 15624; // one second when using cpu/256

	// For 4Mhz
	TCCR1B |= (1 << CS12);  // clk/256

	//PCICR |= (1 << PCIE2);    //Enables interrupt vector1 (interupts 16:23)
	//PCMSK2 |= (1 << PCINT18); //PD2 interrupt PCINT18
	EICRA |= (1 << ISC00);
	EIMSK |= (1 << INT0);
	sei(); //enable interupts
}

