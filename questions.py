def get_questions(path_file):
    with open(path_file, "r", encoding="KOI8-R") as file:
        file_contents = file.read()
    blocks = file_contents.split("\n\n")
    questions = {}
    for i in range(len(blocks)):
        if 'Вопрос' in blocks[i]:
            question = blocks[i].split(':')[1].strip()
            answer = blocks[i+1].split(':')[1].strip()
            questions[question] = answer
    return questions

print(get_questions('questions/12koll09.txt'))