import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from handlers import start, handle_job_description
from dotenv import load_dotenv
load_dotenv()

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    """Функция для пост-инициализации бота"""
    await application.bot.set_my_commands([
        ("start", "Начать работу с ботом"),
    ])

def main() -> None:
    """Запуск бота"""
    try:
        # Создаем Application и передаем токен бота
        application = Application.builder() \
            .token(os.getenv("TELEGRAM_BOT_TOKEN")) \
            .post_init(post_init) \
            .build()

        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_job_description))

        # Запускаем бота
        logger.info("Бот запущен")
        application.run_polling()

    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")

if __name__ == "__main__":
    main()