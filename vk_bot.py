import argparse
import os
import random

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

def discussion_with_bot(event, vk_api, chat_data, quiz_questions, quiz_answers, r, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)

    if event.text == 'Начать':
        text = 'Привет! Я бот для викторин!'
    elif event.text == 'Новый вопрос':
        text = handle_new_question_request(event, chat_data, quiz_questions, r, user_id)
    elif event.text == 'Сдаться':
        text = handle_give_up(event, vk_api, chat_data, quiz_questions, quiz_answers, r, user_id)
    else:
        text = handle_solution_attempt(event, chat_data, quiz_answers,user_id)

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=text,
    )


def handle_new_question_request(event, chat_data, quiz_questions, r, user_id):
    vk_question_id = random.choice(list(quiz_questions.keys()))
    phrase = random.choice(PHRASES)
    question_text = f'{phrase}\n{quiz_questions[vk_question_id]}'
    r.set(event.user_id, question_text)
    return question_text


def handle_solution_attempt(event, chat_data, quiz_answers, user_id):
    if event.text.split('.')[0] in quiz_answers[f'Ответ {chat_data[user_id]["vk_question_id"]}']:
        chat_data["vk_question_id"] += 1
        return 'Правильно!'
    else:
        return 'Неправильно… Попробуешь ещё раз?'


def handle_give_up(event, vk_api, chat_data, quiz_questions, quiz_answers, r, user_id):
    vk_api.messages.send(
        user_id=event.user_id,
        message=quiz_answers[f'Ответ {chat_data[user_id]["vk_question_id"]}'],
        random_id=random.randint(1, 1000)
    )
    chat_data[user_id]["vk_question_id"] += 1
    return handle_new_question_request(event, chat_data, quiz_questions, r, user_id)


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
    chat_data = {}
    host = os.environ.get("REDIS_HOST")
    port = os.environ.get("REDIS_PORT")
    password = os.environ.get("REDIS_PASSWORD")
    r = redis.Redis(
        host=host,
        port=int(port),
        password=password,
        decode_responses=True
    )
    r.set('score', 0)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            if user_id not in chat_data:
                chat_data[user_id] = {'vk_question_id': 0}
            discussion_with_bot(event,
                                vk_api,
                                chat_data,
                                quiz_questions,
                                quiz_answers,
                                r,
                                user_id,
                                )

    
if __name__ == '__main__':
    main()
