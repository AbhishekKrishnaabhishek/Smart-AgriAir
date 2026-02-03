from django.contrib import admin
from .models import Crop, Advisory

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('name', 'optimal_temp_min', 'optimal_temp_max', 'water_requirement')
    search_fields = ('name',)

@admin.register(Advisory)
class AdvisoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'date_posted')
    list_filter = ('severity', 'date_posted')
    search_fields = ('title', 'content')
