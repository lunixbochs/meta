#/*
echo "Building ./retina"
gcc "$0" -framework Foundation -framework AppKit -o retina
exit 0
*/

#import <Foundation/Foundation.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
            snprintf(mode->name, 32, "%dx%d@%.0f,%dhz", mode->width, mode->height, mode->scale, mode->freq);
        } else {
            snprintf(mode->name, 32, "%dx%d,%dhz", mode->width, mode->height, mode->freq);
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

void print_display(CGDirectDisplayID display, int num) {
    display_mode_t *modes;
    int count;
    get_all_modes(display, &modes, &count);

    int current_mode_num = get_display_mode(display);
    display_mode_t *current_mode;
    for (int i = 0; i < count; i++) {
        if (modes[i].mode == current_mode_num) {
            current_mode = &modes[i];
        }
    }

    printf("Display [%d]", num);
    if (current_mode != NULL) {
        printf(" (now: %s)\n", current_mode->name);
    } else {
        printf("\n");
    }
    printf("  Allowed modes:\n  ");
    for (int i = 0; i < count; i++) modes[i].skip = 0;
    for (int i = 0; i < count; i++) {
        display_mode_t *a = &modes[i], *b;
        if (a->skip) continue;
        a->skip = 1;
        // pad to column * scale (in case a resolution isn't available unscaled?)
        for (int s = 1; s < a->scale; s++)
            printf("%18s", "");
        printf("%18s", a->name);
        // print scaled equivalents in the same row
        for (int j = 0; j < count; j++) {
            b = &modes[j];
            if (a == b || b->skip) continue;
            if (a->width * a->scale == b->width * b->scale &&
                    a->height * a->scale == b->height * b->scale) {
                printf("%18s", b->name);
                b->skip = 1;
            }
        }
        printf("\n  ");
    }
    printf("\n");
}

void set_friendly_mode(CGDirectDisplayID display, int num, const char *mode) {
    display_mode_t *modes;
    int count;
    get_all_modes(display, &modes, &count);
    int current_mode_num = get_display_mode(display);

    for (int i = 0; i < count; i++) {
        if (strcmp(modes[i].name, mode) == 0) {
            if (modes[i].mode == current_mode_num) {
                printf("[%d] already at %s\n", num, mode);
                return;
            }
            set_display_mode(display, modes[i].mode);
            return;
        }
    }
    printf("[%d] does not support mode %s\n", num, mode);
    print_display(display, num);
}

int main(int argc, const char **argv) {
    CGDirectDisplayID activeDisplays[128];
    uint32_t count;
    CGGetActiveDisplayList(128, activeDisplays, &count);
    if (argc < 2) {
        printf("Usage: %s [display] <mode>\n", argv[0]);
        for (int i = 0; i < count; i++) {
            print_display(activeDisplays[i], i);
        }
        return 1;
    } else if (argc == 2) {
        set_friendly_mode(CGMainDisplayID(), 0, argv[1]);
    } else if (argc > 2) {
        for (int i = 1; i < argc; i += 2) {
            int display = strtol(argv[i], NULL, 10);
            if (display >= 0 && display < count && i + 1 < argc) {
                set_friendly_mode(activeDisplays[display], display, argv[i + 1]);
            } else {
                printf("Invalid final display arguments (at %s).\n", argv[i]);
            }
        }
    }
    return 0;
}
