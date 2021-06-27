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
#include <util/atomic.h>
#include <avr/wdt.h>
#include "anemometer.h"
#define SPEEDTO 20000
#define DEBOUNCETO 15


static volatile uint16_t counter = 0;
static volatile uint16_t best_counter = 0;

static volatile unsigned long timer1_comp_count = 0;
static volatile unsigned long debounce_time = 0;
static volatile unsigned long lastspeed_time = 0;

static unsigned long millis(void);

/**
 * Counts anemometer ticks on falling edge with 15ms debounce.
 * 15ms is 150mph which will be our limited speed
 */
ISR(PCINT0_vect)
{
    if(!(PINB & _BV(PB5))) { //Falling edge since normally is high from pullup
       unsigned long m = millis();
       // debounce_time > m is from 50 day overflow
       // May get one extra count from ringing
       if (debounce_time > m || m - debounce_time > DEBOUNCETO) {
           counter++;
           debounce_time = m;
       }
    }
}

/**
 * 1) Increment millisecond timer counter
 * 2) Every SPEEDTO seconds copy counter to best_counter that is used in calculation for mph
 */
ISR(TIMER1_COMPA_vect)
{
    unsigned long m = timer1_comp_count;
    unsigned long lt = lastspeed_time;
    m += 1;
    timer1_comp_count = m;
    if (lt > m) {
        // We overflowed at 50 days, ignore this one.
        lastspeed_time = m;
        counter = 0;
    } else if (m - lt >= SPEEDTO) {
        lastspeed_time=m;
        best_counter = counter;
        counter = 0;
    }
}

/**
 * Returns cpu run time in milliseconds
 */
unsigned long millis()
{
    unsigned long m;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        m = timer1_comp_count;
    }
    return m;
}

/**
 * Returns last anemometer reading in mph*100 rounded to decimal places.
 */
uint16_t anemometer_mph(void)
{
    uint16_t c;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        c = best_counter;
    }
	return (uint16_t)(((double)c)*225.0/(((double)SPEEDTO)/1000.0) + 0.5);
}

/**
 * 1) Sets input and pull on PB5
 * 2) Sets up interrupt on PB5 to count ticks
 * 3) Sets timer to get millisecond time and periodically copy and reset PB5 counter.
 * 4) Enables interupts
 */
void anemometer_ioinit(void)
{
    TCCR1A = 0;
    TCCR1B = 0;
	TCCR1B =(1<<WGM12) | (1 << CS11); // Timer 1 CTC mode and div/8
	TIMSK1 = (1 << OCIE1A); // Enable CTC interrupt
	OCR1A = 500; // millisecond when using clock4mhz/8

    // PB5 PCINT
	DDRB &=~_BV(DDB5); // read on PB5
	PORTB |= _BV(PORTB5); //Enable internal pullup resistor
    PCICR |= (1 << PCIE0); // Enable Interrupts PCINT7..0, PB5 is PCINT5
	PCMSK0 |= (1 << PCINT5); //Enable specifically PB5 pin interrupt PCINT5

	sei(); //enable interupts
}
