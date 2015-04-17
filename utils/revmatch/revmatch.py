from collections import defaultdict
from contextlib import contextmanager
import os
import shutil
import subprocess
import sys
import tempfile

SvnMatch = None
HgMatch = None

@contextmanager
def tmpdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

def call(*args, **kwargs):
    stderr = kwargs.get('stderr')
    if stderr:
        stderr = subprocess.PIPE
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
    o1, o2 = p.communicate('')
    o = (o1 or '') + (o2 or '')
    if p.poll() and kwargs.get('throw') != False:
        print o
        raise subprocess.CalledProcessError(p.poll(), args, o)
    return o

def diff(a, b):
    excludes = ['--exclude={}'.format(t) for t in repo_types]
    return call('diff', '-r', a, b, *excludes, throw=False)

class Matcher:
    def __init__(self, repo):
        self.repo = repo

class GitMatch(Matcher):
    def clone(self, target):
        call('git', 'clone', self.repo, target, stderr=True)

    def revs(self):
        with tmpdir() as tmp:
            self.clone(tmp)
            revs = call('git', '-C', tmp, 'log', '--pretty=format:%H').split('\n')
            total = len(revs)
            for rev in revs:
                call('git', '-C', tmp, 'checkout', rev, stderr=True)
                yield rev, tmp, total

repo_types = {
    '.git': ('Git', GitMatch),
    '.svn': ('SVN', SvnMatch),
    '.hg': ('Mercurial', HgMatch),
}

def detect_repo(repo):
    for folder, tup in repo_types.items():
        if os.path.exists(os.path.join(repo, folder)):
            return tup
    return 'unknown', None

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: {} <repo> <target>'.format(sys.argv[0])
        sys.exit(1)

    repo, target = sys.argv[1:3]
    repo_type, matcher = detect_repo(repo)
    if not matcher:
        print '{} is unsupported'.format(repo_type)
        sys.exit(1)

    matcher = matcher(repo)
    print 'Using {} backend.'.format(repo_type)
    matches = defaultdict(list)
    last = ''
    i = 0
    for rev, tmp, total in matcher.revs():
        i += 1
        sys.stdout.write(len(last) * '\b')
        last = '{} {}/{}'.format(rev, i, total)
        sys.stdout.write(last)
        sys.stdout.flush()

        d = diff(tmp, target)
        matches[len(d)].append(rev)
        if len(d) == 0:
            break
    print

    if not matches:
        print 'No revisions found.'
    else:
        print 'Best candidate(s):'.format(min(len(matches), 5))
        for k in sorted(matches.keys())[:5]:
            if k == 0:
                print '(Perfect match)',
            print 'Diff: {}, Hash: {}'.format(k, ', '.join(matches[k]))
