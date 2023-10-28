from django.urls import path

from . import views
from django.contrib.auth.views import LoginView

app_name = "questionnaire"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("create_question/", views.create_question, name="create_question"),
    path("question/", views.CreateQuestionViews.as_view(), name="create"),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('staff_questions/', views.StaffQuestions.as_view(), name="staff_questions"),
    path('login/', views.user_login, name='user_login'),
    path('parents/', views.ParentsView.as_view(), name='parents'),
    path('operation/', views.OperationView.as_view(), name='operation'),
    path('movement/', views.MovementView.as_view(), name='movement'),
    path('group-questions/<str:role>/<str:user_name>/', views.QuestionsFromGroupView.as_view(), name='group_questions'),
    path('results/submit_response/', views.SubmitResponseView.as_view(), name='submit_response'),
    path('results/parents/<str:group_name>/', views.ResultsView.as_view(), name='results_page')

]
