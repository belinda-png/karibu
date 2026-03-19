from django.forms import ModelForm

# from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.models import User, Group
from .models import User_profile
from .models import *

# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from django import forms

# from all forms  everything has to end with a word Form


class AddStockForm(ModelForm):
    class Meta:
        model = Stock

        # fields = ['product_name, quantity, type_pf_stock, date, unit_date, suppliers_name']
        fields = "__all__"


class AddSaleForm(ModelForm):
    # a class meta is like a helper class
    class Meta:
        model = Sale
        # fields = '__all__' returns all fields from our models
        fields = [
            "product_name",
            "product_quantity",
            "unit_price",
            "amount_recieved",
            "payment_method",
            "customer_name",
            "sales_agent",
            "confirm_quantity",
        ]


class UpdateStockForm(ModelForm):
    class Meta:
        model = Stock
        fields = ["product_quantity"]


class AddCreditForm(ModelForm):
    class Meta:
        model = Credit
        fields = "__all__"


from django import forms
from .models import User_profile, Branch

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import User_profile, Branch


def validate_strong_password(password):
    """Custom password validator for strong passwords."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    
    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")
    
    if not any(char.islower() for char in password):
        errors.append("Password must contain at least one lowercase letter.")
    
    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one number.")
    
    if not any(char in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for char in password):
        errors.append("Password must contain at least one special character (!@#$%^&*).")
    
    if errors:
        raise ValidationError(errors)


class UserCreationForm(UserCreationForm):
    branch = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Branches",
    )

    USER_TYPE_CHOICES = [
        ("salesagent", "Sales Agent"),
        ("manager", "Manager"),
        ("owner", "Owner"),
    ]
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES, widget=forms.RadioSelect, label="User Type"
    )

    class Meta:
        model = User_profile
        fields = ("username", "email", "password1", "password2", "user_type", "branch")

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            validate_strong_password(password1)
        return password1

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")
        branches = cleaned_data.get("branch")
        
        # Validate that managers and sales agents must select at least one branch
        if user_type in ["manager", "salesagent"] and not branches:
            raise forms.ValidationError(
                f"{user_type.title()}s must select at least one branch."
            )
        
        # Owners should not have any branches selected (they get access to all)
        if user_type == "owner" and branches:
            # Clear branches for owners - they get access to all branches automatically
            cleaned_data["branch"] = None
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Set user type based on selection
        user_type = self.cleaned_data["user_type"]
        if user_type == "owner":
            user.is_owner = True
            # Owners don't need specific branches - they get access to all
        elif user_type == "manager":
            user.is_manager = True
        elif user_type == "salesagent":
            user.is_salesagent = True

        if commit:
            user.save()
            # Only save branches if not an owner
            if user_type != "owner":
                user.branches.set(self.cleaned_data["branch"])
            else:
                # For owners, we can optionally assign all branches or leave empty
                # since they have system-wide access
                pass

        return user


# class UserCreation(UserCreationForm):

#     branch = forms.ModelChoiceField(
#         queryset=Branch.objects.all(),
#         required=False,
#         empty_label="Select Branch (optional)"
#     )

#     # User type selection
#     USER_TYPE_CHOICES = [
#         ('sales', 'Sales Agent'),
#         ('manager', 'Manager'),
#         ('owner', 'Owner'),
#     ]
#     user_type = forms.ChoiceField(
#         choices=USER_TYPE_CHOICES,
#         widget=forms.RadioSelect
#     )

#     class Meta:
#         model = User_profile
#         fields = ('username', 'email', 'password1', 'password2', 'user_type', 'branch')

#     def save(self, commit=True):
#         user = super().save(commit=False)

#         # Set user type based on selection
#         user_type = self.cleaned_data['user_type']
#         if user_type == 'sales':
#             user.is_salesagent = True
#         elif user_type == 'manager':
#             user.is_manager = True
#         elif user_type == 'owner':
#             user.is_owner = True

#         if commit:
#             user.save()
#         return user


from .models import Buying


class BuyingForm(forms.ModelForm):
    class Meta:
        model = Buying
        fields = "__all__"


class UserEditForm(UserChangeForm):
    password = None  # hide password field

    class Meta:
        model = User_profile
        fields = [
            "username",
            "email",
            "is_staff",
            "is_active",
            "is_salesagent",
            "is_manager",
            "is_owner",
        ]
