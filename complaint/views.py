from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from .forms import ComplaintForm, ComplaintUpdateForm, AddStaffForm, EditStaffForm, ComplaintManagerEditForm
from .sms_utils import send_sms_mock
from .models import Complaint, Profile
from .utils import generate_ticket_number, user_has_role
from django.contrib.auth.views import PasswordChangeView
import random
import string
import openpyxl
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.core.paginator import Paginator
from product.models import Product
from django.utils.timezone import now
from django.contrib.auth.models import Group, User


#landing page
def landing_page(request):
    return render(request, 'landing.html')

# 🔐 Custom Login View with Role-Based Redirection
def custom_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            role = getattr(user.profile, 'role', None)
            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'manager':
                return redirect('manager_dashboard')
            elif role == 'engineer':
                return redirect('engineer_dashboard')
            elif role == 'accountant':
                return redirect('accountant_dashboard')
            elif role == 'customer':
                return redirect('public_complaint_form')
            elif role == 'tally':
                return redirect('tally_dashboard')
            else:
                messages.error(request, "Unknown user role.")
                return redirect('login')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})

# Utility: Generate random ticket number
def generate_ticket_number():
    return ''.join(random.choices(string.digits, k=8))

# Public Complaint Form (no login required)
def public_complaint_form(request):

    base_form_template = "base_public.html"
    back_url = reverse('home')

    if request.method == 'POST':
        form = ComplaintForm(request.POST, show_admin_fields=False)
        if form.is_valid():
            complaint = form.save(commit=False)

            # ✅ Save ticket number
            while True:
                ticket = generate_ticket_number()
                if not Complaint.objects.filter(ticket_number=ticket).exists():
                    break
            complaint.ticket_number = ticket
            complaint.save()

            # ✅ Send SMS
            send_sms_mock(complaint.mobile_number, complaint.ticket_number)

            # Send complaint number email
            subject = "Your Complaint Ticket Number"
            message = render_to_string("emails/complaint_notification_email.txt", {
                'customer_name': complaint.customer_name,
                'ticket_number': complaint.ticket_number,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [complaint.email])

            return render(request, 'complaint/thank_you.html', {
                'ticket_number': ticket,
                'base_form_template': base_form_template,
            })

    else:
        form = ComplaintForm(show_admin_fields=False)

    return render(request, 'complaint/complaint_form.html', {
        'form': form,
        'is_admin': False,
        'base_form_template': base_form_template,
        'back_url': back_url,
    })

@login_required
def user_complaint_form(request):
    form = ComplaintForm(request.POST if request.method == 'POST' else None, show_admin_fields=False)

    # ✅ Define roles 
    is_admin = user_has_role(request.user, 'admin')
    is_engineer = user_has_role(request.user, 'engineer')
    is_manager = user_has_role(request.user, 'manager')
    is_accountant = user_has_role(request.user, 'accountant')
    is_tally = user_has_role(request.user, 'tally')

    # ✅ Set base_form_template dynamically based on role
    if is_admin:
        base_form_template = "base.html"
        back_url = reverse('admin_dashboard')
    elif is_engineer:
        base_form_template = "base_engineer.html"
        back_url = reverse('engineer_dashboard')
    elif is_manager:
        base_form_template = "base_manager.html"
        back_url = reverse('manager_dashboard')
    elif is_accountant:
        base_form_template = "base_accountant.html"
        back_url = reverse('accountant_dashboard')
    elif is_tally:
        base_form_template = "base_tallyuser.html"
        back_url = reverse('tally_dashboard')
    else:
        base_form_template = "base_public.html"
        back_url = reverse('home')

    if request.method == 'POST' and form.is_valid():
        complaint = form.save(commit=False)
        complaint.user = request.user  # Link user

        # ✅ Save ticket number
        while True:
            ticket = generate_ticket_number()
            if not Complaint.objects.filter(ticket_number=ticket).exists():
                break
        complaint.ticket_number = ticket
        complaint.save()

        # ✅ Send SMS
        send_sms_mock(complaint.mobile_number, complaint.ticket_number)

        # Send complaint number email
        subject = "Your Complaint Ticket Number"
        message = render_to_string("emails/complaint_notification_email.txt", {
            'customer_name': complaint.customer_name,
            'ticket_number': complaint.ticket_number,
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [complaint.email])

        return render(request, 'complaint/thank_you.html', {
                'ticket_number': ticket,
                'base_form_template': base_form_template,
        })


    return render(request, 'complaint/complaint_form.html', {
        'form': form,
        'is_admin': False,
        'base_form_template': base_form_template,
        'back_url': back_url,
    })

@login_required
def complaint_form(request):
    return redirect('public_complaint_form')


@login_required
def complaint_list(request):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Only admins can view all complaints.")

    # Handle export via POST, filters via GET
    if request.method == "POST" and request.POST.get("export") == "true":
        search = request.POST.get('search', '')
        status = request.POST.get('status', '')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        unassigned = request.POST.get('unassigned', '')
    else:
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        unassigned = request.GET.get('unassigned', '')

    # Base queryset
    complaints = Complaint.objects.all().order_by('-created_at')

    # Filters
    if search:
        complaints = complaints.filter(
            Q(ticket_number__icontains=search) |
            Q(mobile_number__icontains=search) |
            Q(email__icontains=search)
        )

    if status:
        complaints = complaints.filter(status__iexact=status)

    if from_date:
        complaints = complaints.filter(created_at__date__gte=parse_date(from_date))

    if to_date:
        complaints = complaints.filter(created_at__date__lte=parse_date(to_date))

    # ✅ Filter for unassigned complaints
    if unassigned == 'true':
        complaints = complaints.filter(assigned_engineer__isnull=True)

    # Handle Excel export
    if request.method == "POST" and request.POST.get("export") == "true":
        return export_complaints_to_excel(complaints, role="admin")

    # Pagination
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    complaints_page = paginator.get_page(page_number)

    context = {
        'complaints': complaints_page,
        'search': search,
        'status': status,
        'from_date': from_date,
        'to_date': to_date,
        'unassigned': unassigned,  # Optional, if you want to track in UI
    }

    return render(request, 'complaint/complaint_list.html', context)


@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    return render(request, 'complaint/complaint_detail.html', {
        'complaint': complaint
    })

@login_required
def complaint_edit(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    user = request.user
    is_admin = user_has_role(user, 'admin')
    is_manager = user_has_role(user, 'manager')
    is_accountant = user_has_role(user, 'accountant')

    if not (is_admin or is_manager or is_accountant):
        return HttpResponseForbidden("Only admins, managers, or accountants can edit complaints.")

    form_kwargs = {'instance': complaint, 'user': user}

    if request.method == 'POST':
        #form = ComplaintUpdateForm(request.POST, request.FILES, **form_kwargs)
        if is_manager:
            form = ComplaintManagerEditForm(request.POST, instance=complaint)
        else:
            form = ComplaintUpdateForm(request.POST, request.FILES, **form_kwargs)

        if form.is_valid():
            complaint = form.save(commit=False)

            if is_admin or is_manager:
                # Handle status and assignment logic
                if complaint.assigned_engineer and not complaint.assigned_date:
                    complaint.status = 'in_progress'
                    complaint.assigned_date = now()
                else:
                    complaint.status = 'open'
                    complaint.assigned_date = None

                if complaint.product_serial_number and complaint.service_confirmation_photo:
                    complaint.status = 'resolved'
                    complaint.resolved_date = now()

            if is_accountant or is_admin:
                # Only allow accountant and admin to mark as paid
                if (form.cleaned_data.get('payment_method') == 'cash' and
                    form.cleaned_data.get('mark_cash_paid')):
                    complaint.payment_status = 'paid'

                if (form.cleaned_data.get('payment_method') == 'online' and
                    form.cleaned_data.get('payment_confirmation_photo')):
                    complaint.payment_status = 'paid'

            complaint.save()
            if is_manager:
                return redirect('show_manager_complaints')
            elif is_accountant:
                return redirect('show_accountant_complaints')
            else:
                return redirect('complaint_detail', pk=complaint.pk)

    else:
        if is_manager:
            service_cost_editable = complaint.service_cost is None
            form = ComplaintManagerEditForm(instance=complaint, service_cost_editable=service_cost_editable)
        else:
            form = ComplaintUpdateForm(**form_kwargs)
            service_cost_editable = False

    # ✅ Set base_template dynamically based on role
    if is_admin:
        base_template = "base.html"
        template_name = 'complaint/complaint_edit.html'
    elif is_manager:
        base_template = "base_manager.html"
        template_name = 'complaint/edit_complaint_by_manager.html'
    elif is_accountant:
        base_template = "base_accountant.html"
        template_name = 'complaint/complaint_edit.html'
    else:
        base_template = "base_public.html"
        template_name = 'complaint/complaint_edit.html'

    return render(request, template_name, {
        'form': form,
        'complaint': complaint,
        'base_template': base_template,
        'service_cost_editable': service_cost_editable,
    })

@login_required
def update_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if not (user_has_role(request.user, 'admin') or complaint.assigned_engineer == request.user):
        return HttpResponseForbidden("You are not authorized to update this complaint.")

    form_kwargs = {'instance': complaint, 'user': request.user}

    if request.method == 'POST':
        form = ComplaintUpdateForm(request.POST, request.FILES, **form_kwargs)
        if form.is_valid():
            complaint = form.save(commit=False)

            # Auto-set In Progress when engineer assigned (initial assignment handled elsewhere)
            if complaint.assigned_engineer and not complaint.assigned_date:
                complaint.status = 'in_progress'
                complaint.assigned_date = now()
            else:
                # Unassigned case: Reset status and date
                complaint.status = 'open'
                complaint.assigned_date = None


            # Auto-set Resolved when serial number + service photo uploaded
            if complaint.product_serial_number and complaint.service_confirmation_photo:
                complaint.status = 'resolved'
                complaint.resolved_date = now()

            # Engineer can't change status manually

            complaint.save()
            return redirect('complaint_list' if user_has_role(request.user, 'admin') else 'engineer_dashboard')
    else:
        form = ComplaintUpdateForm(**form_kwargs)

    return render(request, 'complaint/update_complaint.html', {
        'form': form,
        'complaint': complaint
    })

def export_complaints_to_excel(queryset, role=None, username=None):
    import openpyxl
    from datetime import datetime

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Complaints"

    # Define headers based on role
    if role == "accountant":
        headers = ["Ticket No", "Customer Name", "Email", 'Mobile Number', "Product", 'Issue Type', "Status", "Engineer", "Service Cost", "Payment Mode", "Created At"]
    else:
        headers = ["Ticket No", "Customer Name", "Email", 'Mobile Number', "Product", 'Issue Type', "Status", "Engineer", "Created At"]
    
    ws.append(headers)

    for obj in queryset:
        row = [
            obj.ticket_number,
            obj.customer_name,
            obj.email or '',
            obj.mobile_number,
            obj.product.name if obj.product else 'Other',
            obj.issue_type,
            #obj.status,
            obj.get_status_display(),
            getattr(obj.assigned_engineer, 'username', 'Not Assigned'),
        ]

        if role == "accountant":
            row.extend([
                obj.service_cost if hasattr(obj, 'service_cost') else '',
                obj.payment_method if hasattr(obj, 'payment_method') else '',
            ])

        row.append(obj.created_at.strftime("%Y-%m-%d %H:%M"))
        ws.append(row) 

    # Generate file name based on role and time
    filename = f"{role or 'complaints'}_export_{username or 'user'}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response

# Admin Dashboard
@login_required
def admin_dashboard(request):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Admins only.")

    context = {
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status__iexact='Pending').count(),
        'not_assigned_complaints': Complaint.objects.filter(assigned_engineer__isnull=True).count(),
        'total_staff': Profile.objects.count(),
        'total_products': Product.objects.count(), 
    }

    return render(request, 'dashboards/admin_dashboard.html', context)

#  Engineer Dashboard
@login_required
def engineer_dashboard(request):
    user = request.user
    total_assigned = Complaint.objects.filter(assigned_engineer=user).count()
    pending_count = Complaint.objects.filter(assigned_engineer=user, status__iexact='Pending').count()
    resolved_count = Complaint.objects.filter(assigned_engineer=user, status__iexact='Resolved').count()
    pending_payments = Complaint.objects.filter(assigned_engineer=user, payment_status__iexact='Pending').count()

    return render(request, 'dashboards/engineer_dashboard.html', {
        'total_assigned': total_assigned,
        'pending_count': pending_count,
        'resolved_count': resolved_count,
        'pending_payments': pending_payments,
    })

@login_required 
def engineer_assigned_complaints(request):
    if not user_has_role(request.user, 'engineer'):
        return HttpResponseForbidden("Only engineers can view assigned complaints.")

    # Get filters from query parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Filter complaints assigned to the engineer
    complaints = Complaint.objects.filter(assigned_engineer=request.user).select_related('product').order_by('-created_at')

    # Apply search filter (product name or issue type)
    if search_query:
        complaints = complaints.filter(
        Q(ticket_number__icontains=search_query) |
        Q(mobile_number__icontains=search_query) |
        Q(customer_name__icontains=search_query)
        )

    # Apply status filter
    if status_filter:
        complaints = complaints.filter(status__iexact=status_filter)

    # Apply date range filter (filter by created_at)
    if start_date:
        complaints = complaints.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        complaints = complaints.filter(created_at__date__lte=parse_date(end_date))

    complaints = complaints.order_by('-created_at')

    # Paginate
    paginator = Paginator(complaints, 10)  # 10 complaints per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'complaint/engineer_assigned_list.html', {
        'complaints': complaints,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date
    })

