# Generated by Django 3.0.5 on 2020-04-26 10:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AppUserManage', '0003_auto_20200425_1709'),
        ('AppOrderManage', '0002_auto_20200425_0125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderinfo',
            name='addr',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='AppUserManage.Address', verbose_name='地址'),
        ),
    ]
