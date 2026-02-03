from django.db import models
from django.contrib.auth.models import User

class Crop(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    optimal_temp_min = models.FloatField(help_text="Minimum optimal temperature in Celsius")
    optimal_temp_max = models.FloatField(help_text="Maximum optimal temperature in Celsius")
    water_requirement = models.CharField(max_length=100, help_text="e.g., High, Medium, Low")
    soil_type = models.CharField(max_length=100)
    fertilizers = models.TextField(blank=True, help_text="Recommended fertilizers", default="Balanced NPK 10:10:10")
    manures = models.TextField(blank=True, help_text="Recommended manures", default="Farm Yard Manure")
    pesticides = models.TextField(blank=True, help_text="Recommended pesticides", default="Neem Oil")
    image = models.ImageField(upload_to='crops/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Tracking Features
    planted_date = models.DateField(null=True, blank=True, help_text="Date when the crop was planted")
    harvested_date = models.DateField(null=True, blank=True, help_text="Expected or actual harvest date")
    is_tracked = models.BooleanField(default=False, help_text="Show this crop on the dashboard for daily tracking")

    def __str__(self):
        return self.name

class Advisory(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High')
    ], default='LOW')

    def __str__(self):
        return self.title

class PollutionReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True, help_text="e.g. Village Name or Coordinates")
    image = models.ImageField(upload_to='pollution_reports/', blank=True, null=True)
    date_reported = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved')
    ], default='PENDING')

    def __str__(self):
        return f"{self.title} - {self.status}"

