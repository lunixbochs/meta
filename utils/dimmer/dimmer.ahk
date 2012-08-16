; Dimmer.ahk
; by Ryan Hileman (lunixbochs@gmail.com)
; This script allows you to dim/undim screens using a hotkey
; Press your configured modifier + number key to dim/undim a monitor

;; config
; available modifiers:
; ^  ctrl
; <^ left ctrl
; >^ right ctrl

; !  alt
; <! left alt
; >! right alt

; +  shift
; <+ left shift
; >+ right shift

; #  windows logo
; ># right windows logo
; <# left windows logo

modifiers = ^!+

;; end config

#NoEnv
#NoTrayIcon
#Persistent
#SingleInstance

dxva2 := DllCall("LoadLibrary", Str, "dxva2.dll", "Ptr")

GetNumberOfPhysicalMonitorsFromHMONITOR := DllCall("GetProcAddress"
	, uint, dxva2
	, str, "GetNumberOfPhysicalMonitorsFromHMONITOR")

GetPhysicalMonitorsFromHMONITOR := DllCall("GetProcAddress"
	, uint, dxva2
	, str, "GetPhysicalMonitorsFromHMONITOR")

GetMonitorCapabilities := DllCall("GetProcAddress"
	, uint, dxva2
	, str, "GetMonitorCapabilities")

GetMonitorBrightness := DllCall("GetProcAddress"
	, uint, dxva2
	, str, "GetMonitorBrightness")

SetMonitorBrightness := DllCall("GetProcAddress"
	, uint, dxva2
	, str, "SetMonitorBrightness")

ToggleBrightness(hMon) {
	global
	; Find number of Physical Monitors
	DllCall(GetNumberOfPhysicalMonitorsFromHMONITOR, "int", hMon, "uint*", nMon)

	; Get Physical Monitor from handle
	VarSetCapacity(Physical_Monitor, (A_PtrSize ? A_PtrSize : 4) + 128, 0)

	DllCall(GetPhysicalMonitorsFromHMONITOR
		, "int", hMon   ; monitor handle
		, "uint", nMon   ; monitor array size
		, "int", &Physical_Monitor)   ; point to array with monitor

	hPhysMon := NumGet(Physical_Monitor)

	DllCall(GetMonitorBrightness, "int", hPhysMon, "uint*", minBright, "uint*", curBright, "uint*", maxBright)

	if (curBright > minBright) {
		DllCall(SetMonitorBrightness, "int", hPhysMon, "uint", minBright)
	} else {
		DllCall(SetMonitorBrightness, "int", hPhysMon, "uint", maxBright)
	}
}

EnumMonitor(hMonitor, hdcMonitor, lprcMonitor, dwData) {
	static mCount = 0
	mCount += 1
	if (dwData = mCount) {
		ToggleBrightness(hMonitor)
		mCount = 0
		return 0
	}
	return 1
}

callback := RegisterCallback("EnumMonitor")

AdjustBrightness(mon) {
	global callback
	res := DllCall("EnumDisplayMonitors"
		, "int", 0
		, "int", 0
		, "ptr", callback
		, "int", mon)
}

; hopefully you don't have more than 9 monitors and still care about individual brightness control ;)
Loop, 9 {
	Hotkey, %modifiers%%A_Index%, HandleKey
}

OnExit Cleanup
return

HandleKey:
key := SubStr(A_ThisHotkey, 0, 1)
AdjustBrightness(key)
return

Cleanup:
DllCall("FreeLibrary", "Ptr", dxva2)
ExitApp
