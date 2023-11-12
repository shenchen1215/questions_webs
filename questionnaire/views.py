from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic, View
from .models import Choice, Question, UserProfile, Group, UserResponse, Picture, OperationQuestion
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from datetime import datetime

def get_age_by_username(username):
    try:
        user = User.objects.get(username=username)
        user_profile = UserProfile.objects.get(user=user)
        birth_date = user_profile.birth_date

        current_date = datetime.now()
        age_in_months = (current_date.year - birth_date.year) * 12 \
                        + (current_date.month - birth_date.month)

        return age_in_months
    except User.DoesNotExist:
        return None  # Handle the case where the username doesn't exist
    except UserProfile.DoesNotExist:
        return None  # Handle the case where the user doesn't have a user profile

class IndexView(generic.ListView):
    template_name = "question/index.html"
    context_object_name = "latest_question_list"
    model = Question

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("id")[:5]

class StaffQuestions(generic.ListView):
    template_name = "question/staff_questions.html"
    context_object_name = "babies_list"
    model = UserProfile

    def get_queryset(self):
        return UserProfile.objects.filter(role='user')

class DetailView(generic.DetailView):
    model = Question
    template_name = "question/detail.html"


class CreateQuestionViews(generic.ListView):
    model = Question
    template_name = "question/createquestions.html"
    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("id")[:5]

class SignUpViews(generic.ListView):
    model = Question
    template_name = "question/sign_up.html"

class SignUpForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())  # Password confirmation field
    birthday_date = forms.DateField(required=False)
    role = forms.ChoiceField(choices=[('admin', 'Admin'), ('user', 'Normal User'), ('staff', 'Staff')])
    

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError("The passwords do not match. Please try again.")


def sign_up(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            birthday_date = form.cleaned_data['birthday_date']
            role = form.cleaned_data['role']
            # Check if the username already exists
            if User.objects.filter(username=username).exists():
                return render(request, 'question/sign_up.html', {'form': form, 'error_message': 'Username already exists'})

            user = User.objects.create_user(username=username, password=password)
            user.save()
        
            user_profile = UserProfile(user=user, birth_date=birthday_date, role=role)
            user_profile.save()
            login(request, user)
            if role == 'staff':
                return HttpResponseRedirect(reverse('questionnaire:staff_questions'))
            current_date = datetime.now()
            age_in_months = (current_date.year - birthday_date.year) * 12 + (current_date.month - birthday_date.month)
            group_name = str(age_in_months)

            return HttpResponseRedirect(reverse('questionnaire:group_questions', args=[role,username]))
        else:
            # Form is not valid, show the form with errors
            return render(request, 'question/sign_up.html', {'form': form})

    else:
        form = SignUpForm()
    return render(request, 'question/sign_up.html', {'form': form})

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('admin', 'Admin'), ('user', 'Normal User'), ('staff', 'Staff')])

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_superuser or user.is_staff:
                    return HttpResponseRedirect(reverse("questionnaire:create_question"))
                login(request, user)
                if role == 'staff':
                    return HttpResponseRedirect(reverse('questionnaire:staff_questions'))
                age = get_age_by_username(username)
                group_name = str(age)
                return HttpResponseRedirect(reverse('questionnaire:group_questions', args=[role,username]))
            else:
                print('user is not valid')
        else:
            print('form is not valid')
    else:
        form = LoginForm()
    return render(request, 'question/login.html', {'form': form})
def create_new_question(g_month, g_type, question, choices, task, stimulus, posture,picture, op_id):
        # Create a new Group object and save it
        new_group = Group(name=g_month, type=2)  # Provide the desired name and type
        new_group.save()

        new_question_text = question

        # Replace '/path/to/your/picture.jpg' with the actual path to your picture file
        picture_path = f'/templates/question_pictures/{picture}'

        # Create a Picture object
        picture = Picture(image=f'{picture_path}', description = f'{picture}')

        # Save the Picture object
        picture.save()
        new_question = OperationQuestion(
            question_text=new_question_text,
            group=new_group,
            type=g_type,
            task = task,
            stimulus = stimulus,
            posture = posture,
            picture =picture,
            operation_id = op_id
        )
        new_question.save()
        for choice in choices:
            Choice.objects.create(operation_question=new_question, choice_text=choice)

