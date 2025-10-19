"""
URL configuration for belinda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

# urlpatterns = [
#
# ]
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from karibu import views
from karibu.views import login_view

app_name = "karibu"

urlpatterns = [
    path("admin/", admin.site.urls),

    # Home and Auth
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("login/", login_view, name="login"),
    path("logout/", views.custom_logout, name="logout"),
    path("signup/", views.signup, name="signup"),

    # Dashboards
    path("owner/", views.owner_dashboard, name="owner_dashboard"),
    path("manager/", views.manager_dashboard, name="manager_dashboard"),
    path("salesagent/", views.salesagent_dashboard, name="salesagent_dashboard"),

    # Stock
    path("allstock/", views.allstock, name="allstock"),
    path("addstock/", views.addstock, name="addstock"),
    path("stock/view/<int:stock_id>/", views.viewstock, name="viewstock"),
    path("stock/edit/<int:stock_id>/", views.editstock, name="editstock"),
    path("stock/delete/<int:stock_id>/", views.deletestock, name="deletestock"),

    # Sales
    path("sales/", views.saleslist, name="saleslist"),
    path("sales/make/", views.makesale, name="makesale"),
    path("sales_records/", views.sales_records, name="sales_records"),
    path("receipt/<int:sale_id>/", views.receipt, name="receipt"),
    path("reports/custom/", views.custom_sales_report, name="custom_sales"),

    # Credits
    path("credits/", views.manage_credits, name="manage_credits"),
    path("credits/add/", views.add_credit, name="add_credit"),
    path("credits/<int:pk>/", views.view_credit, name="view_credit"),
    path("credits/<int:pk>/edit/", views.edit_credit, name="edit_credit"),
    path("credits/delete/<int:pk>/", views.delete_credit, name="delete_credit"),

    # Buying
    path("buying/", views.buying_list, name="buying_list"),
    path("buying/add/", views.add_buying, name="add_buying"),
    path("buying/<int:pk>/edit/", views.edit, name="edit"),
    path("buying/<int:pk>/delete/", views.buying_delete, name="buying_delete"),

    # Users
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.add_user, name="add_user"),
    path("users/edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path("users/deactivate/<int:user_id>/", views.deactivate_user, name="deactivate_user"),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
