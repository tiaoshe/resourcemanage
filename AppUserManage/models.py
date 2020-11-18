from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import AbstractUser


class User(AbstractUser, BaseModel):
    '''用户模型'''
    "用户权限选择"
    USER_POWER_CHOICES = (
        (1, '普通用户'),  # 新注册的用户
        (2, '普通会员'),  # 参与过购买的用户
        (3, '终身会员'),  # 购买了店铺会员
        (9, '管理员')
    )
    USER_POWER = {
        1: '普通用户',
        2: '普通会员',
        3: '终身会员',
    }
    upower = models.IntegerField(choices=USER_POWER_CHOICES, default=1, db_column='power', verbose_name='用户权限')

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


# objects = UserManager()
class AddressManager(models.Manager):
    '''地址模型管理器类'''

    def get_default_address(self, user):
        try:
            address = self.get(addUser=user, is_default=2)
        except self.model.DoesNotExist:
            address = None
        return address

    def get_choice_address(self, user):
        try:
            address = self.get(addUser=user, is_default=3)
        except self.model.DoesNotExist:
            try:
                address = self.get(addUser=user, is_default=2)
            except self.model.DoesNotExist:
                address = None
        return address

    # 获取用户下所有的地址
    def get_all_address(self, user):
        try:
            addresslist = self.filter(addUser=user)
        except self.model.DoesNotExist:
            addresslist = None
        return addresslist


class Address(BaseModel):
    '''地址模块'''
    USER_ADDRESS_CHOICE = (
        (1, '地址'),  # 新注册的用户
        (2, '默认地址'),  # 参与过购买的用户
        (3, '选择的地址'),
    )
    addUser = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='所属账户')
    addReceiver = models.CharField(max_length=20, db_column='receiver', verbose_name='收件人')
    addr = models.CharField(max_length=256, db_column='address', verbose_name='收件地址')
    zip_code = models.CharField(max_length=11, null=True, verbose_name='邮编')
    aphone = models.CharField(max_length=11, db_column='phone', verbose_name='联系电话')
    is_default = models.IntegerField(default=1, verbose_name='地址分类')

    objects = AddressManager()

    class Meta:
        db_table = 'address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name


class UserDemand(BaseModel):
    content = models.CharField(max_length=500, db_column='content', verbose_name='内容')

    class Meta:
        db_table = 'user_Demand'
        verbose_name = '用户需求'
        verbose_name_plural = verbose_name
