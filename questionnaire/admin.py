from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Question, Choice, Group, UserProfile, UserResponse, OperationQuestion, Picture,UserOperationPoints

admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Group)
admin.site.register(UserProfile)
admin.site.register(UserResponse)
admin.site.register(OperationQuestion)
admin.site.register(Picture)
admin.site.register(UserOperationPoints)
