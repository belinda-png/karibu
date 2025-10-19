from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)

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
    return render(request, "index.html")


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
    if request.method == "POST":
        form = AddSaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            return redirect("receipt", sale_id=sale.id)
    else:
        form = AddSaleForm()

    return render(request, "sell_item.html", {"form": form})


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

    # Get current branch
    branch_id = request.session.get("branch_id")

    # If no branch is selected, handle that case
    if not branch_id:
        # Try to get user's first branch
        if request.user.branches.exists():
            branch_id = request.user.branches.first().id
            request.session["branch_id"] = branch_id
        else:
            # Handle case where user has no branches
            messages.error(request, "No branch selected or available")
            return redirect("home")  # Redirect to an appropriate page

    # Today's date
    today = timezone.now().date()

    # 1. TOTAL STOCK CALCULATION
    stock = Stock.objects.filter(branch_id=branch_id).count()

    # 2. AVERAGE COST CALCULATION
    avg_cost_data = Stock.objects.filter(branch_id=branch_id).aggregate(avg=Avg("cost"))
    average = int(avg_cost_data["avg"] or 0)  # Convert to integer to avoid decimals

    # 3. TOTAL SALES AMOUNT CALCULATION
    # Calculate using get_sales method from Sale model
    sales = Sale.objects.filter(branch_id=branch_id)
    amount = 0
    for sale in sales:
        amount += sale.get_sales()

    # Keep your original calculations for additional metrics

    # TODAY'S SALES CALCULATION (in UGX)
    todays_sales_data = Sale.objects.filter(branch_id=branch_id, sales_date__date=today)
    todays_sales = 0
    for sale in todays_sales_data:
        todays_sales += sale.get_sales()

    # PENDING CREDITS CALCULATION (in UGX)
    pending_credits = (
        Credit.objects.filter(branch_id=branch_id, status="Pending").aggregate(
            total_credits=Sum("due_amount")
        )["total_credits"]
        or 0
    )

    # LOW STOCK ITEMS
    low_stock_items = Stock.objects.filter(
        branch_id=branch_id, product_quantity__lt=10  # Threshold for low stock
    ).count()

    context = {
        # Variables that match your template
        "stock": stock,
        "average": average,
        "amount": amount,
        # Keep your original variables for other parts of the template
        "total_stock": stock,  # For backward compatibility
        "todays_sales": todays_sales,
        "pending_credits": pending_credits,
        "low_stock_items": low_stock_items,
        # For the recent activity section
        "recent_sales": Sale.objects.filter(branch_id=branch_id).order_by(
            "-sales_date"
        )[:5],
        "recent_stock": Stock.objects.filter(branch_id=branch_id).order_by(
            "-date_added"
        )[:3],
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
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # Redirect after successful signup
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
def user_list(request):
    users = User_profile.objects.all().order_by("-date_joined")
    return render(
        request,
        "user_list.html",
        {
            "users": users,
            "total_users": users.count(),
            "active_users": users.filter(is_active=True).count(),
            "staff_users": users.filter(is_staff=True).count(),
        },
    )


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def add_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created successfully!")
            return redirect("user_list")
    else:
        form = UserCreationForm()
    return render(request, "add_user.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def edit_user(request, user_id):
    user = get_object_or_404(User_profile, pk=user_id)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} updated successfully!")
            return redirect("user_list")
    else:
        form = UserEditForm(instance=user)
    return render(request, "edit_user.html", {"form": form, "user": user})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def deactivate_user(request, user_id):
    user = get_object_or_404(User_profile, pk=user_id)
    if request.method == "POST":
        user.is_active = False
        user.save()
        messages.success(request, f"User {user.username} deactivated successfully!")
        return redirect("user_list")
    return render(request, "confirm_deactivate.html", {"user": user})
