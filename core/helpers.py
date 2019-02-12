import json
from time import sleep

def split_n(string, delimiter=',', n=None, length=None, rejoin=True):
    l = string.split(delimiter)
    count = len(l)
    if isinstance(n, int):
        length = count // n
        r = [l[i*(length+1): (i+1)*(length+1)] if i < (count % n) else l[i*length: (i+1)*length] for i in range(n)]
    elif isinstance(length, int):
        n = count // length + (0 if count % length == 0 else 1)
        r = [l[i*length: (i+1)*length] for i in range(n)]
    else:
        raise ValueError('One of "n" and "length" must be integer. {} and {} given.'.format(n, length))
    if rejoin:
        r = [delimiter.join(i) for i in r]
    return r

def try_n(n, func, interval=0.1, *args, **kwargs):
    '''Run `func` for `n` times.'''
    for i in range(n):
        try:
            r = func(*args, **kwargs)
        except KeyboardInterrupt:
            break
        except:
            continue
        else:
            return r
        sleep(interval)
    return False


def read_json(f):
    with open(f, 'r') as json_file:
        data = json.load(json_file)
    return data

def write_json(f, data):
    with open(f, 'w') as outfile:
        json.dump(data, outfile)