# Manager Dashboard
@login_required
def manager_dashboard(request):
    if not user_has_role(request.user, 'manager'):
        return HttpResponseForbidden("Service managers only.")

    context = {
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status__iexact='Pending').count(),
        'inprogress_complaints': Complaint.objects.filter(status__iexact='In_Progress').count(),
        'resolved_complaints': Complaint.objects.filter(status__iexact='Resolved').count(),
    }

    return render(request, 'dashboards/manager_dashboard.html', context)

@login_required
def show_manager_complaints(request):
    if not user_has_role(request.user, 'manager'):
        return HttpResponseForbidden("Service managers only.")

    complaints = Complaint.objects.all().order_by('-created_at')

    # Filters
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if search:
        complaints = complaints.filter(
            Q(ticket_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(product__model_name__icontains=search)
        )

    if status:
        complaints = complaints.filter(status__iexact=status)

    if from_date:
        complaints = complaints.filter(created_at__date__gte=parse_date(from_date))
    if to_date:
        complaints = complaints.filter(created_at__date__lte=parse_date(to_date))

    # Export to Excel
    if 'export' in request.GET:
        return export_complaints_to_excel(complaints, role="manager", username=request.user.username)

    # Pagination
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'complaint/show_manager_complaints.html', {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'from_date': from_date,
        'to_date': to_date,
    })

