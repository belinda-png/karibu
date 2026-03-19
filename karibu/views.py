from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, Q
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.core.paginator import Paginator

# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from .forms import UserCreationForm
from .models import Receipt
from django.db.models import Sum, Q, Avg
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from .models import *
from .forms import *
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login

from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout



# Custom decorator for role-based permissions
def index(request):
    # Landing page showing featured products
    featured_products = Stock.objects.filter(product_quantity__gt=0).order_by('-date_added')[:6]
    context = {
        'featured_products': featured_products,
    }
    return render(request, "index.html", context)


def is_manager_check(user):  # Proper alignment
    # Check if the user is a manager
    return user.is_manager  #


def is_salesagent_check(user):  # Proper alignment
    # Check if the user is a sales agent
    return user.is_salesagent


def is_owner_check(user):
    # Check if the user is an owner
    return user.is_owner


def home(request):
    return render(request, "home.html")


def allstock(request):
    if request.user.is_authenticated:
        # Owners can see all branches, others see only their assigned branches
        if request.user.is_owner:
            stocks = Stock.objects.all()
        else:
            # Check if the user has any associated branches
            user_branches = request.user.branches.all()

            if user_branches.exists():
                # Filter stocks based on the user's branches
                stocks = Stock.objects.filter(branch__in=user_branches)
            else:
                # If no branches are associated, return an empty queryset or handle accordingly
                stocks = Stock.objects.none()
    else:
        # Handle the case where the user is not authenticated
        stocks = Stock.objects.none()

    return render(request, "allstock.html", {"stocks": stocks})


# @login_required
# @role_required(['owner', 'manager'])
def addstock(request):
    if request.method == "POST":
        form = AddStockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Stock added successfully!")
            return redirect("allstock")
    else:
        form = AddStockForm()
    return render(request, "addstock.html", {"form": form})


# @login_required
# @role_required(['owner', 'manager'])
def viewstock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    return render(request, "viewstock.html", {"stock": stock})


# @login_required
# @role_required(['owner', 'manager'])
def editstock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    if request.method == "POST":
        form = AddStockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, "Stock updated successfully!")
            return redirect("allstock")
    else:
        form = AddStockForm(instance=stock)
    return render(request, "editstock.html", {"form": form, "stock": stock})


def deletestock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    if request.method == "POST":
        stock.delete()
        return redirect("allstock")
    return render(request, "deletestock.html", {"stock": stock})


def makesale(request):
    # Show product gallery for sales
    if request.method == "POST":
        form = AddSaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.sales_agent = request.user
            sale.save()
            return redirect("receipt", sale_id=sale.id)
    else:
        form = AddSaleForm()
    
    # Get all available products for the gallery
    products = Stock.objects.filter(product_quantity__gt=0).select_related('category_name')
    
    context = {
        'form': form,
        'products': products,
    }
    return render(request, "sell_item.html", context)


def save(self, commit=True):
    instance = super().save(commit=False)
    if instance.product_quantity and instance.unit_price:
        instance.amount_recieved = instance.product_quantity * instance.unit_price
    if commit:
        instance.save()
    return instance


# In forms.py
def clean(self):
    cleaned_data = super().clean()
    payment_method = cleaned_data.get("payment_method")
    amount_paid = cleaned_data.get("amount_paid")

    if payment_method == "Cash" and not amount_paid:
        raise forms.ValidationError("Amount paid is required for cash payments")

    return cleaned_data


def add_sale(request):
    if request.method == "POST":
        form = AddSaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.branch = request.user.branch
            sale.save()
            return redirect("sales_list")
    else:
        form = AddSaleForm()
    return render(request, "add_sale.html", {"form": form})


def branch_sales(request, branch_name):
    branch = Branch.objects.get(name=branch_name)
    sales = Sale.objects.filter(branch=branch)
    return render(request, "branch_sales.html", {"sales": sales})


def saleslist(request):
    if request.user.is_authenticated:
        # Owners can see all branches, others see only their assigned branches
        if request.user.is_owner:
            sales = Sale.objects.all().order_by("-sales_date")
        else:
            # Check if the user has any associated branches
            user_branches = request.user.branches.all()

            if user_branches.exists():
                # Filter sales based on the user's branches
                sales = Sale.objects.filter(branch__in=user_branches).order_by(
                    "-sales_date"
                )
            else:
                # If no branches are associated, return an empty queryset or handle accordingly
                sales = Sale.objects.none()
    else:
        # Handle the case where the user is not authenticated
        sales = Sale.objects.none()

    return render(request, "saleslist.html", {"sales": sales})


