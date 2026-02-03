from core.models import Crop
# Delete all existing crops to ensure a fresh start for users
msg = f"Deleting {Crop.objects.count()} existing global crops..."
print(msg)
Crop.objects.all().delete()
print("All crops deleted. Now crops will be user-specific.")
