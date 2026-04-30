from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction


class Command(BaseCommand):
    help = "Bootstrap emergency superuser, Admin group, and sample admin users."

    def add_arguments(self, parser):
        parser.add_argument('--superuser', action='store', help='Superuser username', default='super_admin')
        parser.add_argument('--email', action='store', help='Superuser email', default='ops@example.com')
        parser.add_argument('--password', action='store', help='Superuser password', default='ChangeMe!123')
        parser.add_argument('--create-samples', action='store_true', help='Create sample admin users')

    def handle(self, *args, **options):
        User = get_user_model()
        su_username = options['superuser']
        email = options['email']
        password = options['password']
        create_samples = options['create_samples']

        with transaction.atomic():
            # Superuser
            if not User.objects.filter(username=su_username).exists():
                User.objects.create_superuser(username=su_username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f'Created superuser: {su_username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Superuser {su_username} already exists'))

            # Admin group + permissions
            admin_group, created = Group.objects.get_or_create(name='Admin')
            perm_codenames = ['add_user', 'change_user', 'delete_user', 'view_user']
            perms = Permission.objects.filter(codename__in=perm_codenames)
            admin_group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f'Configured Admin group with perms: {perm_codenames}'))

            # Optional sample admin users
            if create_samples:
                samples = [
                    ('admin_jane', 'jane.admin@hospital.com', 'Jane', 'Admin'),
                    ('admin_mark', 'mark.admin@hospital.com', 'Mark', 'Admin'),
                ]
                for username, email_s, first, last in samples:
                    if User.objects.filter(username=username).exists():
                        self.stdout.write(self.style.WARNING(f'{username} exists, skipping'))
                        continue
                    u = User.objects.create_user(
                        username=username,
                        email=email_s,
                        password='ChangeMe!123',
                        role='admin',
                        first_name=first,
                        last_name=last
                    )
                    # User.save() will set is_staff and is_superuser correctly for role='admin'
                    u.groups.add(admin_group)
                    self.stdout.write(self.style.SUCCESS(f'Created admin user {username}'))

        self.stdout.write(self.style.SUCCESS('Bootstrapping complete'))
