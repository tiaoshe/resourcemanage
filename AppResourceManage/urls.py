from django.urls import path
from AppResourceManage.views import IndexView, DetailView, ResourceTypeView

app_name = 'AppOrderManage'
urlpatterns = [
    path('index', IndexView.as_view(), name='index'),
    path('detail/<int:resource_id>/', DetailView.as_view(), name='detail'),
    path('type_list/<int:type_id>/', ResourceTypeView.as_view(), name='type_list')
]
