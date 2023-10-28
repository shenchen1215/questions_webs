import re

def ana():
    choice_dict = {
            "精细动作能力水平" : 1,
            "情绪、社会能力开展水平" : 2,
            "精细动作能力水平" : 3,
            "认知能力开展水平" : 4,
            "语言能力开展水平" : 5,
            "大动作能力水平" : 6,
        }

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

ana()

      
