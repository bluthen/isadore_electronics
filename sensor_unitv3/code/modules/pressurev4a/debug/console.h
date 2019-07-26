#ifndef CONSOLE_H
#define CONSOLE_H

#include <stdbool.h>

//Max command length including null terminator 
#define CONSOLE_CMD_LEN 30 

void console_ioinit(void);
bool console_command_ready(void);
void console_command_reset(void);
char* get_console_command(void);

#endif
