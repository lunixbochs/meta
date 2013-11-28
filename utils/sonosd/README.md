sonosd
------

Redis-backed Sonos control daemon, with smooth volume control.

This depends on a running Redis server, and assumes your primary Sonos is called "Master".

Commands
-----

 - vol\_up
 - vol\_down
 - play (acts as play/pause)
 - next
 - prev


Usage
-----

From a command line:

    redis-cli publish sonos vol_up

From AppleScript (for the Griffin PowerMate control knob):

    do shell script "/usr/local/bin/redis-cli publish sonos vol_up"
