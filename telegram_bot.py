import argparse
import json
import os
import random
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
from quiz import create_quiz_answers, create_quiz_questions, parse_question_file
import redis

QUESTION, ANSWER = range(2)


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


def start(update, context):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Счёт', '/start']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        "Привет! Я бот для викторин!")
    update.message.reply_text(
        "Жми на кнопку Новый вопрос", reply_markup=reply_markup)
    return QUESTION


def handle_new_question_request(update, context, quiz_questions, r):
    update.message.reply_text(random.choice(PHRASES))
    question_id, question = random.choice(list(quiz_questions.items()))
    r.set(update.effective_user.id, json.dumps({"question_id":question_id}))
    update.message.reply_text(question)
    return ANSWER


def handle_solution_attempt(update, context, quiz_answers, r):
    question_id = json.loads(r.get(update.effective_user.id))["question_id"]
    correct_answer = quiz_answers[question_id]
    if update.message.text.lower() in correct_answer.lower():
        update.message.reply_text('Правильно! Нажимай на новый вопрос.')
        return QUESTION
    else:
        update.message.reply_text(f'Нет, пробуй ещё. Подсказка: {correct_answer[0: random.randint(4,9)]}', 
                                  )
        return ANSWER
    

def handle_give_up(update, context, quiz_questions, quiz_answers, r):
    question_id = json.loads(r.get(update.effective_user.id))["question_id"]
    correct_answer = quiz_answers[question_id]
    update.message.reply_text(f'Правильный ответ: {correct_answer}')
    
    return handle_new_question_request(update, context, quiz_questions, r)


def handle_show_score(update, context, quiz_questions, quiz_answers, r):
    return ANSWER


def cancel(update, context):
    update.message.reply_text('До свидания! Надеюсь, мы ещё поговорим!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    parser = argparse.ArgumentParser(description='Введите путь до папки с вопросами')
    parser.add_argument('--path', help='Путь до вопросов', default='./questions')
    args = parser.parse_args()
    questions_path = args.path
    load_dotenv()

    host = os.environ.get("REDIS_HOST")
    port = os.environ.get("REDIS_PORT")
    password = os.environ.get("REDIS_PASSWORD")
    file_contents = parse_question_file(questions_path)
    r = redis.Redis(host=host,
                    port=port,
                    password=password,
                    decode_responses=True,
                    )

    quiz_questions = create_quiz_questions(file_contents)
    quiz_answers = create_quiz_answers(file_contents)

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTION: 
                    [MessageHandler(Filters.regex('Новый вопрос'), 
                                    lambda update, context: handle_new_question_request(update, context, quiz_questions, r))],
            ANSWER: 
                    [MessageHandler(Filters.regex('Новый вопрос'), 
                                    lambda update, context: handle_new_question_request(update, context, quiz_questions, r)),
                    MessageHandler(Filters.regex('Сдаться'), 
                                    lambda update, context: handle_give_up(update, context, quiz_questions, quiz_answers, r)),
                    MessageHandler(Filters.regex('Счёт'), 
                                    lambda update, context: handle_show_score(update, context, quiz_questions, quiz_answers, r)),
                    MessageHandler(Filters.text & ~Filters.command, 
                                    lambda update, context: handle_solution_attempt(update, context, quiz_answers, r))]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
