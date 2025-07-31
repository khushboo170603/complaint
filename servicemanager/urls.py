from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from complaint import views  # Import views for landing page

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth views (Django default + custom)
    #path('accounts/', include('django.contrib.auth.urls')),  # for password reset, etc.

    path('login/', views.custom_login_view, name='login'),   # custom login
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # ✅ this line added
    path('change_password/', views.change_password, name='change_password'),
    
    # Landing page
    path('', views.landing_page, name='landing_page'),

    # Password Reset URLs
    path('forgot-password/', views.send_password_reset_email_view, name='password_reset_custom'),
    path('password-reset-done/', views.password_reset_done_view, name='password_reset_done_custom'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm_custom'),
    path('password-reset-complete/', views.password_reset_complete_view, name='password_reset_complete_custom'),

    # Complaint app URLs
    path('complaint/', include('complaint.urls')),

    # Product app URLs
    path('products/', include('product.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
