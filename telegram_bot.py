import argparse
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


def get_score(update, r):
    score = r.get('score') 
    update.message.reply_text(
        f"Твой счёт: {score}")
    return score


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
    question_id = random.choice(list(quiz_questions.keys()))
    question_text = quiz_questions[question_id]
    r.set(update.effective_user.id, question_id)
    r.set(update.effective_user.id, get_score(update, r))
    update.message.reply_text(question_text)
    return ANSWER


def handle_solution_attempt(update, context, quiz_answers, r):
    user_id = update.effective_user.id
    answer_id = f'Ответ {user_id}' 
    question_id = r.get(user_id) 
    

    
    correct_answer = quiz_answers[f'Ответ {question_id}']

    
    if update.message.text.lower() in correct_answer.lower():
        r.set('score', int(r.get('score'))+1)
        update.message.reply_text('Правильно! Нажимай на новый вопрос.')
        return QUESTION
    else:
        update.message.reply_text(f'Неправильно… Попробуешь ещё раз? {correct_answer}')
        return ANSWER
    
    


def handle_give_up(update, context, quiz_questions, quiz_answers, r):
    update.message.reply_text(random.choice(PHRASES_GIVE_UP))
    user_id = update.effective_user.id
    question_id = r.get(user_id)
    question_id = question_id[7:]
    return handle_new_question_request(update, context, quiz_questions, r)


def handle_show_score(update, context, quiz_questions, quiz_answers, r):
    user_id = update.effective_user.id
    score = get_score(update, r)
    user_id = update.effective_user.id
    
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
    r = redis.Redis(host=host, port=port, password=password, decode_responses=True)
    r.set('score', 0)
    file_contents = parse_question_file(questions_path)

    r = redis.Redis(host=host,
                    port=port,
                    password=password,
                    decode_responses=True)

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
