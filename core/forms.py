from django import forms
from django import forms
from .models import Crop, PollutionReport

class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['name', 'image', 'planted_date', 'harvested_date', 'is_tracked']
        widgets = {
            'planted_date': forms.DateInput(attrs={'type': 'date'}),
            'harvested_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PollutionReportForm(forms.ModelForm):
    class Meta:
        model = PollutionReport
        fields = ['title', 'location', 'description', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
