#/*
echo "Building ./taplist"
gcc "$0" -framework CoreGraphics -o taplist
exit 0
*/

#include <CoreGraphics/CoreGraphics.h>
#include <libproc.h>
#include <libgen.h>

char *process_name(int pid) {
    char name[PROC_PIDPATHINFO_MAXSIZE] = {0};
    if (proc_name(pid, name, 1024) <= 0) {
        if (proc_pidpath(pid, name, 1024) > 0) {
            return strdup(basename(name));
        } else {
            return strdup("<unknown process>");
        }
    }
    return strdup(name);
}

struct event {
    char *name;
    uint64_t num;
    uint64_t bit;
};
#define ev(name) {#name, name, CGEventMaskBit(name)}
struct event events[] = {
    ev(kCGEventNull),
    ev(kCGEventLeftMouseDown),
    ev(kCGEventLeftMouseUp),
    ev(kCGEventRightMouseDown),
    ev(kCGEventRightMouseUp),
    ev(kCGEventMouseMoved),
    ev(kCGEventLeftMouseDragged),
    ev(kCGEventRightMouseDragged),
    ev(kCGEventKeyDown),
    ev(kCGEventKeyUp),
    ev(kCGEventFlagsChanged),
    ev(kCGEventScrollWheel),
    ev(kCGEventTabletPointer),
    ev(kCGEventTabletProximity),
    ev(kCGEventOtherMouseDown),
    ev(kCGEventOtherMouseUp),
    ev(kCGEventOtherMouseDragged),
    // NX events:
    ev(NX_KITDEFINED),
    ev(NX_SYSDEFINED),
    ev(NX_APPDEFINED),
    ev(NX_ZOOM),
};
#undef ev

void print_mask(uint64_t mask) {
    if (mask == kCGEventMaskForAllEvents) {
        printf("kCGEventMaskForAllEvents (%#llx)\n", mask);
        return;
    }
    bool first = true;
    for (int i = 0; i < sizeof(events) / sizeof(events[0]); i++) {
        if (mask & events[i].bit) {
            if (!first) printf(" | ");
            printf("%s", events[i].name);
            first = false;
        }
    }
    if (!first) printf(" ");
    printf("(%#llx)\n", mask);
}

const char *location_name(uint32_t location) {
    switch (location) {
        case kCGHIDEventTap: return "kCGHIDEventTap";
        case kCGSessionEventTap: return "kCGSessionEventTap";
        case kCGAnnotatedSessionEventTap: return "kCGAnnotatedSessionEventTap";
        default: return "<unknown>";
    }
}

int main() {
    uint32_t count = 0;
    CGError err = 0;
    if ((err = CGGetEventTapList(0, NULL, &count))) {
        printf("error fetching event taps: %d\n", err);
        return -1;
    }
    CGEventTapInformation *taps = calloc(sizeof(CGEventTapInformation), count);
    if ((err = CGGetEventTapList(count, taps, &count))) {
        printf("error fetching event taps: %d\n", err);
        return -1;
    }
    for (uint32_t i = 0; i < count; i++) {
        CGEventTapInformation *tap = &taps[i];
        printf("- %d:\n", tap->eventTapID);
        char *process = process_name(tap->tappingProcess);
        char *target = process_name(tap->processBeingTapped);

        printf("    enabled: %s\n", tap->enabled ? "true" : "false");
        printf("    process: %s (%d)\n", process, tap->tappingProcess);
        if (tap->processBeingTapped)
            printf("  target: %s (%d)\n", target, tap->processBeingTapped);
        printf("    options: %s (%#x)\n", (tap->options&1 ? "kCGEventTapOptionDefault" : "kCGEventTapOptionListenOnly"), tap->options);
        printf("   location: %s\n", location_name(tap->tapPoint));
        printf("       mask: ");
        print_mask(tap->eventsOfInterest);
        printf("    latency: min=%.3fms avg=%.3fms max=%.3fms\n", tap->minUsecLatency/1000, tap->avgUsecLatency/1000, tap->maxUsecLatency/1000);
        printf("\n");

        free(process);
        free(target);
    }
}
