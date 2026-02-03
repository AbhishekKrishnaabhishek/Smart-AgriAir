from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth import login
from .forms import SignUpForm
from .models import UserProfile

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile for new user
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'FARMER'})
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})
