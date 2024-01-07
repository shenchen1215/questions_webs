from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic, View
from .models import Choice, Question, UserProfile, Group, UserResponse, Picture, OperationQuestion, UserOperationPoints
from django.db.models import Max
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from datetime import datetime
from django.http import JsonResponse
import json
from django.core.serializers import serialize
from django.conf import settings
from django.utils import timezone
from openpyxl import Workbook
from django.http import HttpResponse

# points_record = [-1 for i in range(100)]
points_record = {}

def get_user_profile(user_id):
    try:
        user = User.objects.get(id=user_id)
        user_profile = user.userprofile
        return user_profile
    except User.DoesNotExist:
        return None
    except UserProfile.DoesNotExist:
        # Handle the case where the user profile doesn't exist for the user
        return None

def get_age_by_userid(user_id):
    try:
        user = User.objects.get(id=user_id)
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

class HomeView(generic.ListView):
    template_name = "question/homepage.html"
    context_object_name = "latest_question_list"
    model = Question

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("id")[:5]

class StaffQuestions(generic.ListView):
    template_name = "question/staff_questions.html"
    model = UserProfile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id', '0')
        user = User.objects.get(id=user_id)
        user_profile = UserProfile.objects.get(user=user)
        location = user_profile.hospital
        context['babies_list'] = UserProfile.objects.filter(role='user', hospital=location)
        context['staff_id'] = user_id
        return context


def export_excel(request):
    print('excel')
    # Your logic to fetch data goes here
    data_head = ["姓名", "性别", "年龄", "卡号", "测试项目",
             "总题数", "答对个数", "正确率",  "训练日期"]

    # Create a new workbook and add a worksheet
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(data_head)

    all_response = UserResponse.objects.all()
    op_list = get_all_operation_questions()
    record_type = {}
    for response in all_response:
        if response.operation_question is not None:
            user_name = response.user_profile.user.username
            user_id = response.user_profile.user_id
            op_type = response.operation_question.type
            if user_id not in record_type.keys():
                record_type[user_id] = [op_type]
            elif op_type not in record_type[user_id]:
                record_type[user_id].append(op_type)
            else:
                continue
            op_type_display = response.operation_question.get_type_display()
            gender = response.user_profile.gender
            birth_date = str(response.user_profile.birth_date)
            user_id = response.user_profile.user_id
            op_nums = len(op_list[op_type - 1])
            points = UserOperationPoints.objects.filter(
                    user_profile = response.user_profile,
                    type = op_type,
                    answer_time = 0,
                    ).values()
            op_points = serialize_operation_points(points)
            op_points = op_points['point']
            timestamp = str(response.timestamp)
            row_data = [user_name, gender, birth_date, user_id, op_type_display, op_nums * 2, op_points, op_points / (op_nums * 2), timestamp]
            print(row_data)
            # Write your data to the worksheet
            worksheet.append(row_data)

    # Create a response with the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=export_data.xlsx'
    workbook.save(response)

    return response

class CreateQuestionViews(generic.ListView):
    model = Question
    template_name = "question/createquestions.html"
    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("id")[:5]

class HomepageUserView(generic.ListView):
    template_name = "question/homepage_login.html"
    model = UserProfile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id', '0')
        user_profile = get_user_profile(user_id)
        context['user_profile'] = user_profile
        user_month = get_age_by_userid(user_id) 
        context['user_month'] = user_month
        return context

