"""
Migration: Add Role model and UserProfile model (dynamic role system).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_branch_multi_role_setup'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Create Role table
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                # Permission flags
                ('can_manage_orders', models.BooleanField(default=False, help_text='Create and update orders')),
                ('can_delete_orders', models.BooleanField(default=False, help_text='Delete orders')),
                ('can_manage_products', models.BooleanField(default=False, help_text='Add, edit products')),
                ('can_manage_customers', models.BooleanField(default=False, help_text='View and manage customers')),
                ('can_view_reports', models.BooleanField(default=False, help_text='Access PDF reports and analytics')),
                ('can_manage_users', models.BooleanField(default=False, help_text='Create users and assign roles')),
                ('can_manage_branches', models.BooleanField(default=False, help_text='Create and manage branches')),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_roles',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),

        # 2. Create UserProfile table
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_ceo', models.BooleanField(
                    default=False,
                    help_text='CEO has full access to all branches and can manage roles/users.'
                )),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('branch', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='staff',
                    to='accounts.branch',
                )),
                ('roles', models.ManyToManyField(
                    blank=True,
                    related_name='users',
                    to='accounts.role',
                )),
            ],
        ),
    ]
