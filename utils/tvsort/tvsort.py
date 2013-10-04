#!/usr/bin/python
# tv_sort.py
# detects and sorts tv shows automatically based on filename

import os
import shutil

import re
import xmlrpclib

words = r'([\w\.\- ]+?)'
spacers = re.compile(r'[\s_\-\.]+')
show_filename = re.compile(words + r'S(\d+)E(\d+)', re.IGNORECASE)
show_filename_2 = re.compile(words + r'(\d+)x(\d+)', re.IGNORECASE)
show_filename_3 = re.compile(words + r'(\d+?)(\d{1,2})', re.IGNORECASE)
word_match = re.compile('(%s+)' % words, re.IGNORECASE)
the_match = re.compile(r'(.*?)(, The)$', re.IGNORECASE)
hd_match = re.compile(r'(720p|1080p)')

date = r'(19\d{2}|2\d{3})'
date_match = re.compile(r' ?(\(%s\)|%s) ?' % (date, date))

extensions = ('.mp4', '.avi', '.mkv', '.m4v', '.wmv', '.mpg', '.mpeg')

def forward_the(name):
    if the_match.match(name):
        return the_match.sub(r'The \1', name)
    return name

class Auto(dict):
    def __init__(self, path):
        self.path = path
        if os.path.isfile(path):
            f = open(path, 'r')
            for line in f.readlines():
                line = line.strip()
                if line and ':' in line:
                    key, value = line.split(':', 1)
                    key, value = key.strip(), value.strip()
                    value = value.strip('\'"')
                    self[key] = value

class Folder:
    def __init__(self, path):
        self.path = path
        self.name = os.path.split(path)[1]
        self.regex = None
        self.naming = 'Season %(season)s/%(name)s %(epstr)s'

        auto = Auto(os.path.join(path, '.auto'))
        if 'regex' in auto:
            try:
                self.regex = re.compile(auto['regex'], re.IGNORECASE)
            except:
                print 'error parsing regex for: %s' % auto.path
        if 'name' in auto:
            self.naming = auto['name']

        if not self.regex:
            self.regex = re.compile(word_match.match(self.name).group(), re.IGNORECASE)

    def match(self, name):
        match = self.regex.search(name)
        if match:
            return True

        return False

    def rename(self, name, season, episode, hd=None, ext='.avi'):
        epstr = 'S%02dE%02d' % (season, episode)
        target = self.naming % {'name':name, 'season':season, 'episode':episode, 'epstr':epstr}
        if hd:
            target = '%s (%s)' % (target, hd)

        return self.path, target + ext

    def __repr__(self):
        return '<Folder "%s">' % self.name

def extract(path):
    cwd = os.getcwd()
    os.chdir(path)
    first = os.listdir('.')
    for entry in first:
        if entry.endswith('.rar'):
            print 'Extracting: %s' % entry,
            os.popen('unrar x -o- %s' % entry)
            break

    second = os.listdir('.')
    for entry in second:
        ext = os.path.splitext(entry)[1]
        if ext in extensions:
            print '=> "%s"' % entry
            os.chdir(cwd)
            return entry, ext
    else:
        print '- Nothing found :('
        os.chdir(cwd)
        return None, None

def move(path, filename, name, season, episode, folders, force_move=False, dry_run=False, link=False, hd=None, ext='.avi'):
    copy = True

    for folder in folders:
        if folder.match(name):
            break
    else:
        print 'Skipped "%s" (example: %s)' % (name, filename)
        return True

    target_folder, target = folder.rename(name, season, episode, hd, ext)

    no_ext = os.path.splitext(os.path.join(target_folder, target))[0]
    test_base = os.path.split(no_ext)[0]
    for test in extensions:
        test_path = no_ext + test
        test_filename = os.path.split(test_path)[1]

        if not os.path.exists(test_base):
            if not dry_run:
                os.makedirs(test_base)

            break
        else:
            if test_base == path:
                if test_filename == filename:
                    return
            else:
                for existing in os.listdir(test_base):
                    if existing.lower() == test_filename.lower():
                        return

    path = os.path.join(path, filename)
    if os.path.isdir(path) and not dry_run:
        entry, ext = extract(path)
        if not entry:
            print 'no extracted file found.'
            return
        else:
            print 'success.'

        path = os.path.join(path, entry)
        copy = False

    target_folder, target = folder.rename(name, season, episode, hd, ext)
    target_path, target_filename = os.path.split(os.path.join(target_folder, target))

    print
    print ('%s S%02dE%02d => %s' % (name, season, episode, target)),

    target = os.path.join(target_folder, target)
    if dry_run:
        verb = copy and 'copy' or 'move'
        print
        print 'Would %s %s => %s' % (verb, path, target)
    else:
        if copy and not force_move:
            if link:
                try:
                    os.link(path, target)
                    print 'linked to target'
                except IOError:
                    link = False

            if not link:
                shutil.copyfile(path, target)
                print 'copied to target.'
        else:
            os.rename(path, target)
            print 'moved to target.'

