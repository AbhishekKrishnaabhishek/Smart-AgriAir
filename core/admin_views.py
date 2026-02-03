from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from core.models import PollutionReport, Crop
from accounts.models import UserProfile
from django.db.models import Count

def is_admin(user):
    """Check if user has admin role"""
    try:
        return user.userprofile.role == 'ADMIN'
    except:
        return False

@login_required
def admin_dashboard(request):
    """Admin analytics dashboard"""
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    # Analytics data
    total_users = User.objects.count()
    total_farmers = UserProfile.objects.filter(role='FARMER').count()
    total_admins = UserProfile.objects.filter(role='ADMIN').count()
    total_crops = Crop.objects.count()
    total_reports = PollutionReport.objects.count()
    pending_reports = PollutionReport.objects.filter(status='PENDING').count()
    
    # Recent data
    recent_crops = Crop.objects.all().select_related('user').order_by('-id')[:10]
    recent_reports = PollutionReport.objects.all().select_related('user').order_by('-date_reported')[:10]
    
    context = {
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_admins': total_admins,
        'total_crops': total_crops,
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'crops': recent_crops,
        'reports': recent_reports,
    }
    
    return render(request, 'admin/admin_dashboard.html', context)

@login_required
def manage_users(request):
    """Manage all users"""
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    users = User.objects.all().select_related('userprofile')
    return render(request, 'admin/manage_users.html', {'users': users})

@login_required
def manage_issues(request):
    """Manage pollution reports"""
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    reports = PollutionReport.objects.all().select_related('user').order_by('-date_reported')
    return render(request, 'admin/manage_issues.html', {'reports': reports})

@login_required
def update_issue_status(request, pk):
    """Update pollution report status"""
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        report = get_object_or_404(PollutionReport, pk=pk)
        new_status = request.POST.get('status')
        if new_status in ['PENDING', 'REVIEWED', 'RESOLVED']:
            report.status = new_status
            report.save()
            messages.success(request, f"Report status updated to {new_status}")
        return redirect('manage_issues')
    
    return redirect('manage_issues')

@login_required
def delete_user(request, pk):
    """Delete a user"""
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        if user != request.user:  # Prevent self-deletion
            user.delete()
            messages.success(request, f"User {user.username} deleted successfully")
        else:
            messages.error(request, "You cannot delete your own account")
        return redirect('manage_users')
    
    return redirect('manage_users')
