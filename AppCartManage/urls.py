from django.urls import path
from AppCartManage.views import CartAddView, CartInfoView, CarDeleteView, CartAddressAdd, AddressChoice

app_name = 'AppCartManage'
urlpatterns = [
    path('cartadd', CartAddView.as_view(), name='cartadd'),
    path('cart', CartInfoView.as_view(), name='cart'),
    path('remove', CarDeleteView.as_view(), name='remove'),
    path('address', CartAddressAdd.as_view(), name='address'),
    path('addchoice', AddressChoice.as_view(), name='addchoice'),
]
