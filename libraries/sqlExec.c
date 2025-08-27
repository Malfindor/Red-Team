// Designed to be uploaded to a Mariadb instance as 'sys_exec()'
#include <mysql.h>
#include <string.h>
#include <stdlib.h>

// Initialization function
my_bool sys_exec_init(UDF_INIT *initid, UDF_ARGS *args, char *message) {
    if (args->arg_count != 1) {
        strcpy(message, "sys_exec() requires exactly one argument");
        return 1;  // error
    }
    if (args->arg_type[0] != STRING_RESULT) {
        strcpy(message, "sys_exec() requires one string");
        return 1;  // error
    }
    return 0; // success
}

// Main function
int sys_exec(UDF_INIT *initid, UDF_ARGS *args, char *is_null, char *error) {
    char *cmd = args->args[0];
	system(cmd);
    return 0; // success
}

void sys_exec_deinit(UDF_INIT *initid) {}
