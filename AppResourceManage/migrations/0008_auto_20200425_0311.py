# Generated by Django 3.0.5 on 2020-04-24 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AppResourceManage', '0007_resourcetype_sort_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcetype',
            name='sort_num',
            field=models.IntegerField(blank=True, db_column='sort_num', null=True, verbose_name='类别排序'),
        ),
    ]
