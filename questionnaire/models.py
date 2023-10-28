from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)  # Use DateField for date of birth
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'Normal User'), ('staff', 'Staff')], default='user')

    def __str__(self):
        return self.user.username  # Represent the user profile by username


from django.db import models


class Group(models.Model):
    GROUP_TYPE = [
        (1, "家长题目"),
        (2, "操作题目"),
        (3, "运动题目")
    ]

    name = models.IntegerField(default=12) # month
    type = models.IntegerField(choices=GROUP_TYPE, default=1)

    def __str__(self):
        type_display = self.get_type_display()
        return f'{self.name}_{type_display}'


class Question(models.Model):
    CHOICES = [
        (1, "精细动作能力水平"),
        (2, "情绪、社会能力开展水平"),
        (3, "精细动作能力水平"),
        (4, "认知能力开展水平"),
        (5, "语言能力开展水平"),
        (6, "大动作能力水平")
    ]
    question_text = models.CharField(max_length=200)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default='12')
    type = models.IntegerField(choices=CHOICES, default=1)  # Default to '1'

    def __str__(self):
        return self.question_text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200, default='yes')
    def __str__(self):
        return self.choice_text

class UserResponse(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_profile.user.username}'s response to {self.question.question_text}"

