import os
import httpx
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Пришли мне описание вакансии, и я найду подходящих кандидатов с HeadHunter."
    )

async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений с описанием вакансии"""
    try:
        job_description = update.message.text
        
        # Формируем URL с проверкой протокола
        base_url = os.getenv('API_URL', '').rstrip('/')
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{base_url}/search/",
                json={
                    "position": "Python Developer",
                    "city": "Москва",
                    "description": job_description
                }
            )
        
        if response.status_code == 200:
            candidates = response.json()
            if not candidates:
                await update.message.reply_text("По вашему запросу кандидатов не найдено.")
                return
                
            await update.message.reply_text("🔍 Вот топ кандидатов с HeadHunter:")
            
            for candidate in candidates[:5]:
                try:
                    await update.message.reply_text(
                        f"👤 {candidate['resume']['fio']}\n"
                        f"🏆 Оценка: {candidate['score']}/10\n"
                        f"📝 Анализ: {candidate['details']}\n"
                        f"🔗 Ссылка: https://hh.ru/resume/{candidate['resume']['source_id']}"
                    )
                except KeyError as e:
                    logger.error(f"Ошибка формата данных кандидата: {e}")
                    continue
                    
            await update.message.reply_text("Хотите уточнить параметры поиска? Пришлите новое описание вакансии.")
            
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            await update.message.reply_text("Произошла ошибка при поиске кандидатов. Попробуйте позже.")
            
    except httpx.ConnectError:
        logger.error("Connection error to API")
        await update.message.reply_text("Не удалось подключиться к сервису поиска. Попробуйте позже.")
    except httpx.TimeoutException:
        logger.error("API timeout")
        await update.message.reply_text("Сервис поиска не отвечает. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("Произошла непредвиденная ошибка. Мы уже работаем над её устранением.")