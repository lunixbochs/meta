#!/usr/bin/env python

class Base:
	def __init__(self, possible):
		self.possible = set(possible)
		self.index = 0
	
	def current(self):
		return sorted(self.possible)[self.index]

	def next(self):
		value = self.current()
		self.index += 1
		if self.index >= len(self):
			self.index = 0
		return value

	def __contains__(self, value):
		return value in self.possible
	
	def __len__(self):
		return len(self.possible)
	
	def __str__(self):
		return self.current()
	
	def __repr__(self):
		return 'Base(['+','.join(self.possible)+'])'

class Chain(Base):
	def __init__(self, possible):
		Base.__init__(self, possible)
		self.n = None
	
	def chain(self, next):
		self.n = next

	def next(self):
		Base.next(self)
		if self.index == 0:
			if self.n:
				self.n.next()

class Single(Chain):
	def __init__(self, possible):
		Base.__init__(self, set(possible))
	
	def current(self):
		return tuple(self.possible)[0]

	def next(self):
		self.index = abs(self.index - 1)

class Word:
	def __init__(self, chains):
		self.chains = chains
	
	def __str__(self):
		return ''.join(str(chain) for chain in self.chains)

similar = [
	'a4h',
	'b8e3',
	'L7',
	'96g',
	'rRP',
	'1Il!|',
	',.',
	"'`",
	'CGdpqo',
	'xk',
	'mn',
	'wm',
	't7',
	'2z',
	's5',
	'0o',
	'#H',
	'yu',
	'prk',
	'AHV',
	'FB',
	'jyg',
	';:',
	'?P',
	'<c',
	'C(',
	'>)D',
	'$S',
	'@a',
	'-_=',
	'[]()',
	'\/i'
]

chains = {}
for chars in similar:
	for char in chars:
		if not char in chains:
			chains[char] = set([char])
		for sub in chars:
			for case in (sub.lower(), sub.upper()):
				chains[char].add(case)

def make_chain(char):
	if char in chains:
		chars = chains[char]
	else:
		chars = [char]

	if len(chars) == 1:
		return Single(char)
	else:
		return Chain(chars)

def permute(string):
	positions = [make_chain(char) for char in string]
	word = Word(positions)
	for i in xrange(len(positions)-1):
		positions[i].chain(positions[i+1])

	first = positions[0]
	last = positions[-1]
	while last.index == 0:
		first.next()
		yield word
	
	while last.index != 0:
		first.next()
		yield word

if __name__ == '__main__':
	import sys
	output = False

	if len(sys.argv) > 1:
		output = True
		for word in sys.argv[1:]:
			for result in permute(word):
				print result
	
	if not sys.stdin.isatty():
		output = True
		for line in sys.stdin:
			for result in permute(line.strip()):
				print result
	
	if not output:
		print 'Usage: ./permute.py word ...'
