import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Conflict
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

async def shutdown(application):
    """Функция для корректного завершения работы"""
    await application.stop()
    await application.updater.stop()

def main() -> None:
    """Запуск бота"""
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не найден в .env файле или переменных окружения.")
            return

        # Конфигурация long-polling
        application = Application.builder() \
            .token(token) \
            .post_init(post_init) \
            .read_timeout(30) \
            .get_updates_read_timeout(30) \
            .build()

        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_job_description))

        logger.info("Бот запущен")
        
        # Запуск с обработкой конфликтов
        try:
            application.run_polling(
                close_loop=False,
                stop_signals=None,  # Игнорируем сигналы завершения (для Docker)
                drop_pending_updates=True  # Игнорируем сообщения, полученные во время простоя
            )
        except Conflict:
            logger.warning("Обнаружен другой запущенный экземпляр бота. Завершаемся.")
        except Exception as e:
            logger.error(f"Ошибка в работе бота: {e}")
        finally:
            asyncio.run(shutdown(application))

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    main()