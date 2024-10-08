# Generated by Django 4.2.4 on 2024-08-13 19:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0041_recordedpackaging'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='packaging',
            name='is_full',
        ),
        migrations.AddField(
            model_name='packaging',
            name='empty_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='packaging',
            name='full_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='packaging',
            name='sales_point',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.salespoint'),
        ),
    ]
