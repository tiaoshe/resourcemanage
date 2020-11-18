from celery import Celery
import os
from AppResourceManage.models import ResourceInfo
from django.template import loader
from django.conf import settings


# 任务处理者一端加入这个，django环境的初始化
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmanage.settings')
django.setup()


# 创建一个Celery实例对象，第一个参数随便写，按照规则路径加文件名
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/2')


@app.task
def generate_static_index_html():
    '''产生静态页面'''
    # 查询出首页用到的数据
    list = ResourceInfo.objects.all()

    # 使用模板
    # 1、加载模板文件
    temp = loader.get_template('AppResourceManage/index.html')
    # 2、定义模板上下文
    context = {'list': list}
    # 3、模板渲染
    satic_index_html = temp.render(context)

    # 生成一个对应的文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(satic_index_html)
