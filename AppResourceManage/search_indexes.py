# 定义索引类
from haystack import indexes

from AppResourceManage.models import ResourceInfo


class ResourceInfoIndex(indexes.SearchIndex, indexes.Indexable):
    # 索引字段 use_template=True 制定根据表中的那些字段建立索引文件的说明放在一个文件中
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return ResourceInfo

    # 建立索引的数据
    def index_queryset(self, using=None):
        return self.get_model().objects.all()
