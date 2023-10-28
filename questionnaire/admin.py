from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Question, Choice, Group, UserProfile, UserResponse

admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Group)
admin.site.register(UserProfile)
admin.site.register(UserResponse)
