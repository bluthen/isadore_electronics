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
#include <math.h>
#include <stdio.h>
#include <stdint.h>


uint16_t h_t_to_shth(uint32_t h) {
	return (uint16_t)(h);
}

uint16_t t_to_shtt(int32_t t) {
	return (uint16_t)((100*t + 401111 + 50)/100);
}

uint16_t get_p(uint32_t pres) {
return (uint16_t)(((pres-50000)*1000)/2290);
}


int main() {
	printf("%d,%d,%d\n", t_to_shtt(4012), h_t_to_shth(9834), get_p(104123));
	return 0;
}
