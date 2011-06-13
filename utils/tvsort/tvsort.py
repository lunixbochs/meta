#!/usr/bin/python
# tv_sort.py
# detects and sorts tv shows automatically based on filename

import os
import shutil

import re
import xmlrpclib

words = r'([\w\.\- ]+?)'
spacers = re.compile(r'[\s_\-\.]+')
show_filename = re.compile(words + r'S?(\d+)[xE](\d+)', re.IGNORECASE)
word_match = re.compile('(%s+)' % words, re.IGNORECASE)
the_match = re.compile(r'(.*?)(, The)$', re.IGNORECASE)

date = r'(19\d{2}|2\d{3})'
date_match = re.compile(r' ?(\(%s\)|%s) ?' % (date, date))

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
	
	def rename(self, name, season, episode, ext='.avi'):
		epstr = 'S%02dE%02d' % (season, episode)
		target = self.naming % {'name':name, 'season':season, 'episode':episode, 'epstr':epstr} + ext
		return self.path, target
	
	def __repr__(self):
		return '<Folder "%s">' % self.name

def extract(path):
	first = os.listdir(path)
	for entry in first:
		if entry.endswith('.rar'):
			rar = os.path.join(path, entry)
			print 'Extracting: %s' % os.path.split(rar)[1],
			os.popen('unrar x -o- %s' % rar)
	
	second = os.listdir(path)
	for entry in second:
		if entry.endswith('.avi'):
			print '=> "%s"' % entry
			return entry
	else:
		print '- Nothing found :('

def move(path, filename, name, season, episode, folders, force_move, dry_run):
	copy = True
	for folder in folders:
		if folder.match(name):
			target_folder, target = folder.rename(name, season, episode)
			target_path, target_filename = os.path.split(os.path.join(target_folder, target))
			break
	else:
		print 'Skipped "%s" (example: %s)' % (name, filename)
		return True

	if not os.path.exists(target_path) and not dry_run:
		os.makedirs(target_path)

	if target_path == path:
		if target_filename == filename:
			return
	else:
		for existing in os.listdir(target_path):
			if existing.lower() == target_filename.lower():
				return
	print 
	print ('%s S%02dE%02d => %s' % (name, season, episode, target)),

	path = os.path.join(path, filename)
	if os.path.isdir(path) and not dry_run:
		cwd = os.getcwd()
		os.chdir(path)
		print 'extracting archive',
		entry = extract(path)
		os.chdir(cwd)
		if not entry:
			print 'no extracted file found.'
			return
		else:
			print 'success.'

		path = os.path.join(path, entry)
		copy = False

	target = os.path.join(target_folder, target)
	if dry_run:
		verb = copy and 'copy' or 'move'
		print
		print 'Would %s %s => %s' % (verb, path, target)
	else:
		if copy and not force_move:
			shutil.copyfile(path, target)
			print 'copied to target.'
		else:
			os.rename(path, target)
			print 'moved to target.'

def run(source, targets, force_move=False, dry_run=False):
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
		seeding = x.download_list('seeding')

		for torrent in seeding:
			files.add(x.d.get_base_path(torrent))
	else:
		for filename in os.listdir(source):
			files.add(os.path.join(source, filename))
	
	skip = set()
	for path in sorted(files):
		path, filename = os.path.split(path)
		match = show_filename.match(filename)
		if match:
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
			
			skip_name = move(path, filename, name, int(season), int(episode), folders, force_move, dry_run)
			if skip_name:
				skip.add(name)

def usage():
	print 'Usage: ./tv_sort.py [flags] <source> <target folder> [target folder] [target folder]...'
	print 'Sorts TV shows into folders.'
	print '  Flags:'
	print '    -m, --move: force moving of normal files (extracted files are always moved)'
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
	for arg in sys.argv[1:]:
		if arg in ('-m', '--move'):
			force_move = True
		elif arg in ('-d', '--dry'):
			dry_run = True
		elif arg in ('-md', '-dm'):
			force_move, dry_run = True, True
		else:
			args.append(arg)

	if len(args) < 2:
		usage()
	else:
		run(args[0], args[1:], force_move=move, dry_run=dry_run)
