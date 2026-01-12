# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "tqdm",
#     "shishua @ git+https://github.com/lunixbochs/shishua-python.git",
# ]
# ///

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from shishua import SHISHUA
from tqdm import tqdm
from typing import Callable
import argparse
import functools
import json
import logging
import os
import random
import subprocess
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
    seed: str
    state: str # reading | writing | done
    serial: str = ""
    found: bool = False

@dataclass
class State:
    pbar: tqdm
    blocksize: int
    limit: int
    seeksize: int
    devices: dict[str, Device]
    save_path: Path | None
    errors: int

class SeekSHUA:
    rng: SHISHUA

    def __init__(self, *, seed: str, chunksize: int, pos: int = 0):
        self.seed = seed
        self.chunksize = chunksize
        self.pos = pos
        self.reseed()

    def reseed(self) -> None:
        chunk = self.pos // self.chunksize
        self.rng = SHISHUA(f"{self.seed}|chunk:{chunk}")

        chunkoff = self.pos % self.chunksize
        buf = bytearray(1 * 1024 * 1024)
        for i in range(0, chunkoff, len(buf)):
            need = min(len(buf), chunkoff - i)
            self.rng.fill(buf[:need]) # slicing here copies, but we're throwing buf away anyway

    def fill(self, buf: bytearray) -> None:
        mbuf = memoryview(buf)
        pos = 0
        need = len(buf)
        while need:
            feed = min(need, self.chunksize - self.pos % self.chunksize)
            self.rng.fill(mbuf[pos:pos + feed])
            need -= feed
            pos += feed
            self.pos += feed
            if self.pos % self.chunksize == 0:
                self.reseed()

def wrap_exc[T: Callable](fn: T) -> T:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            traceback.print_exc()
            raise
    return wrapper

@functools.cache
def read_path_to_serial() -> dict[str, str]:
    try:
        p = subprocess.run(["lsblk", "-pdno", "name,serial"], capture_output=True, check=True)
        return dict(row.split() for row in p.stdout.decode().strip().split("\n"))
    except Exception:
        logging.exception("failed to read serials with lsblk, falling back to path tracking")
    return {}

@wrap_exc
def device_init(path: str, state: State):
    path = os.path.realpath(path, strict=True)
    try:
        with open(path, "rb") as f:
            size = f.seek(0, os.SEEK_END)
    except OSError as e:
        logging.error(f"device open error {path}: {e!r}")
        state.errors += 1
        return

    limit = size if not state.limit else min(size, state.limit)
    seed = path + "|" + os.urandom(8).hex()

    path_to_serial = read_path_to_serial()
    serial = path_to_serial.get(path)
    path_key = f"path:{path}"
    serial_key = f"serial:{serial}" if serial else None
    ideal_key = serial_key or path_key

    # upgrade path device to ideal device key
    if (device := state.devices.pop(path, None)) is not None:
        state.devices[ideal_key] = device

    elif (device := state.devices.pop(path_key, None)) is not None:
        state.devices[ideal_key] = device

    elif (device := state.devices.get(ideal_key)) is None:
        device = Device(
            path=path,
            size=size,
            limit=limit,
            read=0,
            wrote=0,
            errors=0,
            seed=seed,
            state="none",
        )
        state.devices[ideal_key] = device

    assert device.size == size
    if serial is not None:
        device.serial = serial
    device.found = True