def create_new_questions():
    
    print('done')
def create_question(request):
    if request.method == "POST":
        question_text = request.POST.get("question_text")

        if question_text:
            choice1 = request.POST.get("choice_1")
            choice2 = request.POST.get("choice_2")
            # Additional processing or redirects can be added here
            new_question = Question.objects.create(question_text=question_text)
            # Create choices for the question
            Choice.objects.create(question=new_question, choice_text=choice1)
            Choice.objects.create(question=new_question, choice_text=choice2)

            # Redirect to a thank-you page or another appropriate view
            return HttpResponseRedirect(reverse("questionnaire:index"))

        return redirect('no question')
    else:
       # Question.objects.all().delete()
       # Choice.objects.all().delete()
       # Group.objects.all().delete()
        create_new_questions()
        return render(request, 'question/createquestions.html')

class OperationView(generic.ListView):
    model = Question
    template_name = "question/operation.html"

class MovementView(generic.ListView):
    model = Question
    template_name = "question/movement.html"

class ParentsView(generic.ListView):
        model = Question
        template_name = "question/parents.html"
        context_object_name = "latest_question_list"

        def get_queryset(self):
            group_name = "12"
            questions_from_group1 = Question.objects.filter(group__name = group_name)

            return questions_from_group1

class QuestionsFromGroupView(generic.ListView):
    model = Question
    template_name = "question/group_questions.html"
    
    def get_queryset(self):
        role = self.kwargs.get('role', '1')
        group_type = {'user' : 1, 'staff':2}
        user_name = self.kwargs.get('user_name', '1')
        age = get_age_by_username(user_name)

        # Filter user responses where the choice is 'no'
        user_responses_no = UserResponse.objects.filter(
            user_profile__user__username=user_name,
            choice__choice_text='还不能'
        ).values_list('question', flat=True)

        # Filter questions where the ID is in the user_responses_no
        answered_no_questions = Question.objects.filter(id__in=user_responses_no)

        # Get the IDs of questions the user has answered
        user_responses = UserResponse.objects.filter(
            user_profile__user__username=user_name
        ).values_list('question', flat=True)

        # Filter questions based on the user's age and role, and exclude all previously answered questions
        new_questions = Question.objects.filter(
            group__name=age,
            group__type=group_type[role]
        ).exclude(id__in=user_responses)

        all_questions = Question.objects.all()
        questions = Question.objects.filter(type=2).distinct()

        return new_questions, answered_no_questions

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            user_name = self.kwargs.get('user_name', '1')  # Default to '1' if not provided
            context['user_name'] = user_name
            role = self.kwargs.get('role', '1')  # Default to '1' if not provided
            context['role'] = role

            # Access 'new_questions' and 'answered_no_questions' from get_queryset
            new_questions, answered_no_questions = self.get_queryset()
            context['new_questions'] = new_questions
            context['answered_no_questions'] = answered_no_questions
            return context

from django.http import JsonResponse
import json
from django.core.serializers import serialize
from django.conf import settings

