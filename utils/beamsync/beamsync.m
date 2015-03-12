#/*
echo "Building ./beamsync"
gcc "$0" -framework Foundation -framework AppKit -o beamsync
exit 0
*/
#import <Foundation/Foundation.h>
#include <string.h>

extern void CGSSetDebugOptions(int);
extern void CGSDeferredUpdates(int);

enum {
    disable = 0,
    automatic = 1,
    forced = 2
};

void set(int mode) {
    CGSSetDebugOptions(mode ? 0 : 0x08000000);
    CGSDeferredUpdates(mode);
}

int try(const char *cmd, const char *match, int flag) {
    if (strcmp(cmd, match) == 0) {
        set(flag);
        NSLog(@"BeamSync %sd.", match);
        return 1;
    }
    return 0;
}

int main(int argc, const char *argv[]) {
    if (argc > 1) {
        if (!(try(argv[1], "enable", automatic) ||
              try(argv[1], "disable", disable))) {
            printf("Usage: %s [enable|disable]\n", argv[0]);
            return 1;
        }
    } else {
        set(disable);
        NSLog(@"BeamSync disabled.");
    }
    return 0;
}