# @login_required


def receipt(request, sale_id):
    sale = Sale.objects.get(id=sale_id)

    return render(request, "receipt.html", {"sale": sale})


def custom_sales_report(request):
    sales = []
    total_amount = 0
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            sales = Sale.objects.filter(sales_date__date__range=(start, end))
            total_amount = sales.aggregate(total=+("amount_received"))["total"] or 0
        except ValueError:
            pass  # ignore invalid dates silently for now

    return render(
        request,
        "custom_report.html",
        {
            "sales": sales,
            "total_amount": total_amount,
        },
    )


# # @login_required
# # @role_required(['owner'])
def manage_credits(request):
    credits = Credit.objects.all()
    return render(request, "manage_credits.html", {"credits": credits})


# @login_required
# @role_required(['owner'])
def add_credit(request):
    if request.method == "POST":
        form = AddCreditForm(request.POST)
        if form.is_valid():
            credit = form.save(commit=False)
            credit.approved_by = request.user
            credit.save()
            messages.success(request, "Credit added successfully!")
            return redirect("manage_credits")
    else:
        form = AddCreditForm()
    return render(request, "add_credit.html", {"form": form})




from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")  # Checkbox for "Remember Me"

        # Basic validation
        if not username or not password:
            messages.error(request, "Please provide both username and password")
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)


        if not remember_me:
            request.session.set_expiry(0)  # Session expires on browser close
        else:
            request.session.set_expiry(1209600)  # Session expires in 2 weeks



        if user is not None:
            login(request, user)

            # Handle 'next' parameter for redirects after login
            next_url = request.POST.get("next") or request.GET.get("next")

            # Role-based redirect with fallbacks
            if next_url:
                return redirect(next_url)
            elif user.is_owner:
                return redirect("owner_dashboard")
            elif user.is_manager:
                return redirect("manager_dashboard")
            elif user.is_salesagent:
                return redirect("salesagent_dashboard")
            else:
                return redirect("home")  # Or your default landing page
        else:
            messages.error(request, "Invalid username or password")

    # Include next parameter in context for the template
    return render(request, "login.html", {"next": request.GET.get("next", "")})


def home(request):
    # Your home view logic
    return render(request, "index.html")


