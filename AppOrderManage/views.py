from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings
from django.urls import reverse

from utils.mixin import LoginRequiredMixin
from AppUserManage.models import Address
from AppResourceManage.models import ResourceInfo
from AppOrderManage.models import OrderInfo, OrderGoods, UserPower

from datetime import datetime
from alipay import AliPay
import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)


# /order/order_pay
class OrderPlaceView(LoginRequiredMixin, View):
    '''提交订单页面显示'''

    def post(self, request):
        # 接收参数，判断有没有传resource_id过来
        resource_id = request.POST.get('resource_id')
        # 获取登录的用户
        user = request.user
        # 用户地址
        address = None
        # 声明资料对象数组
        resource = []
        # 计算商品总金额
        total_price = 0
        # 计算商品总件数
        resource_count = 0
        # 购物车商品id列表
        resource_id_list = []
        is_logistics = False
        address_count = 0
        if not resource_id:
            # 获取商品信息
            conn = get_redis_connection("default")
            cart_key = 'car_%d' % user.id
            cart_dict = conn.hgetall(cart_key)
            for temp in cart_dict.keys():
                resource_count += 1
                temp_id = int(temp)
                resource_id_list.append(temp_id)
                rsc = ResourceInfo.objects.get(id=temp_id)
                total_price += rsc.rprice
                if rsc.is_logistics:
                    is_logistics = True
                    # 获取到用户的地址 这里有缺陷需要单独写方法能够解决问题  如果有多个需要地址的商品会出现重复赋值
                    address = Address.objects.get_choice_address(user)
                    address_count = Address.objects.filter(addUser=user).count()  # 该用户录入的地址条数
                resource.append(rsc)
            # 计算商品实际付款
            actual_payment = total_price
            # 前端数据整理
        else:
            # 通过id查询出商品
            res = ResourceInfo.objects.get(id=resource_id)
            # 判断是否需要地址
            is_logistics = res.is_logistics
            if is_logistics:
                address = Address.objects.get_choice_address(user)
                address_count = Address.objects.filter(addUser=user).count()  # 该用户录入的地址条数
            # 总价格赋值
            total_price = res.rprice
            # 商品数量赋值
            resource_count = 1
            # 实际支付金额
            actual_payment = total_price
            # 资源id 列表赋值
            resource.append(res)
            resource_id_list.append(res.id)
        context = {'choice_address': address,
                   'resource_list': resource,
                   'total_price': total_price,
                   'resource_count': resource_count,
                   'actual_payment': actual_payment,
                   'resource_id_list': resource_id_list,
                   'is_logistics': is_logistics,
                   'address_count': address_count
                   }
        return render(request, 'AppOrder/order_place.html', context)


class UserPowerOrderCommitView(View):
    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'resp': 0, 'errmsg': '用户未登录'})
        pay_method = request.POST.get('pay_method')
        if not all([pay_method, ]):
            return JsonResponse({'resp': 1, 'errmsg': '参数不完整'})
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'resp': 2, 'errmsg': '非法的支付方式'})
        # 订单id：时间+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 0
        # 总数目和总金额
        total_count = 1
        total_price = 199
        pay_name = '终身会员'
        # 设置事物保存点
        save_id = transaction.savepoint()
        try:
            order = UserPower.objects.create(pay_name=pay_name,
                                             order_id=order_id,
                                             user=user,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             order_status=1
                                             )
        except Exception:
            return JsonResponse({'resp': 4, 'errmsg': '下单失败'})
        transaction.savepoint_commit(save_id)

        app_private_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/app_private_key.pem')).read()
        alipay_public_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2016102200737720",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key,
            alipay_public_key_string=alipay_public_key,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )
        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order.order_id,  # 订单id
            total_amount=str(order.total_price),  # 支付总金额
            subject='资源管理系统%s' % order.order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 5, 'pay_url': pay_url, 'order_id': order_id})


