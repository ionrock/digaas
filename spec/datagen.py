import random


def random_digits(n=8):
    return "".join([str(random.randint(0, 9)) for _ in range(n)])


def random_domain(name='testdomain', tld='com'):
    return '{0}{1}.{2}.'.format(name, random_digits(), tld)
