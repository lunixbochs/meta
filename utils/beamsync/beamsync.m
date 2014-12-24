#/*
echo "Building ./beamsync"
gcc "$0" -framework Foundation -framework AppKit -o beamsync
exit 0
*/
#import <Foundation/Foundation.h>

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

int main(int argc, const char *argv[]) {
    set(disable);
    NSLog(@"BeamSync disabled.");
    return 0;
}
