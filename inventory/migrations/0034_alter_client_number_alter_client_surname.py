# Generated by Django 4.2.4 on 2024-08-12 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0033_clientcategory_sales_point_supplier_sales_point'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='number',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='client',
            name='surname',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
