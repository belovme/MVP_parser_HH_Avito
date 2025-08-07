# Обработчики команд
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import httpx

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пришли мне описание вакансии, и я найду подходящих кандидатов с HeadHunter."
    )

async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_description = update.message.text
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('API_URL')}/search/",
            json={
                "position": "Python Developer",  # Можно добавить парсинг из текста
                "city": "Москва",               # Или запросить у пользователя
                "description": job_description
            }
        )
    
    if response.status_code == 200:
        candidates = response.json()
        for candidate in candidates[:5]:  # Показываем топ-5
            await update.message.reply_text(
                f"👤 {candidate['resume']['fio']}\n"
                f"🏆 Оценка: {candidate['score']}/10\n"
                f"📝 Анализ: {candidate['details']}\n"
                f"🔗 Ссылка: https://hh.ru/resume/{candidate['resume']['source_id']}"
            )
    else:
        await update.message.reply_text("Произошла ошибка при поиске кандидатов. Попробуйте позже.")