@login_required
def edit_complaint_by_manager(request, complaint_id):
    if not user_has_role(request.user, 'manager'):
        return HttpResponseForbidden("Only managers can perform this action.")

    complaint = get_object_or_404(Complaint, id=complaint_id)
    service_cost_editable = complaint.service_cost is None

    if request.method == 'POST':
        form = ComplaintManagerEditForm(request.POST, instance=complaint, service_cost_editable=service_cost_editable)
        if form.is_valid():
            complaint = form.save(commit=False)

            # ✅ Automatically update status and dates based on business rules
            if complaint.assigned_engineer and not complaint.assigned_date:
                complaint.status = 'in_progress'
                complaint.assigned_date = now()
            else:
                # Unassigned case: Reset status and date
                complaint.status = 'open'
                complaint.assigned_date = None

            if complaint.product_serial_number and complaint.service_confirmation_photo:
                complaint.status = 'resolved'
                complaint.resolved_date = now()

            complaint.save()
            messages.success(request, "Complaint updated successfully.")
            return redirect('show_manager_complaints')  # Adjust this redirect as needed
    else:
        form = ComplaintManagerEditForm(instance=complaint, service_cost_editable=service_cost_editable)

    return render(request, 'complaint/edit_complaint_by_manager.html', {
        'form': form,
        'complaint': complaint,
        'service_cost_editable': service_cost_editable,
    })

