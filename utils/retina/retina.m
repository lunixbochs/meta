#/*
echo "Building ./retina"
gcc "$0" -framework Foundation -framework AppKit -o retina
exit 0
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "retina.h"

// sorts for highest effective resolution modes first
int sort_modes(const void *a, const void *b) {
    const display_mode_t *da = a, *db = b;
    if (strlen(da->name) < strlen(db->name) || da->scale > db->scale) return 1;
    if (strlen(da->name) > strlen(db->name) || da->scale < db->scale) return -1;
    return strcmp(da->name, db->name) * -1;
}

// grab all the modes and attach a name string
void get_all_modes(CGDirectDisplayID display, display_mode_t **retModes, int *count) {
    CGSGetNumberOfDisplayModes(display, count);
    if (! *count || !retModes) return;
    display_mode_t *modes = malloc(sizeof(display_mode_t) * *count);
    for (int i = 0; i < *count; i++) {
        CGSGetDisplayModeDescriptionOfLength(display, i, modes+i, MODE_SIZE);
        display_mode_t *mode = &modes[i];
        if (mode->scale > 1) {
            snprintf(mode->name, 32, "%dx%d@%.0f", mode->width, mode->height, mode->scale);
        } else {
            snprintf(mode->name, 32, "%dx%d", mode->width, mode->height);
        }
    }
    qsort(modes, *count, sizeof(display_mode_t), sort_modes);
    *retModes = modes;
}

// get the current mode for a display
int get_display_mode(CGDirectDisplayID display) {
    int mode;
    CGSGetCurrentDisplayMode(display, &mode);
    return mode;
}

// set the current mode for a display
void set_display_mode(CGDirectDisplayID display, int mode) {
    CGDisplayConfigRef config;
    CGBeginDisplayConfiguration(&config);
    CGSConfigureDisplayMode(config, display, mode);
    CGCompleteDisplayConfiguration(config, kCGConfigurePermanently);
}

int main(int argc, const char **argv) {
    CGDirectDisplayID main_display = CGMainDisplayID();
    display_mode_t *modes;
    int count;
    get_all_modes(CGMainDisplayID(), &modes, &count);

    if (argc >= 2) {
        // select argv[1] as current mode
        for (int i = 0; i < count; i++) {
            if (strcmp(modes[i].name, argv[1]) == 0) {
                if (modes[i].mode == get_display_mode(main_display)) {
                    printf("Mode already active.\n");
                    return 1;
                }
                set_display_mode(CGMainDisplayID(), modes[i].mode);
                return 0;
            }
        }
        printf("Mode not found.\n\n");
    }

    // print usage and mode columns
    printf("Usage: %s <mode>\n", argv[0]);
    printf("Modes:\n");
    for (int i = 0; i < count; i++) modes[i].skip = 0;
    for (int i = 0; i < count; i++) {
        display_mode_t *a = &modes[i], *b;
        if (a->skip) continue;
        a->skip = 1;
        // pad to column * scale (in case a resolution isn't available unscaled?)
        for (int s = 1; s < a->scale; s++)
            printf("%14s", "");
        printf("%14s", a->name);
        // print scaled equivalents in the same row
        for (int j = 0; j < count; j++) {
            b = &modes[j];
            if (a == b || b->skip) continue;
            if (a->width * a->scale == b->width * b->scale &&
                    a->height * a->scale == b->height * b->scale) {
                printf("%14s", b->name);
                b->skip = 1;
            }
        }
        printf("\n");
    }
    return 1;
}
