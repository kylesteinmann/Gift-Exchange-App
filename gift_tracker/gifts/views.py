from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Group, GiftIdea, Invitation
from django.contrib import messages
from django.contrib.auth.views import LogoutView, LoginView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import random
import string
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.db.models import Prefetch

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            logout(request)
            return self.get(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'gifts/register.html', {'form': form})

@login_required
def home(request):
    return render(request, 'gifts/home.html')

@login_required
def group_list(request):
    groups = Group.objects.filter(members=request.user)
    return render(request, 'gifts/group_list.html', {'groups': groups})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('group_list')

    members = group.members.all()
    
    gifts_by_user = {}
    for member in members:
        gifts = GiftIdea.objects.filter(group=group, user=member).select_related('user', 'purchased_by')
        gifts_by_user[member] = gifts

    context = {
        'group': group,
        'members': members,
        'gifts_by_user': gifts_by_user,
    }
    return render(request, 'gifts/group_detail.html', context)

@login_required
def add_gift(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('group_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        GiftIdea.objects.create(user=request.user, group=group, name=name, description=description)
        messages.success(request, "Gift idea added successfully.")
        return redirect('group_detail', group_id=group_id)
    
    return render(request, 'gifts/add_gift.html', {'group': group})

@login_required
def mark_purchased(request, gift_id):
    gift = get_object_or_404(GiftIdea, id=gift_id)
    if request.user != gift.user and not gift.purchased:
        gift.purchased = True
        gift.purchased_by = request.user
        gift.save()
        messages.success(request, "Gift marked as purchased.")
    return redirect('group_detail', group_id=gift.group.id)

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            group = Group.objects.create(name=name)
            group.members.add(request.user)  # Add the creating user to the group
            messages.success(request, f"Group '{name}' created successfully.")
            return redirect('group_list')
    return render(request, 'gifts/create_group.html')

@login_required
def invite_user(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('group_list')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Generate a unique invitation token
            invitation_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            
            # Save the invitation
            invitation = Invitation.objects.create(
                group=group,
                email=email,
                token=invitation_token,
                invited_by=request.user
            )
            
            # Generate invitation link
            invitation_link = request.build_absolute_uri(
                reverse('accept_invitation', args=[invitation_token])
            )
            print("invitation_link", invitation_link)
            # Send invitation email
            subject = f"Invitation to join {group.name} on Gift Tracker"
            message = f"You've been invited to join {group.name} on Gift Tracker. Click the link below to accept:\n\n{invitation_link}"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, f"Invitation sent to {email}")
            except Exception as e:
                messages.error(request, f"Failed to send invitation: {str(e)}")
        else:
            messages.error(request, "Please provide a valid email address.")
    
    return render(request, 'gifts/invite_user.html', {'group': group})

def accept_invitation(request, token):
    invitation = get_object_or_404(Invitation, token=token)
    
    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
        else:
            # Check if the email already exists
            existing_user = User.objects.filter(email=invitation.email).first()
            if existing_user:
                messages.info(request, "An account with this email already exists. Please log in.")
                return redirect('login')
            
            # Create a new user
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.email = invitation.email
                user.save()
                login(request, user)
            else:
                return render(request, 'gifts/accept_invitation.html', {'invitation': invitation, 'form': form})
        
        # Add user to the group
        invitation.group.members.add(user)
        
        # Delete the invitation
        invitation.delete()
        
        messages.success(request, f"You have successfully joined {invitation.group.name}.")
        return redirect('group_detail', group_id=invitation.group.id)
    
    # If user is not authenticated, check if the email exists
    if not request.user.is_authenticated:
        existing_user = User.objects.filter(email=invitation.email).first()
        if existing_user:
            messages.info(request, "An account with this email already exists. Please log in.")
            return redirect('login')
        
        form = CustomUserCreationForm(initial={'email': invitation.email})
        return render(request, 'gifts/accept_invitation.html', {'invitation': invitation, 'form': form})
    
    return render(request, 'gifts/accept_invitation.html', {'invitation': invitation})

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'gifts/login.html'

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Check if there's a 'next' parameter in the URL
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'gifts/login.html', {'form': form})
