# Generated by Django 3.0.5 on 2020-04-24 18:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AppResourceManage', '0005_auto_20200425_0249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourceinfo',
            name='resource_type',
            field=models.ForeignKey(blank=True, db_column='type', null=True, on_delete=django.db.models.deletion.SET_NULL, to='AppResourceManage.ResourceType', verbose_name='类别'),
        ),
    ]