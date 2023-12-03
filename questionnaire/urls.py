from django.urls import path

from . import views
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static

# ...


app_name = "questionnaire"
urlpatterns = [
    path("", views.HomeView.as_view(), name="homepage"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("create_question/", views.create_question, name="create_question"),
    path("question/", views.CreateQuestionViews.as_view(), name="create"),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('staff_questions/', views.StaffQuestions.as_view(), name="staff_questions"),
    path('login/', views.user_login, name='user_login'),
    path('parents/', views.ParentsView.as_view(), name='parents'),
    path('group-questions/<str:role>/<str:user_name>/', views.QuestionsFromGroupView.as_view(), name='group_questions'),
    path('operation_questions/<str:user_name>/', views.OperationQuestionsFromGroupView.as_view(), name='operation_questions'),
    path('results/submit_response/', views.SubmitResponseView.as_view(), name='submit_response'),
    path('results/parents/<str:group_name>/', views.ResultsView.as_view(), name='results_page'),
    path('operation_questions/<str:user_name>/next_question/', views.next_op_question, name='next_op_question'),
    path('operation_questions/<str:user_name>/prev_question/', views.prev_op_question, name='prev_op_question'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
