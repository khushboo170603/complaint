from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 🌐 Landing or Auto Redirect to Dashboard
    path('', views.redirect_by_role, name='home'),

    # 🆓 Public Complaint Form (No login required)
    path('submit/', views.public_complaint_form, name='public_complaint_form'),
    path('complaint/add/', views.user_complaint_form, name='user_complaint_form'),

    # 🔐 Auth: Login + Logout + change password
    path('login/', views.custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # 🧰 Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/engineer/', views.engineer_dashboard, name='engineer_dashboard'),
    path('dashboard/accountant/', views.accountant_dashboard, name='accountant_dashboard'),
    path('dashboard/tally/', views.tally_dashboard, name='tally_dashboard'),

    # 🗂 Complaint Views
    path('complaints/', views.complaint_list, name='complaint_list'),  # Admin-only
    path('complaints/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('complaints/<int:pk>/edit/', views.complaint_edit, name='complaint_edit'),
    path('update/<int:complaint_id>/', views.update_complaint, name='update_complaint'),

    # 📋 Engineer: Assigned Complaints List
    path('engineer/assigned-complaints/', views.engineer_assigned_complaints, name='engineer_assigned_complaints'),

    path('manager/complaints/', views.show_manager_complaints, name='show_manager_complaints'),
    path('accountant/complaints/', views.show_accountant_complaints, name='show_accountant_complaints'),
    path('tally/complaints/', views.show_tally_complaints, name='show_tally_complaints'),

    #fresh
    path('complaint/edit/<int:complaint_id>/', views.edit_complaint_by_manager, name='edit_complaint_by_manager'),

    # 👤 Staff Management
    path('add-staff/', views.add_staff, name='add_staff'),
    path('show-staff/', views.show_staff, name='show_staff'),
    path('delete-staff/<int:user_id>/', views.delete_staff, name='delete_staff'),
    path('staff/edit/<int:user_id>/', views.edit_staff, name='edit_staff'),
]
