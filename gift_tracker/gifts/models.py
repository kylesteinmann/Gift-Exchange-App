from django.db import models
from django.contrib.auth.models import User

class Group(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='gift_groups')

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

class Invitation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.CharField(max_length=32, unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation for {self.email} to join {self.group.name}"
