# Generated by Django 3.0.5 on 2020-04-24 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AppResourceManage', '0006_auto_20200425_0250'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcetype',
            name='sort_num',
            field=models.IntegerField(blank=True, db_column='sort_num', max_length=4, null=True, verbose_name='类别排序'),
        ),
    ]
