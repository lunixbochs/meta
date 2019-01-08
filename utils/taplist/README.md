taplist
====

View systemwide CGEventTap information on macOS.

Building
----

    sh taplist.c

Example
----

```
$ ./taplist

- 337453826:
    enabled: true
    process: universalaccessd (331)
    options: kCGEventTapOptionListenOnly (0)
   location: kCGSessionEventTap
       mask: kCGEventLeftMouseDown | kCGEventLeftMouseUp | kCGEventRightMouseDown | kCGEventRightMouseUp | kCGEventMouseMoved | kCGEventLeftMouseDragged | kCGEventR
ightMouseDragged | kCGEventScrollWheel | kCGEventTabletPointer | kCGEventTabletProximity | kCGEventOtherMouseDown | kCGEventOtherMouseUp | kCGEventOtherMouseDragged
 | NX_ZOOM (0xffc000fe)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 400000569:
    enabled: false
    process: universalaccessd (331)
    options: kCGEventTapOptionListenOnly (0)
   location: kCGSessionEventTap
       mask: kCGEventLeftMouseDown | kCGEventLeftMouseUp | kCGEventRightMouseDown | kCGEventRightMouseUp | kCGEventMouseMoved | kCGEventLeftMouseDragged | kCGEventR
ightMouseDragged | kCGEventScrollWheel | kCGEventTabletPointer | kCGEventTabletProximity | kCGEventOtherMouseDown | kCGEventOtherMouseUp | kCGEventOtherMouseDragged
 | NX_ZOOM (0x1fc000fe)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 1025202362:
    enabled: true
    process: ViewBridgeAuxiliary (480)
    options: kCGEventTapOptionDefault (0x1)
   location: kCGSessionEventTap
       mask: kCGEventKeyDown | kCGEventKeyUp | kCGEventFlagsChanged (0x1c00)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 1189641421:
    enabled: true
    process: NotificationCenter (390)
    options: kCGEventTapOptionDefault (0x1)
   location: kCGAnnotatedSessionEventTap
       mask: (0x80000000)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 1649760492:
    enabled: true
    process: ViewBridgeAuxiliary (377)
    options: kCGEventTapOptionDefault (0x1)
   location: kCGSessionEventTap
       mask: kCGEventKeyDown | kCGEventKeyUp | kCGEventFlagsChanged (0x1c00)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 719885386:
    enabled: true
    process: universalaccessd (331)
    options: kCGEventTapOptionDefault (0x1)
   location: kCGSessionEventTap
       mask: kCGEventKeyDown | kCGEventKeyUp | kCGEventFlagsChanged (0x1c00)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 424238335:
    enabled: false
    process: universalaccessd (331)
    options: kCGEventTapOptionDefault (0x1)
   location: kCGSessionEventTap
       mask: kCGEventKeyDown | kCGEventKeyUp | kCGEventFlagsChanged (0x1c00)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 1957747793:
    enabled: false
    process: universalaccessd (331)
    options: kCGEventTapOptionDefault (0x1)
   location: kCGSessionEventTap
       mask: kCGEventMouseMoved | kCGEventLeftMouseDragged | kCGEventRightMouseDragged | kCGEventOtherMouseDragged (0x80000e0)
    latency: min=0.000ms avg=0.000ms max=0.000ms

- 1714636915:
    enabled: true
    process: universalaccessd (331)
    options: kCGEventTapOptionDefault (0x1)
   location: kCGSessionEventTap
       mask: NX_SYSDEFINED | NX_ZOOM (0x10204000)
    latency: min=0.000ms avg=0.000ms max=0.000ms
```
