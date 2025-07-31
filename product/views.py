from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
import openpyxl

from product.models import Product
from complaint.utils import user_has_role
from .forms import ProductForm


@login_required
def product_list(request):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Only admins can view product list.")

    query = request.GET.get('q', '')
    products = Product.objects.all().order_by('-id')

    if query:
        products = products.filter(
            Q(serial_number__icontains=query) |
            Q(model_name__icontains=query)
        )

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'product/product_list.html', {
        'page_obj': page_obj,
        'query': query
    })


@login_required
def add_product(request):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Only admins can add products.")

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully.")
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'product/add_product.html', {'form': form})


@login_required
def edit_product(request, product_id):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Only admins can edit products.")

    product = get_object_or_404(Product, id=product_id)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect('product_list')

    return render(request, 'product/edit_product.html', {'form': form, 'product': product})


@login_required
def delete_product(request, product_id):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Only admins can delete products.")

    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('product_list')


@login_required
def export_products_to_excel(request):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Only admins can export products.")

    query = request.GET.get('q', '')
    products = Product.objects.all().order_by('-id')

    if query:
        products = products.filter(
            Q(serial_number__icontains=query) |
            Q(model_name__icontains=query)
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"

    headers = [
        "Serial Number",
        "Model Name",
        "Sold To",
        "Sold Date",
        "Installation Date",
        "Assigned Engineer",
        "Warranty Start",
        "Warranty End"
    ]
    ws.append(headers)

    for product in products:
        ws.append([
            product.serial_number,
            product.model_name,
            product.sold_to,
            product.sold_date.strftime('%Y-%m-%d') if product.sold_date else '',
            product.installation_date.strftime('%Y-%m-%d') if product.installation_date else '',
            str(product.assigned_engineer) if product.assigned_engineer else '',
            product.warranty_start.strftime('%Y-%m-%d') if product.warranty_start else '',
            product.warranty_end.strftime('%Y-%m-%d') if product.warranty_end else ''
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=products.xlsx'
    wb.save(response)
    return response