class OperationQuestionsFromGroupView(generic.ListView):
    model = OperationQuestion
    template_name = 'question/operation_question.html'

    def get_queryset(self):
        user_name = self.kwargs.get('user_name', '1')
        age = get_age_by_username(user_name)
        group_type = {'user' : 1, 'staff' :2}

        operation_questions_list = []

        for type_index in range(1,6):
            operation_questions_list.append(
                    OperationQuestion.objects.filter(
                    group__name = age,
                    type=type_index
                    )
            )
        #for question in operation_questions:
        #    print(question.choice_set.all())
        print(f' MEDiA_url: {settings.MEDIA_URL}')
        return operation_questions_list
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_name = self.kwargs['user_name']

        # Get the questions QuerySet
        questions = self.get_queryset()[0]
        questions_list = list(questions.values())
        index = 0
        op_questions = []
        for question in questions:
            choices = question.choice_set.all()
            choice_list = []
            for choice in choices:
                choice_list.append(choice.choice_text)
            picture = Picture.objects.filter(id=questions_list[index]['picture_id'])[0]
            op_questions.append(
            {
                'questions': questions_list[index],
                'choices': choice_list,
                'picture': f'{settings.MEDIA_URL}{picture}',
            }
            )
            index +=1
        print(op_questions)
 
        context['current_index'] = self.kwargs.get('current_index', 0)
        context['questions'] = op_questions
        return context
   
# forms.py
class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choices = Choice.objects.filter(question=question)
        for choice in choices:
            self.fields['choice_{0}'.format(choice.id)] = forms.BooleanField(
                label=choice.choice_text,
                required=False  # Users can select multiple choices, so use BooleanField
            )

def question_view(request, question_id):
    question = Question.objects.get(pk=question_id)

    if request.method == 'POST':
        form = QuestionForm(question, request.POST)

        if form.is_valid():
            # Process the selected choices
            selected_choices = [choice_id for choice_id in form.cleaned_data if form.cleaned_data[choice_id]]

            # Now you have the list of selected choice IDs in selected_choices
            # You can perform any necessary actions with these choices

    else:
        form = QuestionForm(question)

    return render(request, 'question/results.html', {'question': question, 'form': form})


class ResultsView(View):
    template_name = 'question/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_name = self.kwargs.get('group_name', '1')  # Default to '1'

        # Retrieve selected choices here and prepare the data
        selected_choices = {
            question.id: get_selected_choice(question.id) for question in group_questions
        }

        context['group_name'] = group_name
        context['group_questions'] = group_questions
        context['selected_choices'] = selected_choices
        return context

    def get(self, request, group_name):
        # Retrieve the questions for the specified group
        group = Group.objects.get(name=group_name, type=1)
        questions = Question.objects.filter(group=group)

        context = {
            'group_name': group_name,
            'group_questions': questions,
        }

        return render(request, self.template_name, context)

    def post(self, request, group_name):
        # Handle the form submission and save the selected choices if needed
        # Process the POST data here
        # You can retrieve the selected choices from the request.POST dictionary

        # Redirect to the GET view after processing the POST request
        return HttpResponseRedirect(reverse('questionnaire:results_page', kwargs={'group_name': group_name}))

def get_selected_choice(question_id):
    # Implement this function to get the selected choice for a question
    # You can query the database or retrieve the data as needed
    # Return the selected choice
    return selected_choice


    def get(self, request):
        # ... (your existing code for GET request)
        return render(request, self.template_name)
class SubmitResponseView(View):
    model = Question
    template_name = 'question/submit.html'
    def post(self, request, *args, **kwargs):
        # Retrieve user's selections from the form
        user_profile = request.user.userprofile  # Assuming the user is authenticated and has a UserProfile
        question_ids = [int(key.split('_')[1]) for key in request.POST if key.startswith('question_')]
        selected_choices = {question_id: int(request.POST[f'question_{question_id}']) for question_id in question_ids}

        # Save the user's responses to the database
        for question_id, choice_id in selected_choices.items():
            question = Question.objects.get(pk=question_id)
            choice = Choice.objects.get(pk=choice_id)
            UserResponse.objects.create(user_profile=user_profile, question=question, choice=choice)

        # Retrieve the user's responses
        user_responses = UserResponse.objects.filter(user_profile=user_profile)
        return render(request, self.template_name, {'user_responses': user_responses})
        
    def get(self, request):
        return render(request, self.template_name)
