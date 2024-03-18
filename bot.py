import os
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Здравствуйте")

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def main():
    load_dotenv()
    bot_token = os.environ['TELEGRAM_BOT_TOKEN']

    updater = Updater(token=bot_token, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()