# Accountant Dashboard
@login_required
def accountant_dashboard(request):
    if not user_has_role(request.user, 'accountant'):
        return HttpResponseForbidden("Accountants only.")

    context = {
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status__iexact='Pending').count(),
        'inprogress_complaints': Complaint.objects.filter(status__iexact='In_Progress').count(),
        'resolved_complaints': Complaint.objects.filter(status__iexact='resolved').count(),
    }

    return render(request, 'dashboards/accountant_dashboard.html', context)

@login_required
def show_accountant_complaints(request):
    if not user_has_role(request.user, 'accountant'):
        return HttpResponseForbidden("Accountants only.")

    complaints = Complaint.objects.all().order_by('-created_at')

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if search:
        complaints = complaints.filter(
            Q(ticket_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(product__model_name__icontains=search)
        )

    if status:
        complaints = complaints.filter(status__iexact=status)

    if from_date:
        complaints = complaints.filter(created_at__date__gte=parse_date(from_date))
    if to_date:
        complaints = complaints.filter(created_at__date__lte=parse_date(to_date))

    if 'export' in request.GET:
        return export_complaints_to_excel(complaints, role="accountant", username=request.user.username)

    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'complaint/show_accountant_complaints.html', {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'from_date': from_date,
        'to_date': to_date,
    })

