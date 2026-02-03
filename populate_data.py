import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_agri_air.settings')
django.setup()

from core.models import Crop, Advisory

def populate():
    # Crops
    crops = [
        {
            'name': 'Wheat',
            'description': 'A cereal grain that is a worldwide staple food. Requires cool temperatures.',
            'optimal_temp_min': 12,
            'optimal_temp_max': 25,
            'water_requirement': 'Medium',
            'soil_type': 'Loamy'
        },
        {
            'name': 'Rice',
            'description': 'The seed of the grass species Oryza sativa. Requires high water.',
            'optimal_temp_min': 20,
            'optimal_temp_max': 35,
            'water_requirement': 'High',
            'soil_type': 'Clayey'
        },
        {
            'name': 'Cotton',
            'description': 'A soft, fluffy staple fiber. Requires long frost-free periods.',
            'optimal_temp_min': 18,
            'optimal_temp_max': 30,
            'water_requirement': 'Medium',
            'soil_type': 'Black Soil'
        }
    ]

    for crop_data in crops:
        Crop.objects.get_or_create(name=crop_data['name'], defaults=crop_data)
        print(f"Created crop: {crop_data['name']}")

    # Advisories
    advisories = [
        {
            'title': 'Heavy Rainfall Alert',
            'content': 'Heavy rainfall expected in the next 24 hours. Ensure proper drainage in fields.',
            'severity': 'HIGH'
        },
        {
            'title': 'Pest Warning: Aphids',
            'content': 'Conditions are favorable for Aphid infestation in cotton crops. Inspect fields.',
            'severity': 'MEDIUM'
        },
        {
            'title': 'Sowing Season Starts',
            'content': 'Optimal time for sowing wheat begins next week.',
            'severity': 'LOW'
        }
    ]

    for adv_data in advisories:
        Advisory.objects.get_or_create(title=adv_data['title'], defaults=adv_data)
        print(f"Created advisory: {adv_data['title']}")

if __name__ == '__main__':
    populate()
