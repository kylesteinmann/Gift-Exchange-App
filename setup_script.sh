#!/bin/bash

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install django

# Create Django project
django-admin startproject gift_tracker
cd gift_tracker

# Create gifts app
python manage.py startapp gifts

# Create necessary directories
mkdir -p gifts/templates/gifts static/css static/js

# Create and populate files
cat << EOF > gift_tracker/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-replace-this-with-your-own-secret-key'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gifts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gift_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gift_tracker.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
EOF

cat << EOF > gift_tracker/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gifts.urls')),
]
EOF

cat << EOF > gifts/models.py
from django.db import models
from django.contrib.auth.models import User

class Group(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='groups')

    def __str__(self):
        return self.name

class GiftIdea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gift_ideas')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='gift_ideas')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    purchased = models.BooleanField(default=False)
    purchased_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_gifts')

    def __str__(self):
        return f"{self.name} - {self.user.username}"
EOF

cat << EOF > gifts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Group, GiftIdea
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'gifts/register.html', {'form': form})

@login_required
def home(request):
    return render(request, 'gifts/home.html')

@login_required
def group_list(request):
    groups = request.user.groups.all()
    return render(request, 'gifts/group_list.html', {'groups': groups})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('group_list')
    return render(request, 'gifts/group_detail.html', {'group': group})

@login_required
def gift_list(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('group_list')
    
    gifts = GiftIdea.objects.filter(group=group)
    context = {
        'group': group,
        'gifts': gifts,
        'is_owner': request.user == group.members.first()
    }
    return render(request, 'gifts/gift_list.html', context)

@login_required
def add_gift(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        GiftIdea.objects.create(user=request.user, group=group, name=name, description=description)
        messages.success(request, "Gift idea added successfully.")
        return redirect('gift_list', group_id=group_id)
    return render(request, 'gifts/add_gift.html', {'group': group})

@login_required
def mark_purchased(request, gift_id):
    gift = get_object_or_404(GiftIdea, id=gift_id)
    if request.user != gift.user and not gift.purchased:
        gift.purchased = True
        gift.purchased_by = request.user
        gift.save()
        messages.success(request, "Gift marked as purchased.")
    return redirect('gift_list', group_id=gift.group.id)
EOF

cat << EOF > gifts/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='gifts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/gifts/', views.gift_list, name='gift_list'),
    path('groups/<int:group_id>/add_gift/', views.add_gift, name='add_gift'),
    path('gifts/<int:gift_id>/mark_purchased/', views.mark_purchased, name='mark_purchased'),
]
EOF

cat << EOF > gifts/templates/gifts/base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gift Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body class="bg-gray-100 min-h-screen flex flex-col">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <a href="{% url 'home' %}" class="text-2xl font-bold">Gift Tracker</a>
            <div>
                {% if user.is_authenticated %}
                    <a href="{% url 'group_list' %}" class="mr-4">My Groups</a>
                    <a href="{% url 'logout' %}">Logout</a>
                {% else %}
                    <a href="{% url 'login' %}" class="mr-4">Login</a>
                    <a href="{% url 'register' %}">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="container mx-auto mt-8 px-4 flex-grow">
        {% if messages %}
            <div class="messages mb-4">
                {% for message in messages %}
                    <div class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-2" role="alert">
                        {{ message }}
                    </div>
                {% endfor %}
            </div>
        {% endif %}

        {% block content %}
        {% endblock %}
    </main>

    <footer class="bg-gray-200 text-center p-4 mt-8">
        <p>&copy; 2023 Gift Tracker. All rights reserved.</p>
    </footer>

    <script src="/static/js/main.js"></script>
</body>
</html>
EOF

cat << EOF > static/css/style.css
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.gift-card {
    transition: transform 0.3s ease-in-out;
}

.gift-card:hover {
    transform: translateY(-5px);
}

.btn {
    transition: background-color 0.3s ease-in-out;
}

.btn:hover {
    opacity: 0.9;
}
EOF

cat << EOF > static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const giftCards = document.querySelectorAll('.gift-card');
    
    giftCards.forEach(card => {
        card.addEventListener('click', function() {
            this.classList.toggle('bg-blue-100');
        });
    });
});
EOF

# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run the development server
python manage.py runserver
EOF

# Make the script executable
chmod +x setup_script.sh