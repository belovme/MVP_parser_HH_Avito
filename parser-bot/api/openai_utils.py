# Интеграция с ChatGPT
import json
import openai
from typing import List
from .models import Resume, ResumeAnalysis

async def analyze_resumes(resumes: List[Resume], job_description: str) -> List[ResumeAnalysis]:
    system_prompt = """
    Ты HR-ассистент. Сравниваешь резюме с описанием вакансии.
    Оценивай по 3 критериям (0-10):
    1. Соответствие навыков
    2. Опыт работы
    3. Общее впечатление
    
    Верни JSON с полями: score (среднее), details (краткий анализ).
    """
    
    results = []
    for resume in resumes:
        prompt = f"""
        Вакансия: {job_description}
        
        Резюме:
        Позиция: {resume.position}
        Опыт: {resume.experience_years} лет
        Навыки: {', '.join(resume.skills)}
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        analysis = json.loads(response.choices[0].message.content)
        results.append(ResumeAnalysis(
            resume=resume,
            score=analysis['score'],
            details=analysis['details']
        ))
    
    return results