@login_required
@user_passes_test(lambda u: u.is_owner)
def owner_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # Today's date
    today = timezone.now().date()
    
    # Get all branches for the system admin
    all_branches = Branch.objects.all()
    
    # 1. TOTAL PRODUCTS across all branches
    total_products = Stock.objects.count()
    
    # 2. LOW STOCK ALERTS across all branches (items with quantity < 10)
    low_stock_items = Stock.objects.filter(product_quantity__lt=10)
    low_stock_alerts = low_stock_items.count()
    
    # 3. SALES TODAY across all branches
    todays_sales = Sale.objects.filter(sales_date__date=today)
    sales_today_count = todays_sales.count()
    
    # 4. REVENUE TODAY across all branches
    revenue_today = 0
    for sale in todays_sales:
        revenue_today += sale.get_sales()
    
    # Branch Overview Data
    branch_overview = []
    for branch in all_branches:
        # Products count for this branch
        branch_products = Stock.objects.filter(branch=branch).count()
        
        # Staff count for this branch (users with access to this branch)
        branch_staff = User_profile.objects.filter(branches=branch).count()
        
        # Daily revenue for this branch
        branch_todays_sales = Sale.objects.filter(branch=branch, sales_date__date=today)
        branch_daily_revenue = 0
        for sale in branch_todays_sales:
            branch_daily_revenue += sale.get_sales()
        
        # Low stock items for this branch
        branch_low_stock = Stock.objects.filter(branch=branch, product_quantity__lt=10)
        
        branch_overview.append({
            'name': branch.name,
            'products': branch_products,
            'staff': branch_staff,
            'daily_revenue': branch_daily_revenue,
            'low_stock_items': branch_low_stock
        })
    
    # Recent Activity (last 10 activities across all branches)
    recent_sales = Sale.objects.select_related('product_name', 'branch').order_by('-sales_date')[:5]
    recent_stock = Stock.objects.select_related('branch').order_by('-date_added')[:5]
    
    # Combine recent activities
    recent_activity = []
    
    # Add recent sales
    for sale in recent_sales:
        recent_activity.append({
            'type': 'sale',
            'description': f"Sale of {sale.product_name.item_name if sale.product_name else 'Unknown Product'}",
            'details': f"Customer: {sale.customer_name or 'Anonymous'}",
            'amount': f"UGX {sale.get_sales():,}",
            'time': sale.sales_date,
            'branch': sale.branch.name if sale.branch else 'Unknown'
        })
    
    # Add recent stock additions
    for stock in recent_stock:
        recent_activity.append({
            'type': 'stock',
            'description': f"Stock added: {stock.item_name}",
            'details': f"Quantity: {stock.product_quantity}",
            'amount': f"Cost: UGX {stock.cost:,}" if stock.cost else "No cost",
            'time': stock.date_added,
            'branch': stock.branch.name if stock.branch else 'Unknown'
        })
    
    # Sort by time (most recent first)
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_activity[:10]  # Limit to 10 most recent

    context = {
        # Main Metrics
        'total_products': total_products,
        'low_stock_alerts': low_stock_alerts,
        'sales_today': sales_today_count,
        'revenue_today': revenue_today,
        
        # Branch Overview
        'branch_overview': branch_overview,
        
        # Low Stock Items for alerts section
        'low_stock_items_list': low_stock_items.order_by('product_quantity')[:10],  # Show 10 most critical
        
        # Recent Activity
        'recent_activity': recent_activity,
        
        # For backward compatibility
        'total_stock': total_products,
        'todays_sales': revenue_today,
        'pending_credits': Credit.objects.filter(status="Pending").aggregate(total=Sum("due_amount"))["total"] or 0,
        'low_stock_items': low_stock_alerts,
    }

    return render(request, "owner_dashboard.html", context)


@login_required
@user_passes_test(lambda u: u.is_manager)
def manager_dashboard(request):
    total_stock_items = Stock.objects.count()
    today = timezone.now().date()
    todays_sales = Sale.objects.filter(sales_date__date=today)

    todays_sales_total = 0
    for sale in todays_sales:
        if sale.product_quantity and sale.unit_price:
            todays_sales_total += sale.product_quantity * sale.unit_price

    low_stock_items = Stock.objects.filter(
        Q(product_quantity__lt=10) & Q(product_quantity__gt=0)
    ).count()

    pending_credits_total = (
        Credit.objects.filter(status="Pending").aggregate(total=Sum("due_amount"))[
            "total"
        ]
        or 0
    )

    context = {
        "total_stock_items": total_stock_items,
        "todays_sales_total": todays_sales_total,
        "low_stock_items": low_stock_items,
        "pending_credits_total": pending_credits_total,
        "sales": todays_sales,  # Needed if you're using it in your template (e.g. for receipts dropdown)
    }

    return render(request, "manager_dashboard.html", context)


@login_required
@user_passes_test(lambda u: u.is_salesagent)
def salesagent_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Sales calculations
    today_sales = (
        Sale.objects.filter(sales_date__date=today).aggregate(total=Sum("unit_price"))[
            "total"
        ]
        or 0
    )
    weekly_sales = (
        Sale.objects.filter(sales_date__date__gte=week_ago).aggregate(
            total=Sum("unit_price")
        )["total"]
        or 0
    )

    # Credit calculations
    pending_credits = (
        Credit.objects.filter(status="Pending").aggregate(total=Sum("due_amount"))[
            "total"
        ]
        or 0
    )

    # Stock calculations
    low_stock = Stock.objects.filter(product_quantity__lt=10).count()

    # Recent sales (last 5)
    recent_sales = Sale.objects.select_related("product_name").order_by("-sales_date")[
        :5
    ]

    context = {
        "today_sales": today_sales,
        "weekly_sales": weekly_sales,
        "pending_credits": pending_credits,
        "low_stock": low_stock,
        "recent_sales": recent_sales,
        "today": today,
    }
    return render(request, "salesagent_dashboard.html", context)