@wrap_exc
def device_work(device: Device, state: State) -> None:
    if not device.found:
        return

    try:
        blocksize = state.blocksize

        try:
            fd = os.open(device.path, os.O_WRONLY | os.O_DIRECT)
        except OSError as e:
            device.errors += 1
            logging.exception(f"device error: {device.path} {e!r}")
            return

        with os.fdopen(fd, "wb", buffering=-1) as f:
            size = f.seek(0, os.SEEK_END)
            device.state = "writing"

            rng = SeekSHUA(seed=device.seed, chunksize=state.seeksize, pos=device.wrote)
            buf = bytearray(blocksize)
            f.seek(device.wrote, os.SEEK_SET)
            for i in range(device.wrote, device.limit, blocksize):
                rng.fill(buf)
                n = f.write(buf)
                device.wrote += n
            if device.wrote < device.limit:
                logging.warning(f"{device.path} wrote short ({device.wrote} < {device.limit})")

        rng = SeekSHUA(seed=device.seed, chunksize=state.seeksize, pos=device.read)
        with open(device.path, "rb") as f:
            size = f.seek(0, os.SEEK_END)
            device.state = "reading"

            fbuf = bytearray(blocksize)
            rbuf = bytearray(blocksize)
            f.seek(device.read, os.SEEK_SET)
            for i in range(device.read, device.limit, blocksize):
                n = f.readinto(fbuf)
                rng.fill(rbuf)
                if fbuf[:n] != rbuf[:n]:
                    device.errors += 1
                    logging.error(f"{device.path} verify mismatch at {i}")
                device.read += n
            if device.read < device.limit:
                logging.warning(f"{device.path} read short ({device.read} < {device.limit})")
        device.state = "done"
    except Exception as e:
        raise Exception(f"device error: {device.path}") from e

@wrap_exc
def refresh_loop(state: State) -> None:
    def save():
        if not state.save_path:
            return
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
        drives_missing = sum(not dev.found for dev in devices)
        missing_extra = f"(-{drives_missing}!)" if drives_missing else ""
        state.pbar.set_postfix({
            "drives": f"{drives_writing}w+{drives_reading}r+{drives_done}/{len(state.devices)}" + missing_extra,
            "errors": sum(dev.errors for dev in devices) + state.errors,
        })
        state.pbar.refresh()
        if drives_done == len(state.devices):
            save()
            break
        time.sleep(0.032)

def parse_size(spec: str | None) -> int | None:
    if not spec:
        return None
    suffixes = "kmgtpe"
    spec = spec.lower()
    for i, s in enumerate(suffixes, start=1):
        if spec.endswith(s):
            scale = 1024 ** i
            spec = spec.removesuffix(s)
            size = int(spec) * scale
            break
    else:
        size = int(spec)
    assert size > 0
    return size

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--jobs", type=int, default=None)
    parser.add_argument("-b", "--blocksize", type=int, default=1024 * 1024)
    parser.add_argument("--limit", type=str, default=None)
    parser.add_argument("--seeksize", type=str, default="25g")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("devices", nargs="+")
    args = parser.parse_args()

    state = State(
        pbar=None,
        blocksize=args.blocksize,
        limit=parse_size(args.limit),
        devices={},
        save_path=Path(args.resume) if args.resume else None,
        seeksize=parse_size(args.seeksize),
        errors=0,
    )

    if state.save_path:
        try:
            devset = set(args.devices)
            with open(state.save_path) as f:
                j = json.load(f)
                state.devices = {key: Device(**d) for key, d in j["devices"].items()}
                for device in state.devices.values():
                    device.found = False
        except FileNotFoundError:
            pass

    initial = sum(dev.read + dev.wrote for dev in state.devices.values())
    with tqdm(unit_scale=True, unit="B", unit_divisor=1024, dynamic_ncols=True, initial=initial) as pbar:
        state.pbar = pbar

        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for _ in pool.map(device_init, args.devices, [state] * len(args.devices)):
                pass
            pool.submit(refresh_loop, state)

            devices = list(state.devices.values())
            finished_devs = [dev for dev in devices if dev.state == "done"]
            queued_devs = [dev for dev in devices if dev.state == "none"]
            active_devs = [dev for dev in devices if dev.state in ("reading", "writing")]
            random.shuffle(queued_devs)
            devices = finished_devs + queued_devs + active_devs

            for _ in pool.map(device_work, devices, [state] * len(devices)):
                pass

if __name__ == "__main__":
    main()
