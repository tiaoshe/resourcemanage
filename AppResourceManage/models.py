from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


class ResourceManager(models.Manager):
    def get_type_resource(self, resource_type):
        resource_list = ResourceInfo.objects.filter(resource_type=resource_type)
        return resource_list


# 定义资源模型类
class ResourceInfo(BaseModel):
    rname = models.CharField(max_length=100, db_column='name', verbose_name='资源名称')  # 资源名称
    rprice = models.DecimalField(decimal_places=2, max_digits=5, db_column='price', default=1,
                                 verbose_name='资源价格')  # 资源价格
    rdescribe = models.CharField(max_length=2000, db_column='describe', default="无", verbose_name='资源描述')  # 资源描述
    rdetail = HTMLField(db_column='rdetail', null=True, verbose_name='资源详情')
    is_logistics = models.BooleanField(max_length=2, db_column='is_logistics', default=False, verbose_name='是否需要物流')
    rbaiduCloudAddress = models.CharField(max_length=200, db_column='baiduCloudAddress', default="无",
                                          verbose_name='云盘地址')  # 云盘地址
    resource_type = models.ForeignKey('ResourceType', null=True, blank=True, on_delete=models.SET_NULL,
                                      db_column='type',
                                      verbose_name='类别')
    objects = ResourceManager()

    def __str__(self):
        return "资源管理"

    class Meta:
        db_table = 'resourceinfo'
        verbose_name = '资源'
        verbose_name_plural = verbose_name


class ResourceType(BaseModel):
    '''资源类型模型类'''
    type_name = models.CharField(max_length=30, verbose_name='种类名称', db_column='typename')
    logo = models.CharField(max_length=20, verbose_name='标识', db_column='logo')
    image = models.ImageField(upload_to='type', null=True, blank=True, verbose_name='商品类型图片', db_column='image')
    sort_num = models.IntegerField(null=True, blank=True, verbose_name='类别排序', db_column='sort_num')
    type_parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='类别父类',
                                    db_column='parent')

    class Meta:
        db_table = 'resource_type'
        verbose_name = '商品种类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.type_name


class IndexRsourceBanner(BaseModel):
    '''首页轮播资源展示模型类'''
    Resource = models.ForeignKey('ResourceInfo', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='商品')
    image = models.ImageField(upload_to='banner', null=True, blank=True, verbose_name='图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')  # 0 1 2 3

    class Meta:
        db_table = 'index_banner'
        verbose_name = '首页轮播商品'
        verbose_name_plural = verbose_name


class IndexTypeRsourceBanner(BaseModel):
    '''首页分类商品展示模型类'''
    DISPLAY_TYPE_CHOICES = (
        (0, "标题"),
        (1, "图片")
    )
    type = models.ForeignKey('ResourceType', on_delete=models.CASCADE, verbose_name='资源分类')
    resource = models.ForeignKey('ResourceInfo', on_delete=models.CASCADE, verbose_name='资源')
    display_type = models.SmallIntegerField(default=1, choices=DISPLAY_TYPE_CHOICES, verbose_name='展示类型')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'index_type_goods'
        verbose_name = "主页分类展示资源"
        verbose_name_plural = verbose_name
