from django.urls import path
from django.contrib.auth.decorators import login_required
from AppUserManage.views import RegisterView, LoginView, UserInfoView, UserOrderView, AddressView, LogoutView, \
    UserAllAddressView, UserDemandView, UserPowerView

app_name = 'AppUserManage'
urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('center', UserInfoView.as_view(), name='center'),
    path('order/<int:page>', UserOrderView.as_view(), name='order'),
    path('address', AddressView.as_view(), name='address'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('all_address', UserAllAddressView.as_view(), name='all_address'),
    path('user_demand', UserDemandView.as_view(), name='demand'),
    path('power', UserPowerView.as_view(), name='power')
]