def count_low_stock_items():
    # Example logic
    from .models import Stock

    return Stock.objects.filter(quantity__lt=10).count()


# Example helper functions
def calculate_total_inventory_value():
    # Example implementation
    total = sum(item.price * item.quantity for item in Stock.objects.all())
    return total


def calculate_today_sales():
    # Example implementation
    from django.utils import timezone
    import datetime

    today = timezone.now().date()
    today_sales = Sale.objects.filter(date_created__date=today).count()
    return today_sales


from django.shortcuts import render, redirect
from .forms import UserCreationForm


def signup(request):
    # Only managers can create new users
    if not request.user.is_authenticated or not request.user.is_manager:
        messages.error(request, "Only managers can create new users.")
        return redirect("login")
    
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully!")
            return redirect("user_list")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})


def buying_list(request):
    items = Buying.objects.all()
    return render(request, "buying_list.html", {"items": items})


def add_buying(request):
    if request.method == "POST":
        form = BuyingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("buying_list")
    else:
        form = BuyingForm()
    return render(request, "add_buying.html", {"form": form})


# for updating procurement
def edit(request, pk):
    item = get_object_or_404(Buying, pk=pk)
    if request.method == "POST":
        form = BuyingForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("buying_list")
    else:
        form = BuyingForm(instance=item)
    return render(request, "edit.html", {"form": form})


