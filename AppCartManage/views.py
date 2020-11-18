from encodings.utf_8 import decode

from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from AppResourceManage.models import ResourceInfo
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin
from django.urls import reverse
from AppResourceManage.models import ResourceInfo
from AppUserManage.models import Address
import re


# Create your views here.
class CartAddView(View):
    '''商品列表添加购物车'''

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            context = {'res': 0, 'errmsg': '请先登录'}
            return JsonResponse(context)
        resource_id = request.POST.get('resource_id')
        # 校验商品是否存在
        try:
            resource = ResourceInfo.objects.get(id=resource_id)
        except ResourceInfo.DoesNotExist:
            context = {'res': 3, 'errmsg': '商品不存在'}
            return JsonResponse(context)
        # 业务处理：添加购物车记录
        conn = get_redis_connection()
        cart_key = 'car_%d' % user.id
        resource_count = 1
        conn.hset(cart_key, resource_id, resource_count)
        cart_len = conn.hlen(cart_key)
        context = {'res': 5, 'message': '添加购物车成功', 'cart_len': cart_len}
        return JsonResponse(context)


class CartInfoView(LoginRequiredMixin, View):
    '''显示购物车页面'''

    def get(self, request):
        user = request.user
        conn = get_redis_connection("default")
        cart_key = 'car_%d' % user.id
        len = conn.hlen(cart_key)
        cart_dict = conn.hgetall(cart_key)
        resource = []
        totalprice = 0
        # 是否需要物流flag
        isflag_logistics = False  # 是否需要物流flag
        dft_addr = False  # 是否有默认地址，控制添加框显示
        address_count = 0
        resource_count = 0
        for temp in cart_dict.keys():
            resource_count += 1
            id = int(temp)
            rsc = ResourceInfo.objects.get(id=id)
            totalprice += rsc.rprice
            if rsc.is_logistics:  # 判断是需要物流,如果有赋值
                isflag_logistics = True
                try:
                    address = Address.objects.get_choice_address(user)  # 查询选择出来的地址 is_default = 3 或者默认地址
                    address_count = Address.objects.filter(addUser=user).count()  # 该用户录入的地址条数
                    dft_addr = address
                except ResourceInfo.DoesNotExist:
                    dft_addr = False
            resource.append(rsc)
        context = {'list': resource,
                   'total': totalprice,
                   'is_logistics': isflag_logistics,
                   'dft_addr': dft_addr,
                   'address_count': address_count,
                   'resource_count': resource_count}
        return render(request, 'AppCart/Cart.html', context)


class CarDeleteView(View):
    '''删除购物车商品数据'''

    def post(self, request):
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收参数
        resource_id = request.POST.get('resource_id')
        # 校验数据
        if not resource_id:
            return JsonResponse({'res': 1, 'errmsg': '无效商品id'})
        try:
            ResourceInfo.objects.get(id=resource_id)
        except ResourceInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品已经不存在'})
        # 业务处理：删除redis里面对应的商品
        conn = get_redis_connection('default')
        cart_key = 'car_%d' % user.id
        conn.hdel(cart_key, resource_id)
        return JsonResponse({'res': 3, 'message': '删除成功'})


class CartAddressAdd(LoginRequiredMixin, View):
    '''购物车请求添加地址页面'''

    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        context = {'is_default': 3, 'address_default': address}
        return render(request, 'AppUser/user_center_site.html', context)

    def post(self, request):
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收参数
        receiver = request.POST.get('receiver')
        phone = request.POST.get('phone')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'AppUser/user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'^1([38][0-9]|4[579]|5[0-3,5-9]|6[6]|7[0135678]|9[89])\d{8}$', phone):
            return render(request, 'AppUser/user_center_site.html', {'errmsg': '手机号格式不正确'})

        # 业务处理：地址添加
        # 如果用户已经存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        # 获取登录用户对应user对象
        user = request.user
        address = Address.objects.get_default_address(user)
        if address:
            is_default = 3
        else:
            is_default = 2
        Address.objects.create(addUser=user, aphone=phone, addReceiver=receiver, addr=addr, zip_code=zip_code,
                               is_default=is_default)
        return JsonResponse({'resp': 4, 'msg': '添加成功'})


class AddressChoice(LoginRequiredMixin, View):
    '''购物车页面，在地址列表中选择邮寄的地址'''

    def post(self, request):
        user = request.user
        # 接收参数
        address_id = request.POST.get('address_id')
        # 查询Address原来状态
        old_default = Address.objects.get(addUser=user, id=address_id)
        # 查找是否存在is_default=3的
        try:
            told = Address.objects.get(addUser=user, is_default=3)
            told.is_default = 1
            told.save()
            if old_default.is_default == 1:
                old_default.is_default = 3
                old_default.save()
        except Address.DoesNotExist:
            if old_default.is_default == 1:
                old_default.is_default = 3
                old_default.save()
        return JsonResponse({'resp': 1, 'msg': '修改成功'})
