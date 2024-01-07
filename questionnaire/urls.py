from django.urls import path

from . import views
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static

# ...

app_name = "questionnaire"
urlpatterns = [
    path("", views.HomeView.as_view(), name="homepage"),
    path("question/", views.CreateQuestionViews.as_view(), name="create"),
    path('sign_up_normal/', views.sign_up_normal, name='sign_up_normal'),
    path('sign_up_staff/', views.sign_up_staff, name='sign_up_staff'),
    path('staff_questions/<str:user_id>/', views.StaffQuestions.as_view(), name="staff_questions"),
    path('login/', views.user_login, name='user_login'),
    path('homepage_user/<str:user_id>/', views.HomepageUserView.as_view(), name='homepage_user'),
    path('group-questions/<str:user_id>/', views.QuestionsFromGroupView.as_view(), name='group_questions'),
    path('operation_questions/<str:staff_id>/<str:user_id>/', views.OperationQuestionsFromGroupView.as_view(), name='operation_questions'),
    path('results/submit_response/', views.SubmitResponseView.as_view(), name='submit_response'),
    path('results/parents/<str:group_name>/', views.ResultsView.as_view(), name='results_page'),
    path('operation_questions/<str:staff_id>/<str:user_id>/next_question/', views.next_op_question, name='next_op_question'),
    path('operation_questions/<str:user_id>/prev_question/', views.prev_op_question, name='prev_op_question'),
    path('staff_questions/export_excel', views.export_excel, name="export_excel"),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
