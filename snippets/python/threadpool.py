from Queue import Queue, Empty
import threading
import traceback
import inspect
import os, stat

def isiter(obj):
	'''
	test whether an object conforms to the iterator protocol
	'''
	try:
		if obj.__iter__() == obj and obj.next:
			return True
	except AttributeError:
		pass

	return False

class stack_size:
	def __init__(self, stack_size):
		self.stack_size = stack_size
		self.old_size = threading.stack_size()

	def __enter__(self):
		threading.stack_size(self.old_size)

	def __exit__(self, type, value, traceback):
		threading.stack_size(self.stack_size)

class Lock:
	def __init__(self):
		self.lock = threading.Lock()
	
	def __enter__(self):
		self.lock.acquire()
	
	def __exit__(self, type, value, traceback):
		self.lock.release()

class FilenameLogger:
	def __init__(self, filename):
		self.filename = filename
		self.filepath = os.path.join(os.getcwd(), filename)
		self.fileobj = open(self.filepath, 'a')
	
	def __call__(self, msg):
		# someone renamed our file! maybe logrotate'd. open a new one.
		if not os.path.exists(self.filepath) or os.stat(self.filepath)[stat.ST_INO] != os.fstat(self.fileobj.fileno())[stat.ST_INO]:
			self.fileobj = open(self.filepath, 'a')
		
		self.fileobj.write(msg+'\n')

class FileObjLogger:
	def __init__(self, fileobj=None, filename=None):
		self.fileobj = fileobj or open(filename, 'a') if filename else None
	
	def __call__(self, msg):
		if self.fileobj and not self.fileobj.closed:
			self.fileobj.write(msg+'\n')

class ThreadSafeLogger:
	'''
	Init with a list of loggers to call when this class is called()
	"None" logs to stdout, string obj logs to filename, fileobj logs to write(), callable(obj) acts as a callback.

	formatter=callback allows you to set a callback which can rewrite the message passed to log
	separator=str allows you to set the separator between args passed
	'''
	def __init__(self, *args, **kwargs):
		self.formatter = None
		self.separator = ', '
		if 'formatter' in kwargs and callable(kwargs['formatter']):
			self.formatter = kwargs['formatter']
		if 'separator' in kwargs:
			self.separator = kwargs['separator']
		
		loggers = set()
		for logger in args:
			if hasattr(logger, 'write') and callable(logger.write):
				loggers.add(FileObjLogger(fileobj=logger))
			elif isinstance(logger, basestring):
				loggers.add(FilenameLogger(logger))
			elif callable(logger):
				loggers.add(logger)
			else:
				loggers.add(self.echo)
		
		self.loggers = loggers or (self.echo,)
		self.lock = Lock()
	
	def __call__(self, *args):
		with self.lock:
			self.callback(*args)

	def callback(self, *args):
		msg = self.separator.join(str(arg) for arg in args)
		if self.formatter:
			msg = self.formatter(msg)

		for logger in self.loggers:
			logger(msg)

	def echo(self, msg):
		print msg

class ThreadPool:
	def __init__(self, max_threads, log_returns=False, catch_returns=False, logger=None, stack_size=0, return_queue=1000):
		self.lock = threading.Lock()
		self.max = max_threads
		self.logger = logger or (lambda *x: None)
		self.stack_size = stack_size
		self.log_returns = log_returns
		self.catch_returns = catch_returns

		self.call_queue = Queue()
		self.returns = Queue(return_queue)
		self.spawn_workers()

	def __call__(self, func):
		def wrapper(*args, **kwargs):
			self.call_queue.put((func, args, kwargs))

		return wrapper
	
	def spawn_workers(self):
		for i in xrange(self.max):
			thread = threading.Thread(target=self.worker, args=(self.call_queue,))
			thread.daemon = True
			thread.start()
	
	def worker(self, call):
		while True:
			func, args, kwargs = call.get()
			try:
				result = func(*args, **kwargs)
				if self.catch_returns or self.log_returns:
					if inspect.isgenerator(result) or isiter(result):
						for x in result:
							self.returned(x)
					else:
						self.returned(result)
			except:
				self.logger(traceback.format_exc())
			finally:
				call.task_done()
	
	def returned(self, result):
		if self.log_returns:
			self.logger(result)
		if self.catch_returns:
			self.returns.put(result)
	
	def pop(self):
		'''
		pop a result from the queue, blocks if we have none
		'''
		if self.catch_returns:
			result = self.returns.get()
			self.returns.task_done()
			return result

	def iter(self):
		'''
		act as a generator, returning results as they happen
		this method assumes you've already queued all of your calls
		'''
		if not self.catch_returns:
			raise Exception

		while self.call_queue.unfinished_tasks > 0:
			try:
				yield self.returns.get(timeout=0.1)
			except Empty:
				pass

		for value in self.finish():
			yield value

	def flush(self):
		'''
		clear and return the function returns queue
		'''
		if self.catch_returns:
			results = tuple(self.returns.queue)
			self.returns = Queue()
			return results

		return ()

	def finish(self):
		'''
		wait for queue to finish, then return flush()
		'''
		self.call_queue.join()
		return self.flush()

if __name__ == '__main__':
	log = ThreadSafeLogger()
	# don't use catch_returns unless you're going to use them - otherwise they will never clear and just leak memory
	pool = ThreadPool(100, logger=log, log_returns=True, catch_returns=True)

	import time

	@pool
	def test(i):
		log('from thread', i)
		yield 'yield %i' % i
		# sleep to show how awesome it is that we allow generators
		time.sleep(0.5)
		yield 'yield %i' % (i*10)

	for i in xrange(1,6):
		test(i)

	# because these pops will all happen before the sleep is finished, we'll get numbers < 100
	log('first pop')
	for i in xrange(5):
		log(pool.pop())
	
	# just to make sure it works
	pool.flush()

	# because these pops will happen after the sleep, we'll get numbers over 100
	results = pool.finish()
	print results
