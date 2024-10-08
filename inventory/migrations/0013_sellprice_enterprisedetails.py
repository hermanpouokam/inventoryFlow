# Generated by Django 4.2.4 on 2024-08-07 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_alter_user_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sell_prices', to='inventory.product')),
            ],
        ),
        migrations.CreateModel(
            name='EnterpriseDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('enterprise', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='inventory.enterprise')),
            ],
        ),
    ]
