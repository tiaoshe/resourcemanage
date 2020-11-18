from django.urls import path
from AppOrderManage.views import OrderPlaceView, OrderCommitView, OrderPayView, CheckPayView, UserPowerOrderCommitView, CheckPowerPayView

app_name = 'AppOrderManage'
urlpatterns = [
    path('order_place', OrderPlaceView.as_view(), name='order_place'),
    path('order_commit', OrderCommitView.as_view(), name='commit'),
    path('order_pay', OrderPayView.as_view(), name='order_pay'),
    path('order_check', CheckPayView.as_view(), name='check'),
    path('user_power', UserPowerOrderCommitView.as_view(), name='power'),
    path('user_power_pay', CheckPowerPayView.as_view(), name='powerpay'),

]
