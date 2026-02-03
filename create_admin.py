"""
Script to create an admin user for the AgriAir system.
Run this with: python manage.py shell < create_admin.py
"""

from django.contrib.auth.models import User
from accounts.models import UserProfile

# Admin credentials
username = "admin"
email = "admin@agriair.com"
password = "admin123"  # Change this to a secure password

# Create or get admin user
user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email, 'is_staff': True, 'is_superuser': True}
)

if created:
    user.set_password(password)
    user.save()
    print(f"✓ Created admin user: {username}")
else:
    print(f"✓ Admin user already exists: {username}")

# Create or update UserProfile
profile, created = UserProfile.objects.get_or_create(
    user=user,
    defaults={'role': 'ADMIN'}
)

if not created and profile.role != 'ADMIN':
    profile.role = 'ADMIN'
    profile.save()
    print(f"✓ Updated {username} role to ADMIN")
elif created:
    print(f"✓ Created ADMIN profile for {username}")
else:
    print(f"✓ {username} already has ADMIN role")

print(f"\n=== Admin Login Credentials ===")
print(f"Username: {username}")
print(f"Password: {password}")
print(f"================================\n")
