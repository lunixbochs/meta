#!/usr/bin/env python
# copyright (c) 2011 Ryan Hileman
# released into the Public Domain for unlimited use without warranty

import struct

import os
import datetime
import time
from zipfile import ZipFile

class StructBuffer:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, fmt):
        size = struct.calcsize('>'+fmt)
        if self.pos + size >= len(self.data):
            raise IndexError

        ret = struct.unpack(fmt, self.data[self.pos:self.pos+size])
        self.pos += size
        return ret

    def seek(self, pos):
        self.pos = pos

class MacBinary:
    def __init__(self, filename = ''):
        self.filename = filename
        self.type = 0
        self.creator = 0
        self.flags = 0
        self.xpos = 0
        self.ypos = 0
        self.fid = 0
        self.protected = 0
        self.creation = 0
        self.modified = 0
        self.oid = 0

        self.data = ''
        self.res = ''

    @classmethod
    def decode(cls, data):
        head = StructBuffer(data[:128])

        head.seek(1)
        flen, = head.read('B')
        filename, = head.read('%is' % flen)
        bin = cls(filename)

        head.seek(65)
        bin.type, = head.read('I')
        bin.creator, = head.read('I')
        bin.flags, = head.read('B')

        head.seek(74)
        bin.xpos, = head.read('H')
        bin.ypos, = head.read('H')
        bin.fid, = head.read('H')
        bin.protected, = head.read('B')

        head.seek(83)
        datalen, = head.read('I')
        reslen, = head.read('I')

        bin.creation, = head.read('I')
        bin.modified, = head.read('I')

        head.seek(125)
        bin.oid, = head.read('H')

        bin.data = data[128:128+datalen]
        bin.res = data[128+datalen:128+datalen+reslen]

        return bin

    def encode(self):
        fmt = ''.join(('>', 'xB', '63s', '2IBx3H', 'Bx', '4I', '27x', 'H'))
        args = (
            len(self.filename), self.filename,
            self.type, self.creator, self.flags, self.xpos, self.ypos, self.fid,
            self.protected, len(self.data), len(self.res), self.creation, self.modified,
            self.oid
        )

        head = struct.pack(fmt, *args)

        dlen = len(self.data) + 128 - (len(self.data) % 128)
        rlen = len(self.res) + 128 - (len(self.res) % 128)

        return head + struct.pack('%is%is' % (dlen, rlen), self.data, self.res)

def unzip(filename):
    z = ZipFile(filename)
    names = z.namelist()
    for path in names:
        if path.startswith('__MACOSX/'):
            continue

        base, name = os.path.split(path)

        if name.startswith('._') and\
            '%s/' % name.replace('._', '', 1) in names:
            continue

        double = os.path.join('__MACOSX', base, '._' + name)
        if double in names:
            print '=> %s.bin' % path

            info = z.getinfo(path)

            bin = MacBinary(name)
            bin.data = z.open(path, 'r').read()
            bin.res = z.open(double, 'r').read()

            modified = datetime.datetime(*info.date_time)
            bin.modified = time.mktime(modified.timetuple())
            bin.created = time.time()

            if not os.path.exists(base):
                os.makedirs(base)

            with open('%s.bin' % path.rstrip('\r'), 'wb') as f:
                f.write(bin.encode())
        else:
            print '-> %s' % path
            z.extract(path)

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            unzip(arg)
    else:
        print 'Usage: macbinary.py <zipfile> [zipfile...]'
        print 'Extracts a .zip, creating MacBinary files from AppleDouble resource forks'
