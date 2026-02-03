"""
Script to create UserProfile for all existing users
Run this with: Get-Content fix_profiles.py | .\env\Scripts\python.exe manage.py shell
"""

from django.contrib.auth.models import User
from accounts.models import UserProfile

users = User.objects.all()
created_count = 0

for user in users:
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'FARMER'}
    )
    if created:
        created_count += 1
        print(f"✓ Created UserProfile for {user.username}")
    else:
        print(f"✓ UserProfile already exists for {user.username} (Role: {profile.role})")

print(f"\n=== Summary ===")
print(f"Total users: {users.count()}")
print(f"Profiles created: {created_count}")
print(f"================\n")