# for deleting the buying list or procurement
def buying_delete(request, pk):
    item = get_object_or_404(Buying, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect("buying_list")
    return render(request, "buying_delete.html", {"item": item})


def sales_records(request):
    # Group sales by payment method
    payment_methods = Sale.PAYMENT_CHOICES
    sales_data = []

    for method in payment_methods:
        method_name = method[0]
        total_sales = (
            Sale.objects.filter(payment_method=method_name).aggregate(
                total=Sum("amount_recieved")
            )["total"]
            or 0
        )
        sales_data.append(
            {
                "method": method_name,
                "total": total_sales,
                "percentage": 0,  # Will calculate below
            }
        )

    # Calculate percentages
    grand_total = (
        sum(item["total"] for item in sales_data) or 1
    )  # Avoid division by zero
    for item in sales_data:
        item["percentage"] = round((item["total"] / grand_total) * 100)

    context = {"sales_data": sales_data, "grand_total": grand_total}
    return render(request, "sales_records.html", context)


def delete_credit(request, pk):
    credit = get_object_or_404(Credit, pk=pk)

    if request.method == "POST":
        credit.delete()
        return redirect("manage_credits")  # Redirect to the 'manage_credits' view

    return render(request, "delete_credit.html", {"credit": credit})


def view_credit(request, pk):
    credit = get_object_or_404(Credit, pk=pk)
    return render(request, "view_credit.html", {"credit": credit})


def edit_credit(request, pk):
    credit = get_object_or_404(Credit, pk=pk)

    if request.method == "POST":
        form = AddCreditForm(request.POST, instance=credit)  # If using forms
        # Or process form fields manually if not using Django forms
        if form.is_valid():
            form.save()
            return redirect("manage_credits")  # Redirect after successful update

    # For GET requests or invalid POST data
    form = AddCreditForm(instance=credit)  # If using forms
    return render(
        request,
        "edit_credit.html",
        {
            "credit": credit,
            "form": form,  # If using forms
        },
    )


def custom_logout(request):
    logout(request)
    return redirect("login")


@login_required
@user_passes_test(lambda u: u.is_owner)
def user_list(request):
    """
    Owner-only user management page
    Shows all users with filtering, search, and management options
    """
    # Get query parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Start with all users
    users = User_profile.objects.all().order_by("-date_joined")
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Apply role filter
    if role_filter:
        if role_filter == 'owner':
            users = users.filter(is_owner=True)
        elif role_filter == 'manager':
            users = users.filter(is_manager=True)
        elif role_filter == 'salesagent':
            users = users.filter(is_salesagent=True)
        elif role_filter == 'staff':
            users = users.filter(is_staff=True)
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_users = User_profile.objects.count()
    active_users = User_profile.objects.filter(is_active=True).count()
    inactive_users = User_profile.objects.filter(is_active=False).count()
    managers = User_profile.objects.filter(is_manager=True).count()
    sales_agents = User_profile.objects.filter(is_salesagent=True).count()
    owners = User_profile.objects.filter(is_owner=True).count()
    
    context = {
        "page_obj": page_obj,
        "users": page_obj,
        "search_query": search_query,
        "role_filter": role_filter,
        "status_filter": status_filter,
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "managers": managers,
        "sales_agents": sales_agents,
        "owners": owners,
    }
    
    return render(request, "user_list.html", context)


@login_required
@user_passes_test(lambda u: u.is_owner)
def add_user(request):
    """
    Owner-only user creation page
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created successfully!")
            return redirect("user_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    return render(request, "add_user.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_owner)
def edit_user(request, user_id):
    """
    Owner-only user editing page
    """
    user = get_object_or_404(User_profile, pk=user_id)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} updated successfully!")
            return redirect("user_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserEditForm(instance=user)
    return render(request, "edit_user.html", {"form": form, "user": user})


@login_required
@user_passes_test(lambda u: u.is_owner)
def deactivate_user(request, user_id):
    """
    Owner-only user deactivation page
    Deactivates a user (removes access without deleting)
    """
    user = get_object_or_404(User_profile, pk=user_id)
    
    # Prevent deactivating the current user
    if user.id == request.user.id:
        messages.error(request, "You cannot deactivate your own account!")
        return redirect("user_list")
    
    if request.method == "POST":
        user.is_active = False
        user.save()
        messages.success(request, f"User {user.username} has been deactivated successfully!")
        return redirect("user_list")
    return render(request, "confirm_deactivate.html", {"user": user})


@login_required
@user_passes_test(lambda u: u.is_owner)
def delete_user(request, user_id):
    """
    Owner-only user deletion page
    Permanently deletes a user from the system
    """
    user = get_object_or_404(User_profile, pk=user_id)
    
    # Prevent deleting the current user
    if user.id == request.user.id:
        messages.error(request, "You cannot delete your own account!")
        return redirect("user_list")
    
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"User {username} has been permanently deleted from the system!")
        return redirect("user_list")
    return render(request, "confirm_delete_user.html", {"user": user})


@login_required
@user_passes_test(lambda u: u.is_owner)
def reactivate_user(request, user_id):
    """
    Owner-only user reactivation page
    Reactivates a deactivated user
    """
    user = get_object_or_404(User_profile, pk=user_id)
    
    if request.method == "POST":
        user.is_active = True
        user.save()
        messages.success(request, f"User {user.username} has been reactivated successfully!")
        return redirect("user_list")
    return render(request, "confirm_reactivate_user.html", {"user": user})


@login_required
@user_passes_test(lambda u: u.is_owner)
def inventory_management(request):
    """
    System Admin Inventory Management Page
    Shows all products across all branches with filtering and search capabilities
    """
    # Get query parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    branch_filter = request.GET.get('branch', '')
    status_filter = request.GET.get('status', '')

    # Start with all stock items
    stocks = Stock.objects.select_related('branch', 'category_name').all()

    # Apply search filter
    if search_query:
        stocks = stocks.filter(
            Q(item_name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )

    # Apply category filter
    if category_filter:
        stocks = stocks.filter(category_name__category_name=category_filter)

    # Apply branch filter
    if branch_filter:
        stocks = stocks.filter(branch__name=branch_filter)

    # Apply status filter
    if status_filter:
        if status_filter == 'In Stock':
            stocks = stocks.filter(product_quantity__gte=10)
        elif status_filter == 'Low Stock':
            stocks = stocks.filter(product_quantity__lt=10, product_quantity__gt=0)
        elif status_filter == 'Out of Stock':
            stocks = stocks.filter(product_quantity=0)

    # Order by last_updated
    stocks = stocks.order_by('-last_updated')

    # Pagination
    paginator = Paginator(stocks, 15)  # Show 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    categories = Category.objects.values_list('category_name', flat=True).distinct()
    branches = Branch.objects.values_list('name', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'stocks': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'branch_filter': branch_filter,
        'status_filter': status_filter,
        'categories': categories,
        'branches': branches,
        'status_choices': ['In Stock', 'Low Stock', 'Out of Stock'],
    }

    return render(request, 'inventory_management.html', context)