# tally dashboard
@login_required
def tally_dashboard(request):
    if not user_has_role(request.user, 'tally'):
        return HttpResponseForbidden("Tally users only.")

    context = {
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status__iexact='Pending').count(),
        'inprogress_complaints': Complaint.objects.filter(status__iexact='In_Progress').count(),
        'resolved_complaints': Complaint.objects.filter(status__iexact='resolved').count(),
    }

    return render(request, 'dashboards/tally_dashboard.html', context)

@login_required
def show_tally_complaints(request):
    if not user_has_role(request.user, 'tally'):
        return HttpResponseForbidden("Tally users only.")

    complaints = Complaint.objects.all().order_by('-created_at')

    # Filters
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if search:
        complaints = complaints.filter(
            Q(ticket_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(product__model_name__icontains=search)
        )

    if status:
        complaints = complaints.filter(status__iexact=status)

    if from_date:
        complaints = complaints.filter(created_at__date__gte=parse_date(from_date))
    if to_date:
        complaints = complaints.filter(created_at__date__lte=parse_date(to_date))

    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'complaint/show_tally_complaints.html', {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'from_date': from_date,
        'to_date': to_date,
    })

# Landing Page + Role-Based Redirection at /
def redirect_by_role(request):
    if request.user.is_authenticated:
        role = getattr(request.user.profile, 'role', None)

        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'manager':
            return redirect('manager_dashboard')
        elif role == 'engineer':
            return redirect('engineer_dashboard')
        elif role == 'accountant':
            return redirect('accountant_dashboard')
        elif role == 'tally':
            return redirect('tally_dashboard')
        elif role == 'customer':
            return redirect('public_complaint_form')
        else:
            messages.error(request, "Unknown or undefined role.")
            return redirect('login')

    # If not logged in → go to landing page
    return render(request, 'landing.html')

def add_staff(request):
    if request.method == 'POST':
        form = AddStaffForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Ensure single role
            user.groups.clear()

            # Assign role to Profile (Critical)
            role = form.cleaned_data['role']
            Profile.objects.update_or_create(user=user, defaults={'role': role})

            # Optional: Groups logic (if you're using groups)
            user.groups.clear()
            group, created = Group.objects.get_or_create(name=role)
            user.groups.add(group)

            messages.success(request, "Staff user created successfully.")
            return redirect('add_staff')
    else:
        form = AddStaffForm()

    # Clear initial data to avoid pre-filling with logged-in admin's data
    form.initial = {}
 
    return render(request, 'complaint/add_staff.html', {'form': form})

