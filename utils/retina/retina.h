#import <Foundation/Foundation.h>
#include <stdint.h>

#ifndef RETINA_H
#define RETINA_H

typedef struct {
    uint32_t mode;
    uint32_t flags;
    uint32_t width;
    uint32_t height;
    uint32_t depth;
    uint32_t dc2[42];
    uint16_t dc3;
    uint16_t freq;
    uint32_t dc4[4];
    float scale;

    char name[32];
    int skip;
} display_mode_t;

#define MODE_SIZE (sizeof(display_mode_t) - sizeof(char) * 32 - sizeof(int))

void CGSGetCurrentDisplayMode(CGDirectDisplayID display, int *mode);
void CGSConfigureDisplayMode(CGDisplayConfigRef config, CGDirectDisplayID display, int mode);
void CGSGetNumberOfDisplayModes(CGDirectDisplayID display, int *count);
void CGSGetDisplayModeDescriptionOfLength(CGDirectDisplayID display, int index, display_mode_t *mode, int length);

#endif
