# Generated by Django 4.2.4 on 2024-08-05 23:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_category_enterprise_clientcategory_enterprise_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterprise',
            name='plan',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enterprises', to='inventory.plan'),
        ),
    ]
