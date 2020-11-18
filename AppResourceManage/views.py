from django.shortcuts import render, redirect
from AppResourceManage.models import ResourceInfo, ResourceType
from django.views.generic import View
from django.urls import reverse
from django_redis import get_redis_connection
from utils.cart import CartUtil
from AppOrderManage.models import OrderInfo


# 首页显示
class IndexView(View):
    def get(self, request):
        resource_list = ResourceInfo.objects.all()
        # 查询root分类
        resource_type_root = ResourceType.objects.filter(type_parent__isnull=True)
        # 排序root分类
        resource_types = resource_type_root.order_by('sort_num')[0:6]
        # 查询指定编号的,能查询出数组中能够查询出来的编号
        resource_type_appoints = ResourceType.objects.filter(sort_num__in=[1, 2, 3, 4, 5, 6, 7, 8])
        # 购物车数量统计cart_count
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection("default")
            cart_key = 'car_%d' % user.id
            cart_count = conn.hlen(cart_key)
        context = {"resource_list": resource_list,
                   'resource_types': resource_types,
                   'resource_type_appoints': resource_type_appoints,
                   'cart_count': cart_count
                   }
        return render(request, 'AppResource/index.html', context)


class DetailView(View):
    '''详情页显示'''

    def get(self, request, resource_id):
        try:
            resource = ResourceInfo.objects.get(id=resource_id)
        except ResourceInfo.DoesNotExist:
            return redirect(reverse('resource:index'))
        user = request.user
        if not user.is_authenticated:
            cart_count = 0
        else:
            cart_count = CartUtil().find_cart_number(user.id)
        # 获取用户信息
        try:
            if user.upower >= 3:
                cloud_address = resource.rbaiduCloudAddress
            elif OrderInfo.objects.is_payed(user=user, resource=resource):
                cloud_address = resource.rbaiduCloudAddress
            else:
                cloud_address = "购买后自动显示"
        except Exception:
            cloud_address = "购买后自动显示"
        # 数据整理
        context = {'resource': resource, 'cart_count': cart_count, 'cloud_address': cloud_address}

        return render(request, 'AppResource/detail.html', context)


class ResourceTypeView(View):
    def get(self, request, type_id):
        user = request.user
        if not all([type_id]):
            return render(request, 'AppResource/index.html', {'errmsg': '无效参数'})
        try:
            type_temp = ResourceType.objects.get(id=type_id)
        except ResourceType.DoesNotExist:
            return render(request, 'AppResource/index.html', {'errmsg': '无效参数'})
        try:
            resource_list = type_temp.resourceinfo_set.all()
        except Exception:
            resource_list = None

        # 查询分类列表数据
        resource_types = ResourceType.objects.filter(type_parent__isnull=True)
        print(type(user.id))
        try:
            # 查询购物车数量
            cart_count = CartUtil().find_cart_number(user.id)
        except Exception:
            cart_count = 0

        context = {'resource_list': resource_list, 'resource_types': resource_types, 'cart_count': cart_count}
        return render(request, 'AppResource/type_list.html', context)