class SignUpNormalForm(forms.Form):
    username = forms.CharField()
    telephone = forms.CharField()  # Add the telephone field
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())  # Password confirmation field
    birthday_date = forms.DateField(required=False)
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES)
    hospital = forms.ChoiceField(choices=UserProfile.HOSPITAL_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError("The passwords do not match. Please try again.")

def sign_up_normal(request):
    if request.method == "POST":
        form = SignUpNormalForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            telephone = form.cleaned_data['telephone']
            password = form.cleaned_data['password']
            birthday_date = form.cleaned_data['birthday_date']
            gender = form.cleaned_data['gender']
            hospital = form.cleaned_data['hospital']
            # Check if the username already exists
            if UserProfile.objects.filter(user__username=username, telephone=telephone).exists():
                return render(request, 'question/sign_up_normal.html', {'form': form, 'error_message': 'Username already exists'})
            role = 'user'
            user = User.objects.create_user(username=username, password=password)
            user.save()
            user_profile = UserProfile(user=user, birth_date=birthday_date,
                                       role=role, telephone=telephone,gender=gender, hospital=hospital)
            user_id = user_profile.user_id
            user_profile.save()
            login(request, user)
            current_date = datetime.now()
            age_in_months = (current_date.year - birthday_date.year) * 12 + (current_date.month - birthday_date.month)
            group_name = str(age_in_months)
            return HttpResponseRedirect(reverse('questionnaire:homepage_user', args=[user_id]))
        else:
            print(form.errors)
            # Form is not valid, show the form with errors
            return render(request, 'question/sign_up_normal.html', {'form': form})
    else:
        form = SignUpNormalForm()
    return render(request, 'question/sign_up_normal.html', {'form': form})

class SignUpStaffForm(forms.Form):
    invitation_code = forms.CharField()
    username = forms.CharField()
    telephone = forms.CharField()  # Add the telephone field
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())  # Password confirmation field
    hospital = forms.ChoiceField(choices=UserProfile.HOSPITAL_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError("The passwords do not match. Please try again.")

def sign_up_staff(request):
    if request.method == "POST":
        form = SignUpStaffForm(request.POST)
        if form.is_valid():
            invitation_code = form.cleaned_data['invitation_code']
            username = form.cleaned_data['username']
            telephone = form.cleaned_data['telephone']
            password = form.cleaned_data['password']
            hospital = form.cleaned_data['hospital']
            if invitation_code != '1023':
                return render(request, 'question/sign_up_staff.html', {'form': form, 'error_message': 'error invitation code'})

            # Check if the username already exists
            if UserProfile.objects.filter(user__username=username, telephone=telephone).exists():
                return render(request, 'question/sign_up_staff.html', {'form': form, 'error_message': 'Username already exists'})
            role = 'staff'
            user = User.objects.create_user(username=username, password=password)
            user.save()
            user_profile = UserProfile(user=user,
                                       role=role,
                                       telephone=telephone,
                                       hospital=hospital)
            user_id = user_profile.user_id
            user_profile.save()
            login(request, user)
            return HttpResponseRedirect(reverse('questionnaire:staff_questions', args=[user_id]))
        else:
            print(form.errors)
            # Form is not valid, show the form with errors
            return render(request, 'question/sign_up_staff.html', {'form': form})
    else:
        form = SignUpStaffForm()
    return render(request, 'question/sign_up_staff.html', {'form': form})

class LoginForm(forms.Form):
    userid = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['userid']
            password = form.cleaned_data['password']
            user = authenticate(request, userid=user_id, password=password)
            user_profile = get_user_profile(user_id)
            if user_profile is not None:
                if user_profile.role == 'staff':
                    login(request, user)
                    return HttpResponseRedirect(reverse('questionnaire:staff_questions', args=[user_id]))
                elif user_profile.role == 'user':
                    login(request, user)
                    age = get_age_by_userid(user_id)
                    group_name = str(age)
                    return HttpResponseRedirect(reverse('questionnaire:homepage_user', args=[user_id]))
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
            return HttpResponseRedirect(reverse("questionnaire:homepage"))

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
        user_id = self.kwargs.get('user_id', '0')
        age = get_age_by_userid(user_id)
        print(f'{user_id}+{age}')

        # Filter user responses where the choice is 'no'
        user_responses_no = UserResponse.objects.filter(
            user_profile__user__id=user_id,
            choice__choice_text='还不能'
        ).values_list('question', flat=True)

        # Filter questions where the ID is in the user_responses_no
        answered_no_questions = Question.objects.filter(id__in=user_responses_no)
        # Get the IDs of questions the user has answered
        user_responses = UserResponse.objects.filter(
            user_profile__user__id=user_id,
        ).values_list('question', flat=True)

        # Filter questions based on the user's age and role, and exclude all previously answered questions
        new_questions = Question.objects.filter(
            group__name=age,
            group__type=1,
        ).exclude(id__in=user_responses)

        all_questions = Question.objects.all()
        questions = Question.objects.filter(type=2).distinct()

        return new_questions, answered_no_questions

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            user_id = self.kwargs.get('user_id', '0')  # Default to '1' if not provided
            context['user_id'] = user_id

            # Access 'new_questions' and 'answered_no_questions' from get_queryset
            new_questions, answered_no_questions = self.get_queryset()
            context['new_questions'] = new_questions
            context['answered_no_questions'] = answered_no_questions
            return context

    
def get_unique_all_operation_questions(op_type):
    # Assuming OPERATION_CHOICES is defined somewhere in your code

    # Get all OperationQuestion objects with type=1
    operation_questions = OperationQuestion.objects.filter(type=op_type)

    # Create a dictionary to store unique operation_questions based on operation_id
    unique_operation_questions = {}

    # Iterate through the queryset and add each operation_question to the dictionary
    for operation_question in operation_questions:
        unique_operation_questions[operation_question.operation_id] = operation_question

    # Retrieve the values from the dictionary to get unique instances
    sorted_operation_questions = list(unique_operation_questions.values())

    # Sort the list by operation_id
    sorted_operation_questions = sorted(sorted_operation_questions, key=lambda x: x.operation_id)
    return sorted_operation_questions
def serialize_operation_question(question):
    picture = Picture.objects.get(pk = question.picture_id).description
    picture = 'question_pictures/' + str(picture)
 
    return {
        'id': question.id,
        'question_text': question.question_text,
        'group_id': question.group_id,
        'type': question.get_type_display(),
        'picture': picture,
        'task': question.task,
        'stimulus': question.stimulus,
        'posture': question.posture,
        'operation_id': question.operation_id,
        'choices': [{'choice_text': choice.choice_text} for choice in question.choice_set.all()]
    }

def get_sorted_operation_with_choices(sorted_operation_questions):
    questions_with_choices = [serialize_operation_question(question) for question in sorted_operation_questions]
    return questions_with_choices

def find_the_last_answer(user_id, last_answer_time, first_index):
    if last_answer_time is None:
        answer_time = 0
        op_type = 1
        op_index = first_index
        return answer_time, op_type, op_index

    user_profile = get_user_profile(user_id)
    points = UserOperationPoints.objects.filter(user_profile = user_profile,
                             answer_time = last_answer_time)
    if len(points) == 5:
        answer_time = last_answer_time + 1
        op_type = 1
        op_index = first_index
    else:
        latest_response = UserResponse.objects.filter(user_profile=user_profile).latest('timestamp')
        op_index = latest_response.operation_question.operation_id - 1
        op_type = latest_response.operation_question.type
        answer_time = last_answer_time

    return answer_time, op_type, op_index

class OperationQuestionsFromGroupView(generic.ListView):
    model = OperationQuestion
    template_name = 'question/operation_question.html'

    def get_queryset(self):
        user_id = self.kwargs.get('user_id', '1')
        age = get_age_by_userid(user_id)
        group_type = {'user' : 1, 'staff' :2}

        operation_questions_list = []

        for type_index in range(1,6):
            operation_questions_list.append(
                    get_unique_all_operation_questions(type_index)
                    ) 
        return operation_questions_list
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs['user_id']
        staff_id = self.kwargs['staff_id']
        print("OOOOOOO staff_id = {staff_id}");

        questions = self.get_queryset()
        questions_list = []
        for op_type in range(1,6):
            q = get_sorted_operation_with_choices(questions[op_type-1])
            questions_list.append(q)

        max_answer_time = UserResponse.objects.filter(
                user_profile__user__id=user_id,
                operation_question__type= 1
                ).aggregate(max_answer=Max('answer_time'))['max_answer']

        first_index = self.kwargs.get('current_index', 0)
        answer_time, op_type, op_index = find_the_last_answer(user_id, max_answer_time, first_index)
        global points_record 
        context['current_index'] = op_index
        context['questions'] = questions_list
        context['operation_type'] = op_type
        context['op_answer_time'] = answer_time
        context['staff_user_id'] = staff_id

        return context


def get_question_index_from_age(age, op_type):
    op_id = OperationQuestion.objects.filter(
            group__name = age,
            type = op_tyoe).operation_id

def get_all_operation_questions():
    operation_questions_list = []

    for type_index in range(1,6):
        operation_questions_list.append(
                get_unique_all_operation_questions(type_index)
                )

    questions_list = []
    for index in range(1,6):
        q = get_sorted_operation_with_choices(operation_questions_list[index-1])
        questions_list.append(q)
    return questions_list

def save_user_response_for_operation(user_profile, op_question,answer_time, selected_choice):
    try:
        user_response = UserResponse.objects.get(
            user_profile=user_profile,
            operation_question=op_question,
            answer_time = answer_time
        )
        user_response.choice = selected_choice
        user_response.save()
    except:
        user_response = UserResponse.objects.create(
            user_profile = user_profile,
            operation_question = op_question,
            choice = selected_choice,
            answer_time = answer_time
        )

def calculate_operations_points_order(user_profile, op_type, answer_time, choice_point):
    try:
        user_points = UserOperationPoints.objects.get(
                user_profile = user_profile,
                type = op_type,
                answer_time = answer_time
        )
        user_points.operation_points += choice_point
    except:
        user_points = UserOperationPoints.objects.create(
                user_profile = user_profile,
                type = op_type,
                answer_time = answer_time,
                operation_points = choice_point
        )
    print(user_points)
def calculate_operations_points_random(user_profile, op_type, answer_time, top_index, bottom_index):
    global points_record
    choice_point = 2 * (top_index+1)
    for index in range(top_index + 1, bottom_index+1):
        choice_point += points_record[user_profile.id][index]
    user_points = UserOperationPoints.objects.create(
            user_profile = user_profile,
            type = op_type,
            answer_time = answer_time,
            operation_points = choice_point
    )
    print(user_points)

def get_the_operation_questions_first_index(questions_list, age, op_type):
    if op_type not in range(1, 6):
        return -1
    questions = OperationQuestion.objects.filter(
            group__name = age,
            type = op_type)
    
    print(f'age={age}, type={op_type}')
    print(f'questions={questions}')
    index = 0
    while index < len(questions_list[op_type - 1]):
        if questions_list[op_type - 1][index]['operation_id'] == questions[0].operation_id:
            return index
        index += 1
    return 0

def get_the_continous(target_value, user_profile):
    global points_record
    target_index = -1
    count = 0
    for i in range(len(points_record[user_profile.id])):
        if points_record[user_profile.id][i] == target_value:
            count += 1
            if count == 3:
                target_index = i
                count = 0
        else:
            count = 0
    return target_index

def find_in_positive_direction(op_index, total_index, user_profile):
    global points_record
    for index in range(op_index + 1, total_index):
        if points_record[user_profile.id][index] == -1:
            return index
    return -1

def find_in_negative_direction(op_index, user_profile):
    global points_record
    for index in range(op_index - 1, -1, -1):
        if points_record[user_profile.id][index] == -1:
            return index
    return -1

def is_edge(op_index, total_index, user_profile):
    global points_record
    if op_index + 1 == total_index and points_record[user_profile.id][op_index - 1] != -1:
        return True
    if op_index - 1 == -1 and points_record[user_profile.id][op_index + 1] != -1:
        return True
    return False

def find_next2(op_index, total_index, user_profile):
    global points_record
    if is_edge(op_index, total_index, user_profile):
        return -1
    # select the direction
    if points_record[user_profile.id][op_index] == 2 and points_record[user_profile.id][op_index + 1] == -1:
        return find_in_positive_direction(op_index, total_index, user_profile)
    else:
        return find_in_negative_direction(op_index, user_profile)

def find_next0(op_index, total_index, user_profile):
    if is_edge(op_index, total_index, user_profile):
        return -1
    return find_in_positive_direction(op_index, total_index, user_profile)

def one_type_end(end_dict, user_profile):
    global points_record
    questions_list = end_dict['questions_list']
    age = end_dict['age']
    user_profile = end_dict['user_profile']
    op_type = end_dict['op_type']
    answer_time = end_dict['answer_time']
    find_2 = end_dict['find_2']
    find_0 = end_dict['find_0']
    print('END!!!!')
    print(points_record[user_profile.id])
    calculate_operations_points_random(user_profile, op_type, answer_time, find_2, find_0)
    op_type += 1
    op_index = get_the_operation_questions_first_index(questions_list, age, op_type)
    points_record[user_profile.id] = [-1 for i in range(100)]

    return op_type, op_index

def get_next_operation_index(args):
    questions_list = args['questions_list']
    op_type = args['op_type']
    op_index = args['op_index']
    age = args['age']
    choice_point = args['choice_index']
    user_profile = args['user_profile']
    answer_time = args['answer_time']

    global points_record
    total_index = len(questions_list[op_type - 1])
    if op_type == 1 or op_type == 4:
        calculate_operations_points_order(user_profile, op_type, answer_time, choice_point)
        if op_index < total_index - 1: op_index += 1
        else:
            op_type += 1
            op_index = get_the_operation_questions_first_index(questions_list, age, op_type)
            print(points_record)
            points_record[user_profile.id] = [-1 for i in range(100)]
    else:
        print(points_record)
        print(user_profile.id)
        points_record[user_profile.id][op_index] = choice_point
        find_2 = get_the_continous(2, user_profile)
        find_0 = get_the_continous(0, user_profile)
        print(f'find_2={find_2} find_0={find_0}')
        if find_2 != -1 and find_0 != -1:
            dict_end = {'user_profile': user_profile,
                        'questions_list': questions_list,
                        'age': age,
                        'op_type': op_type,
                        'answer_time': answer_time,
                        'find_2': find_2,
                        'find_0': find_0,}
            op_type, op_index = one_type_end(dict_end, user_profile)
        elif find_2 == -1:
            op_index = find_next2(op_index, total_index, user_profile)
            #edge
            if op_index == -1:
                first_index = get_the_operation_questions_first_index(questions_list, age, op_type)
                dict_end = {'user_profile': user_profile,
                            'questions_list': questions_list,
                            'age': age,
                            'op_type': op_type,
                            'answer_time': answer_time,
                            'find_2': 0,
                            'find_0': first_index}
                op_type, op_index = one_type_end(dict_end, user_profile)
        else:
            op_index = find_next0(op_index, total_index, user_profile)
            #edge
            if op_index == -1:
                dict_end = {'user_profile': user_profile,
                            'questions_list': questions_list,
                            'age': age,
                            'op_type': op_type,
                            'answer_time': answer_time,
                            'find_2': find_2,
                            'find_0': find_0,}
                op_type, op_index = one_type_end(dict_end, user_profile)
    return op_type, op_index

def serialize_operation_points(points):
    instance = UserOperationPoints.objects.get(pk = points[0]['id'])
    type_display = instance.get_type_display()
    return {
        'id': points[0]['id'],
        'type': type_display,
        'point': points[0]['operation_points'],
    }

def next_op_question(request, staff_id, user_id):
    total_index = int(request.GET.get('totalIndex', 0))
    op_type = int(request.GET.get('_op_type', 1))
    op_index = int(request.GET.get('prevIndex', 2))
    choice_index = int(request.GET.get('choice', 3))
    answer_time = int(request.GET.get('op_answer_time', 4))
    # Get the UserProfile associated with the current user
    user_profile = get_user_profile(user_id)
    print(f"#################staff_id{staff_id}")

    age = get_age_by_userid(user_id)
    group_type = {'user' : 1, 'staff' :2}

    questions_list = get_all_operation_questions()
    q = questions_list[op_type-1][op_index]
    question = get_object_or_404(OperationQuestion, pk=q['id'])
    choices = Choice.objects.filter(operation_question = question)
    selected_choice = choices[choice_index]
    
    save_user_response_for_operation(user_profile, question, answer_time, selected_choice)
    next_op_parameter = {'questions_list': questions_list,
                         'op_type': op_type,
                         'op_index': op_index,
                         'age': age,
                         'choice_index': choice_index,
                         'user_profile': user_profile,
                         'answer_time': answer_time,
                         }
    op_type, op_index = get_next_operation_index(next_op_parameter)
    op_points = []
    if op_type == 6:
        for _type in range(1, 6):
            points = UserOperationPoints.objects.filter(
                    user_profile = user_profile,
                    type = _type,
                    answer_time = answer_time,
                    ).values()
            print(points)
            op_points.append(serialize_operation_points(points))
    
    return JsonResponse({'next_index': op_index,
                         'next_type': op_type,
                         'op_points': op_points,
                         'user_id': staff_id,
                         })

def prev_op_question(request, user_id):
    print(user_id)

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
            # Check if a UserResponse already exists for the user_profile and question
            existing_response = UserResponse.objects.filter(user_profile=user_profile, question=question).first()

            if existing_response:
                # If a response exists, update the choice
                existing_response.choice = choice
                existing_response.timestamp = timezone.now()
                existing_response.save()
            else:
                # If no response exists, create a new one
                UserResponse.objects.create(user_profile=user_profile, question=question, choice=choice)

        # Retrieve the user's responses
        user_responses = UserResponse.objects.filter(user_profile=user_profile)
        return render(request, self.template_name, {'user_responses': user_responses, 'user_id': 74})
        
    def get(self, request):
        return render(request, self.template_name)
