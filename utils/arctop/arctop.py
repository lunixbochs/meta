from dataclasses import dataclass
from typing import Dict, List
import argparse
import sys
import time

DEFAULT_KEYS = [
    'hits',
    'misses',
    'size',
    'l2_hits',
    'l2_misses',
    'l2_size',
]

# suffixes / keys that are rendered as bytes
BYTE_SUFFIXES = ('_bytes', '_asize', '_size', '_min', '_max')
BYTE_KEYS = {'c', 'p', 'size'}

@dataclass
class Snapshot:
    ts: float
    stats: Dict

    def __getitem__(self, key: str) -> int:
        return self.stats[key]

    def __getattr__(self, key: str) -> int:
        try: return self.stats[key]
        except KeyError: raise AttributeError(key)

def diff(a: Snapshot, b: Snapshot) -> Snapshot:
    diff = {key: b.stats[key] - a.stats[key] for key in b.stats}
    return Snapshot(b.ts - a.ts, diff)

def unit_scale(number: float, byte_scale: bool=False, append: str=''):
    unit = 1000
    suffixes = ' kmbtq'
    if byte_scale:
        unit = 1024
        suffixes = 'BKMGTEZY'

    acc = 1
    scales = []
    for suffix in suffixes:
        scales.append((acc, suffix.strip()))
        acc *= unit

    for scale, suffix in reversed(scales):
        if abs(number) >= scale:
            return f"{number / scale:.2f}{suffix}{append}"
    return f"{number:.2f}{append}"

class Stats:
    history: List[Snapshot]
    first: Snapshot

    def __init__(self):
        self.history = []
        self.first = self.update()

    def update(self) -> Snapshot:
        now = time.perf_counter()
        stats = {}
        with open('/proc/spl/kstat/zfs/arcstats', 'r') as f:
            data = f.read().strip()
        for line in data.split('\n')[2:]:
            name, _, value = line.split()
            stats[name] = int(value)

        snapshot = Snapshot(now, stats)
        self.history.append(snapshot)
        self.history = self.history[-300:]
        return snapshot

    def display(self, a: Snapshot, b: Snapshot, fields: List[str]):
        elapsed  = diff(self.first, b)
        interval = diff(a, b)
        rows = []
        rows.append((
            'cat',
            'key',
            'raw',
            'abs',
            'run',
            'run/s',
            '|',
            'int',
            'int/s',
        ))
        if not fields:
            fields = interval.stats.keys()
        for key in fields:
            byte_scale = (key in BYTE_KEYS or key.endswith(BYTE_SUFFIXES))
            if '_' in key:
                cat, keyname = key.split('_', 1)
            else:
                cat, keyname = '', key

            avalue = b[key]
            evalue = elapsed[key]
            ivalue = interval[key]
            eps    = evalue / (elapsed.ts + 1e-9)
            ips    = ivalue / (interval.ts + 1e-9)
            rows.append((
                cat,
                keyname,
                str(avalue),
                unit_scale(avalue, byte_scale=byte_scale, append=''  ),
                unit_scale(evalue, byte_scale=byte_scale, append=''  ),
                unit_scale(eps,    byte_scale=byte_scale, append='/s'),
                '|',
                unit_scale(ivalue, byte_scale=byte_scale, append=''  ),
                unit_scale(ips,    byte_scale=byte_scale, append='/s'),
            ))

        col_pad = [len(max(col, key=lambda x: len(x))) for col in zip(*rows)]
        sys.stdout.write('\033[H')
        sys.stdout.flush()
        for i, row in enumerate(rows):
            print('\033[K' + (' '.join([
                col.rjust(pad)
                for j, (col, pad) in enumerate(zip(row, col_pad))
            ])))
        sys.stdout.write('\033[0J')
        sys.stdout.flush()

    def top(self, interval: float, fields=None):
        if fields is None:
            fields = DEFAULT_KEYS
        last_snapshot = self.update()
        self.display(last_snapshot, last_snapshot, fields)
        while True:
            time.sleep(1)
            snapshot = self.update()
            if snapshot.ts - last_snapshot.ts > interval:
                self.display(last_snapshot, snapshot, fields)
                last_snapshot = snapshot

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', help='interval',         type=int, default=5)
    parser.add_argument('-a', help='print all fields', action='store_true')
    parser.add_argument('-f', help='fields',           type=str, default=','.join(DEFAULT_KEYS))
    args = parser.parse_args()

    stats = Stats()
    stats.top(interval=args.d, fields=args.f.split(',') if not args.a else ())
