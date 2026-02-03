from django.urls import path
from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('crops/', views.crop_list, name='crop_list'),
    path('crops/add/', views.add_crop, name='add_crop'),
    path('crops/<int:pk>/', views.crop_detail, name='crop_detail'),
    path('crops/<int:pk>/delete/', views.delete_crop, name='delete_crop'),
    path('advisories/', views.advisory_list, name='advisory_list'),
    path('report/', views.report_view, name='report'),
    path('report-issue/', views.report_issue, name='report_issue'),
    # Admin URLs
    path('admin-panel/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', admin_views.manage_users, name='manage_users'),
    path('admin-panel/users/delete/<int:pk>/', admin_views.delete_user, name='delete_user'),
    path('admin-panel/issues/', admin_views.manage_issues, name='manage_issues'),
    path('admin-panel/issues/update/<int:pk>/', admin_views.update_issue_status, name='update_issue_status'),
]
