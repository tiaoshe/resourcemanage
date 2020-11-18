from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers
from django.core.paginator import Paginator

from AppUserManage.models import Address
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from AppUserManage.models import User, UserDemand
from AppOrderManage.models import OrderInfo, OrderGoods, UserPower
import re
from utils.is_include_chinese import IsChinese


class RegisterView(View):
    def get(self, request):
        return render(request, 'AppUser/register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpw = request.POST.get('cpw')
        email = request.POST.get('email')
        # 进行数据校验
        if IsChinese().is_contain_chinese(username):
            return render(request, 'AppUser/register.html', {'errmsg': '用户名中包含中文'})
        if not all([username, password, email]):
            return render(request, 'AppUser/register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'AppUser/register.html', {'errmsg': '邮箱格式不正确'})
        if password != cpw:
            return render(request, 'AppUser/register.html', {'errmsg': '两次输入的密码不一致'})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'AppUser/register.html', {'errmsg': '用户已经存在'})
        user = User.objects.create_user(username, email, password)
        user.is_active = 1
        user.save()
        return redirect('/user/login')


class LoginView(View):
    '''登录'''

    def get(self, request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ""
            checked = ""
        return render(request, 'AppUser/login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remembername = request.POST.get('remember')
        next_url = request.GET.get('next', default=reverse('resource:index'))

        if not all([username, password]):
            return render(request, 'AppUser/login.html', {'errmsg': '数据不完整'})
        user = authenticate(username=username, password=password)
        if user is not None:
            # 记录用户登录状态
            login(request, user)
            response = redirect(next_url)
            if remembername == 'on':
                request.session['username'] = username
                response.set_cookie('username', username, max_age=7 * 24 * 3600)
            else:
                response.delete_cookie('username')
            return response
        else:
            return render(request, 'AppUser/login.html', {'errmsg': '用户名或密码不正确'})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('resource:index'))


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        '''显示用户中心数据'''
        # Django会给request对象添加一个属性reques.user
        # 如果用户未登录->user是AnonymousUser类的一个实力对象
        # 如果用户登录->user是User类的一个实例对象
        user = request.user
        context = {'user': user, 'page': 'user'}
        return render(request, 'AppUser/user_center_info.html', context)


class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        return render(request, 'AppUser/user_center_site.html', {'address_default': address, 'page': 'address'})

    def post(self, request):
        # 接收数据
        receiver = request.POST.get('receiver')
        phone = request.POST.get('phone')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        is_default = request.POST.get('is_default')

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
        if is_default == '3':
            # 检查数据库中是否存在地址为3的
            try:
                address = Address.objects.get(addUser=user, is_default=3)
                # 如果存在，则将所有修改成 1
                address.is_default = 1
                address.save()
            except Address.DoesNotExist:
                is_default = 3
        elif address:
            is_default = 1
        else:
            is_default = 2
        Address.objects.create(addUser=user, aphone=phone, addReceiver=receiver, addr=addr, zip_code=zip_code,
                               is_default=is_default)
        return redirect(reverse('user:address'))


class UserAllAddressView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        addresslist = Address.objects.get_all_address(user)
        jsondata = serializers.serialize('json', addresslist)
        return JsonResponse({'resp': 1, 'address_list': jsondata})


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''

    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_goods = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_resource in order_goods:
                # 计算小计
                amount = order_resource.price
                # 动态给order_resource增加属性amount,保存订单商品的小计
                order_resource.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_goods = order_goods
        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}
        # 使用模板
        return render(request, 'AppUser/user_center_order.html', context)


# /user/demand
class UserDemandView(View):
    """用户提的需求储存"""

    def post(self, request):
        # 获取数据
        content = request.POST.get('user_demand')
        # 判断数据
        if not all([content]):
            return JsonResponse({'resp': 0, 'errmsg': '数据丢失或者没有提交任何数据'})
        demand = UserDemand()
        demand.content = content
        demand.save()
        return JsonResponse({'resp': 1, 'message': '提交成功：老柒很快会看到！'})


class UserPowerView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        user.power_name = User.USER_POWER[user.upower]
        context = {'page': 'power'}
        return render(request, 'AppUser/user_center_power.html', context)
