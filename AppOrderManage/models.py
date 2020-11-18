from django.db import models
from db.base_model import BaseModel


class OrderManager(models.Manager):
    def is_payed(self, user, resource):
        try:
            orders = OrderInfo.objects.filter(user=user, order_status=5).order_by('-create_time')
            result = None
            for order in orders:
                try:
                    order.ordergoods_set.get(sku=resource)
                    result = True  # 找到了该商品
                    break
                except OrderGoods.DoesNotExist:
                    continue
            return result
        except OrderInfo.DoesNotExist:
            return None  # 没有找到该用户的相关订单


class OrderInfo(BaseModel):
    PAY_METHODS = {
        '1': '微信支付',
        '2': '支付宝'
    }
    '''订单模型类'''
    PAY_METHOD_CHOICES = (
        (1, '微信支付'),
        (2, '支付宝'),
    )

    ORDER_STATUS_CHOICES = (
        (1, '待支付'),
        (2, '待发货'),
        (3, '待收货'),
        (4, '待评价'),
        (5, '已完成')
    )

    ORDER_STATUS = {
        1: '待支付',
        2: '待发货',
        3: '待收货',
        4: '待评价',
        5: '已完成'
    }

    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单id')
    user = models.ForeignKey('AppUserManage.User', on_delete=models.CASCADE, verbose_name='用户')
    addr = models.ForeignKey('AppUserManage.Address', on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='地址')
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=1, verbose_name='支付方式')
    total_count = models.IntegerField(default=1, verbose_name='商品数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
    transit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单运费')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name='订单状态')
    trade_no = models.CharField(max_length=128, verbose_name='支付编号')
    objects = OrderManager()

    class Meta:
        db_table = 'df_order_info'
        verbose_name = '订单'
        verbose_name_plural = verbose_name


class OrderGoods(BaseModel):
    '''订单商品模型类'''
    order = models.ForeignKey('OrderInfo', on_delete=models.CASCADE, verbose_name='订单')
    sku = models.ForeignKey('AppResourceManage.ResourceInfo', on_delete=models.CASCADE, verbose_name='商品信息')
    count = models.IntegerField(default=1, verbose_name='商品数目')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='实际成交价格')
    comment = models.CharField(max_length=256, null=True, blank=True, verbose_name='评论')

    class Meta:
        db_table = 'df_order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name


class UserPower(BaseModel):
    PAY_METHODS = {
        '1': '微信支付',
        '2': '支付宝'
    }
    '''订单模型类'''
    PAY_METHOD_CHOICES = (
        (1, '微信支付'),
        (2, '支付宝'),
    )
    ORDER_STATUS_CHOICES = (
        (1, '待支付'),
        (2, '已完成')
    )

    ORDER_STATUS = {
        1: '待支付',
        2: '已完成'
    }
    pay_name = models.CharField(max_length=128, verbose_name='支付名称', null=True, blank=True)
    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单id')
    user = models.ForeignKey('AppUserManage.User', on_delete=models.CASCADE, verbose_name='用户')
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=1, verbose_name='支付方式')
    total_count = models.IntegerField(default=1, verbose_name='商品数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name='订单状态')
    trade_no = models.CharField(max_length=128, verbose_name='支付编号')

    class Meta:
        db_table = 'df_power_order_info'
        verbose_name = '会员订单'
        verbose_name_plural = verbose_name
