from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import login_view, CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('accounts/login/', login_view, name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/add_gift/', views.add_gift, name='add_gift'),
    path('gifts/<int:gift_id>/mark_purchased/', views.mark_purchased, name='mark_purchased'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/invite/', views.invite_user, name='invite_user'),
    path('groups/<int:group_id>/accept_invitation/', views.accept_invitation, name='accept_invitation'),
    path('accept_invitation/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
