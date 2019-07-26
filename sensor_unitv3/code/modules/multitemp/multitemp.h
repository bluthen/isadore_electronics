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
#ifndef __MULTIPOINT
#define __MULTIPOINT

#include <stdint.h>
#include <stdbool.h>

/** Inits multipoint temp code, should be called once. */
void multitemp_init(void);
/** Get next temperature on channel. 
 * @param channel should be 1-4
 * @returns temperature value or 0xFFFF if no more sensors found.
 */
uint16_t multitemp_get(uint8_t channel);
bool multitemp_get_addr(uint8_t channel, uint8_t* dsaddress);
/** Restart which sensor address we are on. */
void multitemp_reset(void);

#endif
