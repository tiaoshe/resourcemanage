from django.test import TestCase
from django_redis import get_redis_connection
from AppResourceManage.models import ResourceInfo


# Create your tests here.
def add():
    zy=ResourceInfo.objects.get(id=3)
    print(zy.rname)


if __name__ == '__main__':
    add()
