from django.test import TestCase


# Create your tests here.

def zhuanhuan():
    a = ['2', '1']
    astr = ','.join(a)
    print(astr)
    list = astr.split(',')
    print(list)


if __name__ == '__main__':
    zhuanhuan()
