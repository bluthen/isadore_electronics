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
#include "adc.h"
#include "pressurev5/pressurev5.h"

#define PRESSUREV5_AVG_COUNT 10
#define CENTIPA_PER_INH2O 249174
#define INH2O_PER_V (10/2.4)

static double pressurev5_getp(void);

double pressurev5_getp(void)
{
	double convert = 0.0;
	uint16_t p;

	for(int i = 0; i < PRESSUREV5_AVG_COUNT; i++) {
		p = read_adc16(ADMUX_PRESSUREV5);
		if( p > 0) {
			// Convert to kPa
			convert += (CAL_PRESSUREV5_M * (double)p*5.0/1023.0 + CAL_PRESSUREV5_B)/PRESSUREV5_AVG_COUNT;
		}
		_delay_ms(5);
	}
	return convert;
}

uint32_t pressurev5_get_wide(void)
{
	uint32_t p;
	double gp;
	gp = pressurev5_getp();
	if(gp > 0) {
		//Convert voltage to centipascals then transfer value.
		p = (uint32_t)((pressurev5_getp() - 2.5)*INH2O_PER_V*CENTIPA_PER_INH2O + 2147483647 + 0.5);
		return p;
	} else {
		return 0xFFFFFFFF;
	}
}

