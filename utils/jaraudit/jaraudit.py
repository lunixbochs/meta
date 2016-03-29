#!/usr/bin/env python
from collections import defaultdict
from xml.dom.minidom import parse as parseXML
import fnmatch
import json
import os
import re
import sys
import zipfile

try:
    import yaml
except ImportError:
    print "PyYAML not found."
    print "`pip install pyyaml`"
    print
    print "If you don't have pip:"
    print "Grab a tarball: https://pypi.python.org/pypi/PyYAML"
    print "  tar -xf PyYAML*.tar.gz"
    print "  mv PyYAML*/lib/yaml ."
    sys.exit(1)

def find(base, *patterns):
    for root, dirs, files in os.walk(base):
        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern):
                    yield os.path.join(root, name)

def name_match(a, b):
    if a == b or a in b:
        return True
    return False

class VersionMatcher:
    def __init__(self, versions):
        self.raw = versions
        self.criteria = [
            [self.split(v) for v in version.split(',')]
            for version in versions
        ]

    @staticmethod
    def split(v):
        sign = '='
        m = re.match('^([><]=?)(.*?)$', v)
        if m:
            sign, v = m.groups()
        out = []
        for sub in v.split('.'):
            if sub.isdigit():
                out.append(int(sub))
            else:
                out.append(sub)
        return sign, tuple(out)

    @staticmethod
    def satisfies(criteria, version):
        signs = {
            '=': lambda a, b: a[:len(b)] == b[:len(a)],
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
        }
        for sign, match in criteria:
            if not signs[sign](version, match):
                return False
        return True

    def match(self, version):
        _, version = self.split(version)
        for c in self.criteria:
            if self.satisfies(c, version):
                return True
        return False

    def __repr__(self):
        return "<VersionMatcher '{0}'>".format(self.raw)

def version_match(v, artifact):
    version = VersionMatcher(artifact.get('version', []))
    fixedin = VersionMatcher(artifact.get('fixedin', []))
    if version.match(v) and not fixedin.match(v):
        return True
    return False

first_dedup = set()

def check(db, package, version):
    global first_dedup
    out = []
    if not package.strip():
        return out
    for artifact in db['affected']:
        _id = artifact['artifactId']
        if name_match(package, _id):
            if version_match(version, artifact):
                out.append({
                    'package': package,
                    'version': version,
                    'db': db,
                })
                if ((package, version)) in first_dedup:
                    continue
                first_dedup.add((package, version))
                print >>sys.stderr, 'Found:', package, version, 'CVE-' + db['cve'],
                if package != _id:
                    print >>sys.stderr, '(WARNING: fuzzy "%s" != "%s")' % (package, _id),
                print >>sys.stderr
    return out

def load(yml):
    with open(yml, 'r') as f:
        return yaml.load(f)

def search(paths):
    for path in paths:
        for match in find(path, '*.jar', 'pom.xml'):
            try:
                if os.path.basename(match) == 'pom.xml':
                    x = parseXML(match)
                    deps = x.getElementsByTagName('dependency')
                    for d in deps:
                        artifact = d.getElementsByTagName('artifactId')[0].childNodes[0].data
                        version = d.getElementsByTagName('version')
                        if version:
                            try:
                                version = version[0].childNodes[0].data
                                m = re.match(r'^\$\{(.+)\}$', version)
                                if m:
                                    lookup = m.group(1)
                                    version = x.getElementsByTagName(lookup)[0].childNodes[0].data
                            except Exception:
                                continue
                            yield match, artifact, version
                    continue

                filename = os.path.splitext(os.path.basename(match))[0].strip()
                version = None
                try:
                    zf = zipfile.ZipFile(match, 'r')
                    try:
                        f = zf.open('META-INF/MANIFEST.MF')
                        contents = f.read()
                    except KeyError:
                        continue
                    finally:
                        zf.close()
                    if 'Implementation-Version: ' in contents:
                        version = contents.split('Implementation-Version: ', 1)[1].split('\n', 1)[0].strip()
                except zipfile.BadZipfile:
                    version = filename.split('-', 1)[1]

                if version is not None:
                    if '"' in version:
                        version = version.split('"', 3)[1]
                    version = version.split(' ', 1)[0].split('+', 1)[0]
                    name = filename.split(version, 1)[0].split('_', 1)[0].rstrip('-_.')
                    yield match, name, version
            except Exception:
                import traceback
                traceback.print_exc()

def shellquote(s):
    return "'%s'" % s.replace('\\', '\\\\').replace("'", "\\'")

def usage():
    print 'Usage: %s [-j,--json] path [path...]' % os.path.basename(sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':
    base = os.path.dirname(str(__file__))
    if base == '.':
        base = ''

    language = 'java'
    db = os.path.join(base, 'victims-cve-db', 'database', language)
    if not os.path.exists(db):
        print "victims-cve-db not found."
        print
        if base:
            print "pushd %s" % shellquote(base)
        print "wget https://github.com/victims/victims-cve-db/archive/master.tar.gz"
        print "tar -xf master.tar.gz; mv victims-cve-db-master victims-cve-db"
        if base:
            print "popd"
        sys.exit(1)

    if len(sys.argv) < 2:
        usage()

    j = False
    if sys.argv[1] in ('-j', '--json'):
        j = True
        if len(sys.argv) < 3:
            usage()

    dbs = list([load(y) for y in find(db, '*.yaml')])
    first = True

    results = []
    file_count = 0
    for path, name, version in search((sys.argv[1:]) or ('.',)):
        file_count += 1
        for db in dbs:
            result = check(db, name, version)
            for r in result:
                r['path'] = path
            results.extend(result)

    out = defaultdict(list)
    for r in results:
        out[r['package']].append(r)

    if out:
        print >>sys.stderr
    for key, items in sorted(out.items()):
        dedup = set()
        if j:
            print json.dumps(items)
        else:
            first = items[0]
            print 'Package:', first['package']
            print 'Version:', first['version']
            print 'Path:   ', first['path']
            for item in items:
                db = item['db']
                if db['cve'] in dedup:
                    continue
                dedup.add(db['cve'])
                print '- Title:', db['title']
                print '    CVE:', 'CVE-' + db['cve']
                print '    URL:', db['references'][0]
                print
    print >>sys.stderr, '(%d) files found. (%d) vulnerable.' % (file_count, len(out))
