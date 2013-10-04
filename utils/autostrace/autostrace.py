#!/usr/bin/python
import os, time, sys
mypid = str(os.getpid())

if len(sys.argv) < 3:
    print 'Usage: ./autostrace.py [username] [process] (extra strace args)'
    sys.exit(1)

username = sys.argv[1]
process = sys.argv[2]

args = ''
if len(sys.argv) > 3:
    args = ' ' + ' '.join(sys.argv[2:])

already = [mypid]
while True:
    ps = os.popen('\ps -u "%s" -o pid,command | tail -n+2 | grep %s' % (username, process)).read()
    for line in ps.strip().split('\n'):
        if not line.strip(): continue
        pid, command = line.split(None, 1)
        if pid in already: continue
        print 'watching %s' % pid
        already.append(pid)
        os.system(('strace %s -p %s -o strace_%s.log &' % (args, pid, pid)))

    time.sleep(0.05)
