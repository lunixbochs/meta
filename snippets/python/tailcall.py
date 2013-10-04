import thread

def tail(func):
    stacks = {}

    def wrapper(*args, **kwargs):
        tid = thread.get_ident()
        topmost = tid not in stacks
        if topmost:
            count = 1
            stack = stacks[tid] = []
            try:
                value = func(*args, **kwargs)
                while len(stack) > 0:
                    count += 1
                    args, kwargs = stack.pop()
                    value = func(*args, **kwargs)

                del stacks[tid]
                return value
            except OverflowError:
                raise OverflowError, 'tail call, recursion depth %i' % count
            except MemoryError:
                raise MemoryError, 'tail call, recursion depth %i' % count
        else:
            stacks[tid].append((args, kwargs))

    return wrapper

if __name__ == '__main__':
    @tail
    def fib(i, current = 0, next = 1):
        if i == 0:
            return current
        else:
            return fib(i - 1, next, current + next)

    import time
    start = time.time()
    # 100k recursions is way over the python max recursion depth, but @tail doesn't care :)
    fib(100000)
    print 'Completed in %0.5f seconds.' % (time.time() - start)
