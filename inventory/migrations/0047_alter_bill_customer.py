# Generated by Django 4.2.4 on 2024-08-21 06:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0046_alter_salespoint_enterprise'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.client'),
        ),
    ]