def run(source, targets, force_move=False, dry_run=False, link=False):
    print
    print 'If anything is skipped, make sure the show name exists as a folder in one of the targets'
    print 'You can also use .auto files (see the readme) to change the show matching a folder'
    folders = []
    for target in targets:
            if not os.path.isdir(target): continue
            for folder in os.listdir(target):
                    path = os.path.join(target, folder)
                    if not os.path.isdir(path): continue

                    folders.append(Folder(path))

    files = set()
    if source.startswith('rtorrent://'):
        rtorrent_uri = source.replace('rtorrent', 'http')
        x = xmlrpclib.ServerProxy(rtorrent_uri)
        seeding = x.download_list()

        for torrent in seeding:
            if not x.d.complete(torrent): continue
            files.add(x.d.get_base_path(torrent))
    else:
        for filename in os.listdir(source):
            files.add(os.path.join(source, filename))

    skip = set()
    for path in sorted(files):
        path, filename = os.path.split(path)

        cleaned_filename = hd_match.sub('', filename)
        match1 = show_filename.match(cleaned_filename)
        match2 = show_filename_2.match(cleaned_filename)
        match3 = show_filename_3.match(cleaned_filename)
        hd = hd_match.search(filename)
        if hd:
            hd = hd.group()

        matches = [m for m in (match1, match2, match3) if m]

        if matches:
            match = matches[0]
            name, season, episode = match.groups()

            # replace all spacer chars with spaces
            name = spacers.sub(' ', name)
            # strip the year from the name
            name = date_match.sub(' ', name)
            name = name.strip()
            first = name[0]
            if first == first.lower():
                name = ' '.join(word.capitalize() for word in name.split(' '))

            if name in skip: continue
            if name.endswith(' S'):
                # work around a bug when encountering full season downloads
                continue

            skip_name = move(path, filename, name, int(season), int(episode), folders, force_move, dry_run, link, hd)
            if skip_name:
                skip.add(name)

def usage():
    print 'Usage: ./tv_sort.py [flags] <source> <target folder> [target folder] [target folder]...'
    print 'Sorts TV shows into folders.'
    print '  Flags:'
    print '    -m, --move: force moving of normal files (extracted files are always moved)'
    print '    -l, --link: hardlink files instead of copying'
    print '    -d, --dry: dry run - only display what would be moved/copied'
    print '  Source options:'
    print '    * /path/to/folder'
    print '    * rtorrent://localhost/scgi_path'
    sys.exit(1)

if __name__ == '__main__':
    import sys

    args = []
    force_move = False
    dry_run = False
    link = False
    for arg in sys.argv[1:]:
        sort = None
        if arg.startswith('-'):
            sort = ''.join(sorted(arg))

        if arg in ('-m', '--move'):
            force_move = True
        elif arg in ('-d', '--dry'):
            dry_run = True
        elif arg in ('-l', '--link'):
            link = True
        elif sort:
            if re.match(r'-[mdv]{1,3}', sort):
                if 'm' in sort: force_move = True
                if 'd' in sort: dry_run = True
                if 'l' in sort: link = True
        else:
            args.append(arg)

    if len(args) < 2:
        usage()
    else:
        run(args[0], args[1:], force_move=force_move, dry_run=dry_run, link=link)
