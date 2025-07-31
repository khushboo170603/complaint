from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.product_list, name='product_list'),           
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('export/', views.export_products_to_excel, name='export_products'),
]
