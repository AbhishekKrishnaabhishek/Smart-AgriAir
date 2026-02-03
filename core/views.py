from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Crop, Advisory
import requests
from datetime import datetime

# Default Location: Ludhiana, Punjab (Farming Hub)
DEFAULT_LAT = 30.9010
DEFAULT_LON = 75.8573
DEFAULT_CITY = "Ludhiana"

def get_coordinates(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        res = requests.get(url).json()
        if 'results' in res:
            return res['results'][0]['latitude'], res['results'][0]['longitude'], res['results'][0]['name']
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None, None

def get_weather_data(lat, lon):
    try:
        # Fetch Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,rain&hourly=temperature_2m,rain&forecast_days=1"
        weather_res = requests.get(weather_url).json()
        
        # Fetch AQI
        aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
        aqi_res = requests.get(aqi_url).json()

        return {
            'temp': weather_res.get('current', {}).get('temperature_2m', 0),
            'rain': weather_res.get('current', {}).get('rain', 0.0),
            'aqi': aqi_res.get('current', {}).get('us_aqi', 0),
            'success': True
        }
    except Exception as e:
        print(f"Error fetching API data: {e}")
        return {'temp': 25, 'rain': 0, 'aqi': 100, 'success': False} # Fallback

def generate_dynamic_advisories(data):
    dynamic_advisories = []
    
    # AQI Alerts
    if data['aqi'] > 150:
        dynamic_advisories.append({
            'title': 'Poor Air Quality Alert',
            'content': f"Current AQI is {data['aqi']}. Avoid burning crop residue. Working outdoors? Wear a mask.",
            'severity': 'HIGH',
            'date_posted': datetime.now()
        })
    elif data['aqi'] > 100:
        dynamic_advisories.append({
            'title': 'Moderate Air Quality',
            'content': f"AQI is {data['aqi']}. Sensitive groups should limit outdoor exertion.",
            'severity': 'MEDIUM',
            'date_posted': datetime.now()
        })

    if data['rain'] > 0:
         dynamic_advisories.append({
            'title': 'Rainfall Update',
            'content': f"It is currently raining ({data['rain']} mm). Delay irrigation and spraying.",
            'severity': 'MEDIUM',
            'date_posted': datetime.now()
        })
    
    return dynamic_advisories

def home(request):
    return render(request, 'core/home.html')


@login_required
def dashboard_old_placeholder(request):
    pass

@login_required
def crop_list(request):
    if 'q' in request.GET:
        q = request.GET['q']
        crops = Crop.objects.filter(name__icontains=q, user=request.user)
    else:
        crops = Crop.objects.filter(user=request.user)
    return render(request, 'core/crop_list.html', {'crops': crops})

from .forms import CropForm, PollutionReportForm
from django.shortcuts import render, redirect, get_object_or_404

@login_required
def add_crop(request):
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.user = request.user
            # Auto-populate details
            details = generate_crop_data(crop.name)
            crop.description = details['description']
            crop.optimal_temp_min = details['min_temp']
            crop.optimal_temp_max = details['max_temp']
            crop.water_requirement = details['water']
            crop.soil_type = details['soil']
            crop.fertilizers = details['fertilizers']
            crop.manures = details['manures']
            crop.pesticides = details['pesticides']
            crop.save()
            return redirect('crop_list')
    else:
        form = CropForm()
    return render(request, 'core/add_crop.html', {'form': form})

from django.conf import settings
import google.generativeai as genai
import json

def fetch_wikipedia_summary(query):
    """Fetches the first paragraph from Wikipedia for a given topic."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        headers = {'User-Agent': 'SmartAgriAir/1.0 (aditya@example.com)'}
        res = requests.get(url, headers=headers, timeout=3).json()
        if 'extract' in res:
            return res['extract']
    except Exception as e:
        print(f"Wikipedia API error: {e}")
    return None

def generate_crop_data_gemini(name):
    """Uses Google Gemini to generate comprehensive crop data."""
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or "YOUR_GEMINI_API_KEY" in api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = (
            f"Generate agronomic farming details for the crop '{name}' in VALID JSON format. "
            "Do not use markdown code blocks. The JSON should have these exact keys: "
            "'description' (short summary), 'min_temp' (number), 'max_temp' (number), "
            "'water' (e.g. High/Medium/Low), 'soil' (soil type), "
            "'fertilizers' (specific names), 'manures' (organic types), 'pesticides' (specific chemical/bio names). "
            "Example: {{'description': '...', 'min_temp': 20, ...}}"
        )
        
        # Set a short timeout for the generation context if possible, otherwise rely on exception handling
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up if model adds markdown
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def generate_crop_data(name):
    """Knowledge Engine: Gemini -> Local DB + Wikipedia -> Fallback"""
    name_key = name.lower().strip()
    
    # 1. Try Google Gemini API
    gemini_data = generate_crop_data_gemini(name)
    if gemini_data:
        return gemini_data

    # 2. Fallback: Fetch Description from Wikipedia
    wiki_desc = fetch_wikipedia_summary(name)
    
    # 3. Local Agronomic Database (Backup)
    knowledge_base = {
        # Cereals & Grains
        'wheat': {
            'min': 10, 'max': 25, 'water': 'Medium', 'soil': 'Loamy/Clay',
            'fert': 'Nitrogen: 120kg, Phosphorus: 60kg, Potassium: 40kg per ha', 'manure': 'FYM @ 10-15 tonnes/ha', 'pest': 'Termites: Chlorpyriphos'
        },
        'rice': { # Paddy
            'min': 20, 'max': 35, 'water': 'High', 'soil': 'Clayey/Loam',
            'fert': 'Urea (split), DAP, MOP, Zinc', 'manure': 'Green Manure (Dhaincha)', 'pest': 'Stem Borer: Cartap'
        },
        'maize': { # Corn
            'min': 18, 'max': 32, 'water': 'Medium', 'soil': 'Well-drained Loam',
            'fert': 'NPK 120:60:40 + Zinc', 'manure': 'Cow Dung / Compost', 'pest': 'Fall Armyworm: Emamectin'
        },
        'barley': {
            'min': 12, 'max': 25, 'water': 'Low-Medium', 'soil': 'Sandy Loam',
            'fert': 'NPK 60:30:20', 'manure': 'FYM', 'pest': 'Aphids: Imidacloprid'
        },
        'millet': { # Bajra/Jowar
            'min': 25, 'max': 35, 'water': 'Low', 'soil': 'Sandy/Shallow',
            'fert': 'Nitrogen low requirement', 'manure': 'Organic Mulch', 'pest': 'Shoot Fly: Cypermethrin'
        },

        # Cash Crops
        'sugarcane': {
            'min': 20, 'max': 35, 'water': 'High', 'soil': 'Deep Loam',
            'fert': 'Heavy NPK user + Micronutrients', 'manure': 'Press Mud / Compost', 'pest': 'Top Borer: Carbofuran'
        },
        'cotton': {
            'min': 21, 'max': 35, 'water': 'Medium', 'soil': 'Black Soil',
            'fert': 'NPK 120:60:60', 'manure': 'FYM', 'pest': 'Pink Bollworm: Pheromone Traps'
        },
        'jute': {
            'min': 24, 'max': 35, 'water': 'High', 'soil': 'Alluvial',
            'fert': 'Urea, NPK', 'manure': 'Compost', 'pest': 'Hairy Caterpillar'
        },
        'tobacco': {
            'min': 20, 'max': 30, 'water': 'Medium', 'soil': 'Red/Loamy',
            'fert': 'High Potash, Low Chloride', 'manure': 'Green Manure', 'pest': 'Caterpillars'
        },

        # Vegetables
        'tomato': {
            'min': 18, 'max': 30, 'water': 'Medium', 'soil': 'Sandy Loam',
            'fert': 'NPK 19:19:19, Calcium Nitrate', 'manure': 'Vermicompost', 'pest': 'Whitefly: Acetamiprid'
        },
        'potato': {
            'min': 15, 'max': 25, 'water': 'Medium', 'soil': 'Loose Loam',
            'fert': 'High Potassium (SOP)', 'manure': 'Poultry Manure', 'pest': 'Late Blight: Mancozeb'
        },
        'onion': {
            'min': 12, 'max': 25, 'water': 'Medium', 'soil': 'Friable Loam',
            'fert': 'Sulphur rich fertilizers', 'manure': 'FYM', 'pest': 'Thrips: Fipronil'
        },
        'brinjal': { # Eggplant
            'min': 20, 'max': 30, 'water': 'Medium', 'soil': 'Silt Loam',
            'fert': 'NPK 100:50:50', 'manure': 'Neem Cake', 'pest': 'Fruit Borer: Spinosad'
        },
        'okra': { # Lady Finger
            'min': 22, 'max': 35, 'water': 'Medium', 'soil': 'Sandy Loam',
            'fert': 'Urea, SSP', 'manure': 'Compost', 'pest': 'Jassids/Shoot Borer'
        },
        'cabbage': {
            'min': 15, 'max': 22, 'water': 'Medium', 'soil': 'Loam',
            'fert': 'Nitrogen heavy', 'manure': 'FYM', 'pest': 'Diamond Back Moth'
        },
        'cauliflower': {
            'min': 15, 'max': 22, 'water': 'Medium', 'soil': 'Loam',
            'fert': 'Boron & Molybdenum critical', 'manure': 'Vermicompost', 'pest': 'Aphids'
        },
        'chilli': {
            'min': 20, 'max': 30, 'water': 'Medium', 'soil': 'Black/Loamy',
            'fert': 'NPK + Sulphur', 'manure': 'Neem Cake', 'pest': 'Thrips/Mites'
        },
        'spinach': {
            'min': 10, 'max': 22, 'water': 'Medium', 'soil': 'Loam',
            'fert': 'Urea (Nitrogen)', 'manure': 'Leaf Mould', 'pest': 'Leaf Miner'
        },

        # Fruits
        'mango': {
            'min': 24, 'max': 35, 'water': 'Medium', 'soil': 'Alluvial/Laterite',
            'fert': 'NPK yearly per age', 'manure': 'Bone Meal + FYM', 'pest': 'Hopper: Imidacloprid'
        },
        'banana': {
            'min': 25, 'max': 30, 'water': 'High', 'soil': 'Rich Loam',
            'fert': 'High Potash & Nitrogen', 'manure': 'Compost heap', 'pest': 'Weevil'
        },
        'citrus': { # Lemon/Lime
            'min': 15, 'max': 30, 'water': 'Medium', 'soil': 'Well-drained',
            'fert': 'Micronutrients (Iron/Zinc)', 'manure': 'FYM', 'pest': 'Leaf Miner/Psylla'
        },
        'guava': {
            'min': 20, 'max': 30, 'water': 'Low-Medium', 'soil': 'Any well-drained',
            'fert': 'NPK', 'manure': 'FYM', 'pest': 'Fruit Fly'
        },
        'apple': {
            'min': 5, 'max': 22, 'water': 'Medium', 'soil': 'Hill Soil',
            'fert': 'NPK + Boron', 'manure': 'Compost', 'pest': 'Scab/Mites'
        },
        'papaya': {
            'min': 22, 'max': 32, 'water': 'Medium', 'soil': 'Fertile Loam',
            'fert': 'Frequent Nitrogen', 'manure': 'Vermicompost', 'pest': 'Mealy Bug'
        },

        # Pulses & Legumes
        'chickpea': { # Gram
            'min': 15, 'max': 25, 'water': 'Low', 'soil': 'Sandy Loam',
            'fert': 'DAP (Phosphorus)', 'manure': 'Rhizobium', 'pest': 'Pod Borer'
        },
        'soybean': {
            'min': 25, 'max': 35, 'water': 'Medium', 'soil': 'Well Drained',
            'fert': 'Sulphur + Phosphorus', 'manure': 'Rhizobium', 'pest': 'Girdle Beetle'
        },
        'groundnut': { # Peanut
            'min': 22, 'max': 30, 'water': 'Medium', 'soil': 'Sandy Loam',
            'fert': 'Gypsum (Calcium/Sulphur)', 'manure': 'FYM', 'pest': 'White Grub'
        },
        'mustard': {
            'min': 10, 'max': 25, 'water': 'Medium', 'soil': 'Loam',
            'fert': 'Sulphur (SSP) is key', 'manure': 'FYM', 'pest': 'Aphids'
        },
        'lentil': {
            'min': 15, 'max': 25, 'water': 'Low', 'soil': 'Light Loam',
            'fert': 'DAP', 'manure': 'None usually', 'pest': 'Pod Borer'
        },
        'turmeric': {
            'min': 20, 'max': 35, 'water': 'High', 'soil': 'Loam',
            'fert': 'Heavy Potash', 'manure': 'Heavy Organic Matter', 'pest': 'Rhizome Fly'
        }
    }
    
    # Check for partial matches in local DB
    db_data = None
    for key in knowledge_base:
        if key in name_key:
            db_data = knowledge_base[key]
            break
            
    # Default values if not in DB
    final_data = {
        'description': wiki_desc if wiki_desc else f"A crop named {name}. Add specific description manully.",
        'min_temp': 20, 'max_temp': 30,
        'water': 'Medium', 'soil': 'Loamy',
        'fertilizers': 'Standard NPK 10:10:10',
        'manures': 'General Organic Compost',
        'pesticides': 'Neem Oil (Bio-pesticide)'
    }

    if db_data:
        # If we have specific agronomic data, overlay it
        final_data.update({
             'min_temp': db_data['min'], 'max_temp': db_data['max'],
             'water': db_data['water'], 'soil': db_data['soil'],
             'fertilizers': db_data['fert'], 'manures': db_data['manure'], 'pesticides': db_data['pest']
        })
        
    return final_data

def get_smart_suggestions(crop, lat, lon, city_name="your location"):
    """Generates AI-like suggestions based on live weather vs crop needs"""
    weather = get_weather_data(lat, lon)
    if not weather['success']:
        return ["Unable to fetch live weather data for analysis."]
    
    suggestions = []
    current_temp = weather['temp']
    rain = weather['rain']
    
    # Context Header
    suggestions.append(f"Analysis for **{city_name}** | Temp: {current_temp}°C | Rain: {rain}mm")

    # Temperature Analysis
    if current_temp > crop.optimal_temp_max:
        valid_range = f"{crop.optimal_temp_min}-{crop.optimal_temp_max}°C"
        suggestions.append(f"⚠️ **Heat Stress Alert**: Current temp ({current_temp}°C) is hotter than optimal ({valid_range}). "
                           f"Suggestion: Increase irrigation frequency and apply mulch.")
    elif current_temp < crop.optimal_temp_min:
        valid_range = f"{crop.optimal_temp_min}-{crop.optimal_temp_max}°C"
        suggestions.append(f"❄️ **Cold Stress Alert**: Current temp ({current_temp}°C) is too cold (Optimal: {valid_range}). "
                           f"Suggestion: Use row covers or delay sowing if possible.")
    else:
        suggestions.append(f"✅ Temperature is near optimal ({current_temp}°C). Excellent growth conditions.")

    # Rain Analysis
    if rain > 5:
        suggestions.append(f"🌧️ **Heavy Rain**: {rain}mm rainfall detected. DO NOT irrigate. Check drainage.")
    elif rain > 0:
        suggestions.append(f"☁️ **Light Rain**: {rain}mm rainfall. Skip today's irrigation cycle.")
    elif crop.water_requirement.lower() == 'high':
         suggestions.append("💧 **Water Need**: No rain today and this is a High-water crop. Ensure sufficient irrigation.")

    return suggestions

@login_required
def dashboard(request):
    # Check if city is passed in GET, else check Session, else Default
    if 'city' in request.GET:
        city = request.GET['city']
        lat, lon, found_city = get_coordinates(city)
        if lat:
            # SAVE TO SESSION
            request.session['lat'] = lat
            request.session['lon'] = lon
            request.session['city'] = found_city
            city_display = found_city
        else:
            lat, lon = DEFAULT_LAT, DEFAULT_LON
            city_display = f"{city} (Not Found)"
    else:
        # Load from Session or Default
        lat = request.session.get('lat', DEFAULT_LAT)
        lon = request.session.get('lon', DEFAULT_LON)
        city_display = request.session.get('city', DEFAULT_CITY)

    weather_data = get_weather_data(lat, lon)
    
    db_advisories = list(Advisory.objects.order_by('-date_posted')[:3])
    live_advisories = generate_dynamic_advisories(weather_data)
    all_advisories = live_advisories + db_advisories
    
    context = {
        'aqi': weather_data['aqi'],
        'rainfall': weather_data['rain'],
        'temperature': weather_data['temp'],
        'advisories': all_advisories[:5], 
        'today': datetime.now(),
        'api_status': weather_data['success'],
        'current_city': city_display,
        'tracked_crops': Crop.objects.filter(is_tracked=True, user=request.user)
    }
    return render(request, 'core/dashboard.html', context)

def crop_detail(request, pk):
    try:
        crop = Crop.objects.get(pk=pk)
    except Crop.DoesNotExist:
        crop = None
        
    suggestions = []
    if crop:
        # USE SESSION LOCATION
        lat = request.session.get('lat', DEFAULT_LAT)
        lon = request.session.get('lon', DEFAULT_LON)
        city = request.session.get('city', DEFAULT_CITY)
        
        suggestions = get_smart_suggestions(crop, lat, lon, city)

    return render(request, 'core/crop_detail.html', {'crop': crop, 'suggestions': suggestions})

@login_required
def delete_crop(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    if request.method == 'POST':
        crop.delete()
        return redirect('crop_list')
    return render(request, 'core/crop_confirm_delete.html', {'crop': crop})

def advisory_list(request):
    # In a real app we'd fetch forecast here too for the list
    advisories = Advisory.objects.all().order_by('-date_posted')
    return render(request, 'core/advisory_list.html', {'advisories': advisories})

@login_required
def report_view(request):
    import csv
    from django.http import HttpResponse

    if request.GET.get('download') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="farming_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Type', 'Detail', 'Severity/Value'])
        
        # Write some sample report data (could be historical data in a real app)
        # Using Advisories as a log
        advisories = Advisory.objects.all()
        for adv in advisories:
            writer.writerow([adv.date_posted.strftime("%Y-%m-%d"), 'Advisory', adv.title, adv.severity])
        
        # Add current conditions
        weather = get_weather_data(DEFAULT_LAT, DEFAULT_LON)
        writer.writerow([datetime.now().strftime("%Y-%m-%d"), 'Weather Log', 'Temperature', f"{weather['temp']} C"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d"), 'Weather Log', 'Rainfall', f"{weather['rain']} mm"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d"), 'Environment', 'AQI', weather['aqi']])
        
        return response


    return render(request, 'core/report.html')

@login_required
def report_issue(request):
    if request.method == 'POST':
        form = PollutionReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            return redirect('dashboard') # Or a success page
    else:
        form = PollutionReportForm()
    return render(request, 'core/report_issue.html', {'form': form})
