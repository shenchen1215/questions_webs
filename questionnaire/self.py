import re

choice_dict = {
            "粗大运动-姿势" : 1,
            "粗大运动-移动" : 2,
            "粗大运动-实物操作" : 3,
            "精细运动-抓握" : 4,
            "精细运动-视觉-运动整合" : 5
        }
def ana():
    with open('question_text', 'r') as file:
        lines = file.readlines()
        group = 1
        for index in range(len(lines)):
            line = lines[index].strip()
            if 'month' in line:
                months = re.findall(r'\d+', line)
                months = [int(digit) for digit in months]
                index += 1
                while index < len(lines) and 'month' not in lines[index]:
                    for month in months:
                        parts = lines[index].split()
                        if len(parts) >= 2:
                            question = parts[0]
                            question_type = parts[1]
                            question_type = choice_dict[question_type]
                            print(f'    create_new_question({month*3+1},{month},{question_type},"{question}")')
                    index += 1

def ana_operation():
    op_id = 0
    with open('question_text', 'r') as file:
        lines = file.readlines()
        for index in range(len(lines)):
            line = lines[index].strip()
            if 'month' in line:
                months = re.findall(r'\d+', line)
                months = [int(digit) for digit in months]
                months = [mon for mon in range(months[0], months[1]+1)]
                index += 1
                while index < len(lines) and 'month' not in lines[index]:
                    for month in months:
                        parts = lines[index].split()
                        if len(parts) >= 2:
                            task, stimulus, posture = parts[0], parts[1], parts[2]
                            question = parts[3]
                            question_type = parts[4]
                            question_type = choice_dict[question_type]
                            choices = [parts[5], parts[6], parts[7]]
                            picture = parts[8]
                            op_id = parts[9]
                            print(f'    create_new_question({month},{question_type},"{question}",{choices}, "{task}", "{stimulus}", "{posture}", "{picture}", {op_id})')
                    index += 1

ana_operation()
