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
#ifndef PRESSUREV1_H
#define PRESSUREV1_H

#define ADMUX_PRESSUREV1 0x02
#define ADMUX_PRESSUREV1_RAW 0x03

uint16_t pressurev1_get(void);
uint32_t pressurev1_get_wide(void);

#endif
