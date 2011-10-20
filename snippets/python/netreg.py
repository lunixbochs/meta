#!/usr/bin/env python

import os

class Registry:
	def __init__(self, host, username, password):
		self.cmd = 'net rpc registry -S %s -U "%s%%%s"' % (host, username, password)

	def call(self, cmd, *args):
		args = '"' + '" "'.join(args) + '"'
		shell = ' '.join((self.cmd, cmd, args))
		n, out, err = os.popen3(shell)
		return out.read()

	def join(self, *args):
		return '\\'.join(args)
	
	def enum(self, *base):
		base = self.join(*base)

		if base.count('HKEY_USERS') > 2: raise
		lines = self.call('enumerate', base)
		data = {}

		key = ''
		cur = {}
		for line in lines.split('\n'):
			if not line:
				if key: data[key] = cur
				key = ''
				cur = {}
				continue

			typ, value = line.strip().split('=', 1)
			typ, value = typ.strip(), value.strip()

			if typ == 'Keyname':
				key = value
			elif typ == 'Valuename':
				key = value
			
			cur[typ] = value

		if key: data[key] = cur
		return data

	def list(self, *base):
		return list(self.enum(*base))

	def get(self, key, name):
		return self.enum(key)[name]

	def set(self, key, name, typ, *values):
		return self.call('setvalue', key, name, typ, *values)

	def delete(self, key, name):
		lines = self.call('deletevalue', key, name)
		return lines

	def walk(self, base):
		tree = {}
		keys = self.enum(base)
		for key in keys:
			if not 'Value' in keys[key]:
				tree[key] = self.walk(base, key)

		return tree

if __name__ == '__main__':
	host = ''
	username = ''
	password = ''
	reg = Registry(host, username, password)
	for user in reg.enum('HKEY_USERS'):
		try:
			run = reg.join('HKEY_USERS', user, 'Software\\Microsoft\\Windows\\CurrentVersion\\Run')
			l = reg.list(run)
			if l:
				print l
				print reg.get(run, l[0])['Value']
				print reg.enum(run)
		except KeyError:
			continue

