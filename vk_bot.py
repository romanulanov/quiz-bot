import argparse
import os
import random
import json

import redis
import vk_api as vk

from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id
from quiz import create_quiz_answers, create_quiz_questions, parse_question_file

PHRASES = [
    "Подыскиваю интересный вопрос. Минуточку...",
    "Сейчас найду что-то интересное для обсуждения.",
    "Хм, дай-ка подумать над вопросом для тебя.",
    "Ищу что-то любопытное. Одну секунду...",
    "Думаю над вопросом. Пожалуйста, подожди.",
    "Хм, что бы тебе задать? Сейчас найду.",
    "Ищу увлекательный вопрос. Момент...",
    "Дай-ка подумаю... Найти бы хороший вопрос.",
    "Сейчас придумаю что-то интересное. Подожди...",
    "Хм, дай мне секунду, подумаю над вопросом.",
    ]
PHRASES_GIVE_UP = [
    "Не сдавайся! Верь в себя!",
    "Ты сможешь! Продолжай двигаться вперед!",
    "Неважно, сколько времени уйдет, главное - не останавливайся!",
    "Каждый шаг приближает тебя к цели!",
    "Ты сильнее, чем думаешь! Продолжай бороться!",
    "Помни, что важно - это не скорость, а упорство!",
    "Самая трудная часть - это первый шаг. Ты уже сделал его!",
    "Даже если путь к цели кажется трудным, помни, что каждый шаг приближает тебя к успеху!",
    "Ты - настоящий боец! Продолжай идти вперед!",
    "Ты можешь все, чего захочешь! Не останавливайся!"
]

def discussion_with_bot(event, vk_api,  quiz_questions, quiz_answers, r, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)

    if event.text == 'Начать':
        text = 'Привет! Я бот для викторин!'
    elif event.text == 'Новый вопрос':
        text = handle_new_question_request(event, quiz_questions, r, user_id)
    elif event.text == 'Сдаться':
        text = handle_give_up(event, vk_api,  quiz_questions, quiz_answers, r, user_id)
    else:
        text = handle_solution_attempt(event, quiz_answers, r, user_id)

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=text,
    )


def handle_new_question_request(event, quiz_questions, r, user_id):
    question_id, question = random.choice(list(quiz_questions.items()))
    r.set(event.user_id, json.dumps({"question_id":question_id}))
    phrase = random.choice(PHRASES)
    question_text = f'{phrase}\n{question}'
    return question_text


def handle_solution_attempt(event, quiz_answers, r, user_id):
    question_id = json.loads(r.get(event.user_id))["question_id"]
    correct_answer = quiz_answers[question_id]
    if event.text.split('.')[0].lower() == correct_answer.lower():
        return 'Правильно! Нажимай на новый вопрос.'
    else:
        return 'Неправильно… Попробуешь ещё раз?'


def handle_give_up(event, vk_api, quiz_questions, quiz_answers, r, user_id):
    question_id = json.loads(r.get(event.user_id))["question_id"]
    correct_answer = quiz_answers[question_id]
    vk_api.messages.send(
        user_id=event.user_id,
        message=f'Ответ: {correct_answer}',
        random_id=random.randint(1, 1000)
      
    )
    return handle_new_question_request(event, quiz_questions, r, user_id)


def main():
    parser = argparse.ArgumentParser(
        description='Введите путь до папки с вопросами'
    )
    parser.add_argument('--path', help='Путь до вопросов', default='./questions')
    args = parser.parse_args()
    questions_path = args.path
    load_dotenv()
    vk_token = os.environ.get("VK_TOKEN")
    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    file_contents = parse_question_file('questions/')
    quiz_questions = create_quiz_questions(file_contents)
    quiz_answers = create_quiz_answers(file_contents)
   
    host = os.environ.get("REDIS_HOST")
    port = os.environ.get("REDIS_PORT")
    password = os.environ.get("REDIS_PASSWORD")
    r = redis.Redis(
        host=host,
        port=int(port),
        password=password,
        decode_responses=True
    )
    

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            
            discussion_with_bot(event,
                                vk_api,                                
                                quiz_questions,
                                quiz_answers,
                                r,
                                user_id,
                                )

    
if __name__ == '__main__':
    main()
