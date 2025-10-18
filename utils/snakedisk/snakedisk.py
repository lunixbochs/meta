# requires-python = ">=3.14t"
# dependencies = [
#     "tqdm",
#     "shishua",
# ]

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from shishua import SHISHUA
from tqdm import tqdm
import argparse
import functools
import json
import os
import random
import sys
import time
import traceback

@dataclass
class Device:
    path: str
    size: int
    limit: int
    read: int
    wrote: int
    errors: int
    seed: bytes
    state: str # reading | writing | done

@dataclass
class State:
    pbar: tqdm
    blocksize: int
    limit: int
    devices: dict[str, Device]
    save_path: Path | None

def wrap_exc[T](fn: Callable[T]) -> Callable[T]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            traceback.print_exc()
            raise
    return wrapper

@wrap_exc
def device_init(path: str, state: State):
    with open(path, "rb") as f:
        size = f.seek(0, os.SEEK_END)
    limit = size if not state.limit else min(size, state.limit)
    seed = path + "|" + os.urandom(8).hex()

    if path in state.devices:
        assert state.devices[path].size == size
    else:
        state.devices[path] = Device(
            path=path,
            size=size,
            limit=limit,
            read=0,
            wrote=0,
            errors=0,
            seed=seed,
            state="none",
        )

@wrap_exc
def device_work(device: Device, state: State) -> None:
    blocksize = state.blocksize

    rng = SHISHUA(device.seed)
    fd = os.open(device.path, os.O_WRONLY | os.O_DIRECT)
    with os.fdopen(fd, "wb", buffering=-1) as f:
        size = f.seek(0, os.SEEK_END)
        device.state = "writing"

        device.wrote -= device.wrote % blocksize
        buf = bytearray(blocksize)
        for i in range(0, device.wrote, blocksize):
            rng.fill(buf)

        f.seek(device.wrote, os.SEEK_SET)
        for i in range(device.wrote, device.limit, blocksize):
            rng.fill(buf)
            n = f.write(buf)
            device.wrote += n
        if device.wrote < device.limit:
            print(f"WARNING: {device.path} wrote short ({device.wrote} < {device.limit})", file=sys.stderr)

    rng = SHISHUA(device.seed)
    with open(device.path, "rb") as f:
        size = f.seek(0, os.SEEK_END)
        device.state = "reading"

        buf = bytearray(blocksize)
        device.read -= device.read % blocksize
        for i in range(0, device.read, blocksize):
            rng.fill(buf)

        f.seek(device.read, os.SEEK_SET)
        for i in range(device.read, device.limit, blocksize):
            n = f.readinto(buf)
            x = rng.random_raw(blocksize)
            if buf[:n] != x[:n]:
                device.errors += 1
                print(f"ERROR: {device.path} verify mismatch at {i}", file=sys.stderr)
            device.read += n
        if device.read < device.limit:
            print(f"WARNING: {device.path} read short ({device.read} < {device.limit})", file=sys.stderr)
    device.state = "done"

@wrap_exc
def refresh_loop(state: State) -> None:
    def save():
        j = {"devices": {path: asdict(d) for path, d in state.devices.items()}}
        with open(state.save_path, "w") as f:
            json.dump(j, f)

    last_save = time.perf_counter()
    while True:
        now = time.perf_counter()
        if state.save_path and now - last_save > 60.0:
            save()
            last_save = now

        devices = state.devices.values()
        state.pbar.n = sum(dev.read + dev.wrote for dev in devices)
        state.pbar.total = sum(dev.limit for dev in devices) * 2
        drives_reading = sum(dev.state == "reading" for dev in devices)
        drives_writing = sum(dev.state == "writing" for dev in devices)
        drives_done = sum(dev.state == "done" for dev in devices)
        state.pbar.set_postfix({
            "drives": f"{drives_writing}w+{drives_reading}r+{drives_done}/{len(state.devices)}",
            "errors": sum(dev.errors for dev in devices),
        })
        state.pbar.refresh()
        if drives_done == len(state.devices):
            save()
            break
        time.sleep(0.032)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--jobs", type=int, default=None)
    parser.add_argument("-b", "--blocksize", type=int, default=1024 * 1024)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("devices", nargs="+")
    args = parser.parse_args()

    devices = list(args.devices)
    random.shuffle(devices)

    state = State(
        pbar=None,
        blocksize=args.blocksize,
        limit=args.limit,
        devices={},
        save_path=Path(args.resume) if args.resume else None,
    )

    if state.save_path:
        try:
            devset = set(devices)
            with open(state.save_path) as f:
                j = json.load(f)
                state.devices = {path: Device(**d) for path, d in j["devices"].items() if path in devset}
        except FileNotFoundError:
            pass

    initial = sum(dev.read + dev.wrote for dev in state.devices.values())
    with tqdm(unit_scale=True, unit="B", unit_divisor=1024, dynamic_ncols=True, initial=initial) as pbar:
        state.pbar = pbar

        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for _ in pool.map(device_init, args.devices, [state] * len(args.devices)):
                pass
            pool.submit(refresh_loop, state)
            for _ in pool.map(device_work, state.devices.values(), [state] * len(args.devices)):
                pass

if __name__ == "__main__":
    main()