def show_staff(request):
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')

    staff_users = User.objects.filter(is_staff=True)

    if query:
        staff_users = staff_users.filter(username__icontains=query) | staff_users.filter(email__icontains=query)

    if role_filter:
        staff_users = staff_users.filter(groups__name=role_filter)

    # Pagination
    paginator = Paginator(staff_users.distinct(), 10)  # 10 users per page
    page_number = request.GET.get('page')
    staff_page = paginator.get_page(page_number)

    # Handle export (before pagination)
    if 'export' in request.GET:
        return export_staff_to_excel(staff_users)

    roles = Group.objects.all().order_by('name')

    return render(request, 'complaint/show_staff.html', {
        'staff_users': staff_page,
        'roles': roles,
        'query': query,
        'role_filter': role_filter,
    })

def export_staff_to_excel(staff_users):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Staff List"
    ws.append(['Name', 'Email', 'Role'])

    for user in staff_users:
        role_names = ', '.join([group.name.capitalize() for group in user.groups.all()]) or 'Not Assigned'
        ws.append([user.username, user.email, role_names])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=staff_list.xlsx'
    wb.save(response)
    return response

def delete_staff(request, user_id):
    user = User.objects.get(id=user_id)
    if user.is_superuser:
        return HttpResponse("Cannot delete superuser.")
    user.delete()
    return redirect('show_staff')

def edit_staff(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = EditStaffForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()

            # Ensure single role
            user.groups.clear()

            # Assign selected role
            role = form.cleaned_data['role']
            group, created = Group.objects.get_or_create(name=role)
            user.groups.add(group)

            messages.success(request, "Staff user updated successfully.")
            return redirect('show_staff')  # or any other appropriate page
    else:
        # Set initial role manually
        initial_role = user.groups.first().name if user.groups.exists() else ''
        form = EditStaffForm(instance=user, initial={'role': initial_role})

    return render(request, 'complaint/edit_staff.html', {'form': form, 'user': user})

@login_required
def change_password(request):

    user = request.user

    is_admin = user_has_role(user, 'admin')
    is_manager = user_has_role(user, 'manager')
    is_accountant = user_has_role(user, 'accountant')
    is_engineer = user_has_role(user, 'engineer')
    is_tally = user_has_role(user, 'tally')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Prevent logout after password change
            messages.success(request, "Password changed successfully.")
        
            if is_admin:
                return redirect('admin_dashboard')
            elif is_manager:
                return redirect('manager_dashboard')
            elif is_accountant:
                return redirect('accountant_dashboard')
            elif is_engineer:
                return redirect('engineer_dashboard')
            elif is_tally:
                return redirect('tally_dashboard')
            else:
                return redirect('login')
            
            
    else:
        form = PasswordChangeForm(request.user)

    # ✅ Set base_template dynamically based on role
    if is_admin:
        base_template = "base.html"
    elif is_manager:
        base_template = "base_manager.html"
    elif is_accountant:
        base_template = "base_accountant.html"
    elif is_engineer:
        base_template = "base_engineer.html"
    elif is_tally:
        base_template = "base_tallyuser.html"
    else:
        base_template = "base_public.html"

    return render(request, 'registration/change_password.html', 
        {'form': form, 
         'base_template': base_template}
    )

#from django.contrib.auth.forms import PasswordResetForm
from .forms import CustomPasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

def send_password_reset_email_view(request):
   
    print("Custom password reset view called")

    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(username=username, email=email)
            except User.DoesNotExist:
                user = None

            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm_custom', kwargs={'uidb64': uid, 'token': token})
                )

                subject = "Password Reset Requested"
                message = render_to_string("emails/reset_email.txt", {
                    'user': user,
                    'reset_url': reset_url,
                })

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            return redirect('password_reset_done_custom')
    else:
        form = CustomPasswordResetForm()

    # Use a unique template name to avoid conflict with admin templates
    return render(request, 'registration/custom_password_reset_form.html', {'form': form})

from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import get_user_model

def password_reset_confirm_view(request, uidb64, token):
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.tokens import default_token_generator

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('password_reset_complete_custom')
        else:
            form = SetPasswordForm(user)
        return render(request, 'registration/custom_password_reset_confirm.html', {'form': form})
    else:
        return render(request, 'registration/custom_password_reset_invalid.html')

def password_reset_done_view(request):
    return render(request, 'registration/custom_password_reset_done.html')

def password_reset_complete_view(request):
    return render(request, 'registration/custom_password_reset_complete.html')

