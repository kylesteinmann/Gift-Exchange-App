from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Group, GiftIdea, Invitation
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import random
import string

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            logout(request)
            return self.get(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

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
    groups = Group.objects.filter(members=request.user)
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
    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group.")
        return redirect('group_list')
    
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

@login_required
def accept_invitation(request, token):
    invitation = get_object_or_404(Invitation, token=token)
    
    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
        else:
            # Create a new user
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = User.objects.create_user(username=username, email=invitation.email, password=password)
            login(request, user)
        
        # Add user to the group
        invitation.group.members.add(user)
        
        # Delete the invitation
        invitation.delete()
        
        messages.success(request, f"You have successfully joined {invitation.group.name}.")
        return redirect('group_detail', group_id=invitation.group.id)
    
    return render(request, 'gifts/accept_invitation.html', {'invitation': invitation})
