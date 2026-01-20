from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("operations/", views.operations_list, name="operations_list"),
    path("statistics/", views.statistics, name="statistics"),
    path("sales/", views.sales, name="sales"),
    path("debts/", views.debts, name="debts"),
    path("login/", auth_views.LoginView.as_view(template_name='register/login.html'), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]