from django.contrib import admin
from AppResourceManage.models import ResourceInfo, ResourceType


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 发出任务,让celery worker重新生成首页内容
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()


class ResourceInfoAdmin(BaseModelAdmin):
    list_display = ['id', 'rname', 'rprice', 'rdescribe']


class ResourceTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'type_name', 'type_parent']


admin.site.register(ResourceInfo, ResourceInfoAdmin)
admin.site.register(ResourceType, ResourceTypeAdmin)
