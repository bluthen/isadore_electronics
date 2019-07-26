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

#include "adc.h"
#include "pressurev1/pressurev1.h"

#define PRESSUREV1_AVG_COUNT 5

static double pressurev1_getp(void);

double pressurev1_getp(void)
{
	double convert = 0.0;
	uint16_t p;

	for(int i = 0; i < PRESSUREV1_AVG_COUNT; i++) {
		p = read_adc16(ADMUX_PRESSUREV1);
		// Convert to kPa
		convert += (CAL_PRESSUREV1_M * (double)p*5.0/1023.0 + CAL_PRESSUREV1_B)/PRESSUREV1_AVG_COUNT;
	}
	return convert;
}

uint16_t pressurev1_get(void)
{
	double p = 0;
	p = pressurev1_getp();
	// Convert to conversion value
	p = (p-50.0)/0.0022888;	

	return (uint16_t)(p+0.5);
}

uint32_t pressurev1_get_wide(void)
{
	uint32_t p;
	p = (uint32_t)(pressurev1_getp()*1000.0 + 0.5);
	return p;
}

