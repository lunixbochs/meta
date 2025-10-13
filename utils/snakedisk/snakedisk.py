# requires-python = ">=3.14t"
# dependencies = [
#     "tqdm",
#     "shishua",
# ]

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from shishua import SHISHUA
from tqdm import tqdm
import argparse
import os
import random
import sys
import time

@dataclass
class State:
    pbar: tqdm
    blocksize: int
    limit: int

    bytes_written: int = 0
    bytes_read: int = 0
    bytes_total: int = 0

    drives_reading: int = 0
    drives_writing: int = 0
    drives_done: int = 0
    drives_total: int = 0
    errors: int = 0
    last_tick: float = 0.0

    def refresh(self):
        now = time.perf_counter()
        if now - self.last_tick < 0.032:
            return
        self.last_tick = now

        self.pbar.n = self.bytes_written + self.bytes_read
        self.pbar.total = self.bytes_total
        self.pbar.set_postfix({
            "drives": f"{self.drives_writing}w+{self.drives_reading}r+{self.drives_done}/{self.drives_total}",
            "errors": self.errors,
        })
        self.pbar.refresh()

def device_init(device: str, state: State):
    state.drives_total += 1
    with open(device, "rb") as f:
        size = f.seek(0, os.SEEK_END)
    limit = size if not state.limit else min(size, state.limit)
    state.bytes_total += limit * 2

def device_work(device: str, state: State):
    blocksize = state.blocksize

    seed = device + "|" + os.urandom(8).hex()
    rng = SHISHUA(seed)
    fd = os.open(device, os.O_WRONLY | os.O_DIRECT)
    with os.fdopen(fd, "wb", buffering=-1) as f:
        size = f.seek(0, os.SEEK_END)
        f.seek(0, os.SEEK_SET)
        limit = size if not state.limit else min(size, state.limit)
        state.drives_writing += 1

        count = 0
        for i in range(0, limit, blocksize):
            x = rng.random_raw(blocksize)
            n = f.write(x)
            count += n
            state.bytes_written += n
            state.refresh()
        if count < limit:
            print(f"WARNING: {device} wrote short ({n})", file=sys.stderr)
        state.drives_writing -= 1

    rng = SHISHUA(seed)
    with open(device, "rb") as f:
        size = f.seek(0, os.SEEK_END)
        f.seek(0, os.SEEK_SET)
        state.drives_reading += 1

        count = 0
        buf = bytearray(blocksize)
        for i in range(0, limit, blocksize):
            n = f.readinto(buf)
            x = rng.random_raw(blocksize)
            if buf[:n] != x[:n]:
                state.errors += 1
                print(f"ERROR: {device} verify mismatch at {i}", file=sys.stderr)

            count += n
            state.bytes_read += n
            state.refresh()
        if count < limit:
            print(f"WARNING: {device} read short ({n})", file=sys.stderr)
        state.drives_reading -= 1
    state.drives_done += 1
    state.refresh()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--jobs", type=int, default=None)
    parser.add_argument("-b", "--blocksize", type=int, default=1024 * 1024)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("devices", nargs="+")
    args = parser.parse_args()

    devices = list(args.devices)
    random.shuffle(devices)

    with tqdm(unit_scale=True, unit="B", unit_divisor=1024, dynamic_ncols=True) as pbar:
        state = State(
            pbar=pbar,
            blocksize=args.blocksize,
            limit=args.limit,
        )

        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for _ in pool.map(device_init, args.devices, [state] * len(args.devices)):
                pass

            for _ in pool.map(device_work, args.devices, [state] * len(args.devices)):
                pass

if __name__ == "__main__":
    main()
