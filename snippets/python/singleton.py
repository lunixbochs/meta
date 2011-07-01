class Singleton(type):
	__singleton = None

	def __new__(cls, names, bases, attrs):
		cls = super(Singleton, cls).__new__(cls, names, bases, attrs)
		cls.__singleton = None
		return cls
	
	def __call__(cls, *args, **kwargs):
		if cls.__singleton is not None:
			return cls.__singleton
		else:
			instance = super(Singleton, cls).__call__(*args, **kwargs)
			cls.__singleton = instance
			return instance

class Test:
	__metaclass__ = Singleton

	def __init__(self, args):
		print 'Test(%s)' % args

if __name__ == '__main__':
	a = Test(1)
	b = Test(2)
	print a is b