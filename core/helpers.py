import json, string
from time import sleep
from collections import OrderedDict

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


def col2num(col):
    num = 0
    for c in col:
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return num

def num2col(num):
    col = ''
    while num > 0:
        num, remainder = divmod(num-1, 26)
        col = chr(65 + remainder) + col
    return col


def circled_str(s, symbol='*', width=86):
    return '\n' + symbol*width + '\n' + symbol + ' ' + s.ljust(width-3) + symbol + '\n' + symbol*width + '\n'

def read_configuration(config_path, key=None):
    config = read_json(config_path)
    if key:
        return config.get(key, None)
    return config

def write_configuration(config_path, **kwargs):
    config = OrderedDict(read_json(config_path))
    config.update(kwargs)
    write_json(config_path, config)