class OrderCommitView(View):
    '''订单创建'''

    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'resp': 0, 'errmsg': '用户未登录'})
        pay_method = request.POST.get('pay_method')
        resource_ids = request.POST.get('resource_ids')
        # 校验参数
        if not all([pay_method, resource_ids]):
            return JsonResponse({'resp': 1, 'errmsg': '参数不完整'})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'resp': 2, 'errmsg': '非法的支付方式'})
        # 校验地址
        resource_ids_list = resource_ids.lstrip('[').rstrip(']').split(',')
        # 组织参数
        # 订单id：时间+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 0
        # 总数目和总金额
        total_count = 0
        total_price = 0
        # 获取商品信息  通过resource_ids 去查询 然后提交订单
        conn = get_redis_connection("default")
        cart_key = 'car_%d' % user.id
        # 商品列表
        resource_list = []
        # 地址为空
        address = None
        for temp in resource_ids_list:
            total_count += 1
            temp_id = int(temp)
            rsc = ResourceInfo.objects.get(id=temp_id)
            total_price += rsc.rprice
            if rsc.is_logistics:
                address = Address.objects.get_choice_address
            resource_list.append(rsc)
        # 设置事物保存点
        save_id = transaction.savepoint()
        try:
            if address:
                order = OrderInfo.objects.create(order_id=order_id,
                                                 user=user,
                                                 pay_method=pay_method,
                                                 total_count=total_count,
                                                 total_price=total_price,
                                                 transit_price=transit_price)
            else:
                order = OrderInfo.objects.create(order_id=order_id,
                                                 user=user,
                                                 addr=address,
                                                 pay_method=pay_method,
                                                 total_count=total_count,
                                                 total_price=total_price,
                                                 transit_price=transit_price)
            for resource in resource_list:
                OrderGoods.objects.create(order=order,
                                          sku=resource,
                                          count=1,
                                          price=resource.rprice)
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'resp': 4, 'errmsg': '下单失败'})
        transaction.savepoint_commit(save_id)
        conn.hdel(cart_key, *resource_ids)
        return JsonResponse({'resp': 5, 'message': '创建成功'})


# ajax post
# 前端传递的参数:订单id(order_id)
# /order/pay
class OrderPayView(View):
    '''订单支付'''

    def post(self, request):
        '''订单支付'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=2,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        app_private_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/app_private_key.pem')).read()
        alipay_public_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2016102200737720",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key,
            alipay_public_key_string=alipay_public_key,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )
        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.transit_price + order.total_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject='资源管理系统%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url, 'order_id': order_id})


# ajax post
# 前端传递的参数:订单id(order_id)
# /order/check
class CheckPayView(View):
    '''查看订单支付的结果'''

    def post(self, request):
        '''订单支付'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=2,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        app_private_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/app_private_key.pem')).read()
        alipay_public_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2016102200737720",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key,
            alipay_public_key_string=alipay_public_key,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)

            # response = {
            #         "trade_no": "2017032121001004070200176844", # 支付宝交易号
            #         "code": "10000", # 接口调用是否成功
            #         "invoice_amount": "20.00",
            #         "open_id": "20880072506750308812798160715407",
            #         "fund_bill_list": [
            #             {
            #                 "amount": "20.00",
            #                 "fund_channel": "ALIPAYACCOUNT"
            #             }
            #         ],
            #         "buyer_logon_id": "csq***@sandbox.com",
            #         "send_pay_date": "2017-03-21 13:29:17",
            #         "receipt_amount": "20.00",
            #         "out_trade_no": "out_trade_no15",
            #         "buyer_pay_amount": "20.00",
            #         "buyer_user_id": "2088102169481075",
            #         "msg": "Success",
            #         "point_amount": "0.00",
            #         "trade_status": "TRADE_SUCCESS", # 支付结果
            #         "total_amount": "20.00"
            # }

            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 5  # 已完成
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，可能一会就会成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class CheckPowerPayView(View):
    '''查看订单支付的结果'''

    def post(self, request):
        '''订单支付'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        print(order_id)
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = UserPower.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=2,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        app_private_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/app_private_key.pem')).read()
        alipay_public_key = open(os.path.join(settings.BASE_DIR, 'AppOrderManage/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2016102200737720",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key,
            alipay_public_key_string=alipay_public_key,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 2  # 已完成
                order.save()
                user.upower = 3
                user.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，可能一会就会成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})
