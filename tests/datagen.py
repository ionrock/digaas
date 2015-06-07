import random
import string

def random_letters(length):
    return "".join(random.choice(string.lowercase) for _ in xrange(length))

def random_digits(length):
    return "".join(random.choice(string.digits) for _ in xrange(length))

def random_zone_name():
    return "{0}-{1}-{2}.com.".format(random_letters(4), random_digits(3), random_letters(4))

def random_ip():
    return ".".join(map(str, [random.randrange(0, 256) for _ in xrange(4)]))
