import os
import httpx
import logging
from telegram import Update
from telegram.ext import ContextTypes
import openai
import json

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Пришли мне описание вакансии, и я найду подходящих кандидатов с HeadHunter."
    )

async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений с описанием вакансии"""
    try:
        job_description = update.message.text

        # Пример фильтров (можно получать от пользователя)
        min_experience = 2  # минимальный опыт в годах
        required_skills = {"python", "django"}  # обязательные навыки

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

            # --- Отправка кандидатов в ChatGPT ---
            prompt = (
                f"Вакансия: {job_description}\n"
                f"Вот список кандидатов в формате JSON:\n"
                f"{candidates}\n"
                "Проранжируй кандидатов по релевантности вакансии и выведи топ-5 с кратким пояснением, почему они в топе. "
                "Ответ верни в структурированном виде: ФИО, опыт, навыки, причина попадания в топ."
            )

            openai.api_key = OPENAI_API_KEY
            chat_response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.2,
            )
            answer = chat_response.choices[0].message.content

            # Сохраняем результат для админ-панели
            with open("ranked_candidates.json", "a", encoding="utf-8") as f:
                json.dump({
                    "job_description": job_description,
                    "ranked": answer
                }, f, ensure_ascii=False)
                f.write("\n")

            await update.message.reply_text("🔍 Вот топ кандидатов по мнению ChatGPT:\n" + answer)

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