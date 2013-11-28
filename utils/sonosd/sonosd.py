#!/usr/bin/env python

import redis
from soco import SoCo, SonosDiscovery
import threading
import time

EXCLUDE = []


def get_devices():
    ips = set()
    for ip in SonosDiscovery().get_speaker_ips():
        ips.add(ip)

    return [SoCo(ip) for ip in ips]


def find_master(devices):
    for d in devices:
        if d.get_speaker_info()['zone_name'].lower() == 'master':
            return d

    return sorted(devices, lambda d: d.get_speaker_info()['zone_name'])[0]


class Volume(object):
    def __init__(self, device):
        self.device = device
        self.state = device.volume()
        self.last = time.time()
        self.lock = threading.RLock()

    @property
    def volume(self):
        now = time.time()
        if self.last < now - 5:
            self.last = now
            self.state = self.device.volume()
        return self.state

    @volume.setter
    def volume(self, new):
        self.last = time.time()
        self.state = new
        self.async_volume(new)

    def async_volume(self, new):
        def change(new):
            with self.lock:
                self.device.volume(new)
        threading.Thread(target=change, args=(new,)).start()


class Daemon:
    def __init__(self):
        self.volume = 0
        self.volume_lock = threading.RLock()

    def volume_thread(self):
        devices = [Volume(d) for d in self.devices]
        while True:
            time.sleep(0.05)
            with self.volume_lock:
                change = self.volume
                self.volume = 0

            if not change:
                continue

            volumes = [d.volume for d in devices]
            if any((v == 0 and change < 0) or (v == 100 and change > 0) for v in volumes):
                continue

            for d in devices:
                d.volume += change

    def change_volume(self, by):
        with self.volume_lock:
            self.volume += by

    def pump(self):
        self.devices = [
            d for d in get_devices()
            if d.get_speaker_info().get('zone_name').lower() not in EXCLUDE
        ]
        self.sonos = find_master(self.devices)
        thread = threading.Thread(target=self.volume_thread)
        thread.daemon = True
        thread.start()

        print 'connected'

        self.redis = redis.StrictRedis()
        ps = self.redis.pubsub()
        ps.subscribe('sonos')
        for item in ps.listen():
            if item['type'] == 'message':
                self.handle(item['data'])

    def handle(self, cmd):
        sonos = self.sonos
        if cmd == 'play':
            state = sonos.get_current_transport_info() or {}
            if state.get('current_transport_state') == 'PAUSED_PLAYBACK':
                sonos.play()
            else:
                sonos.pause()
        elif cmd == 'vol_up':
            self.change_volume(1)
        elif cmd == 'vol_down':
            self.change_volume(-1)
        elif cmd == 'next':
            self.sonos.next()
        elif cmd == 'prev':
            self.sonos.previous()

if __name__ == '__main__':
    Daemon().pump()
