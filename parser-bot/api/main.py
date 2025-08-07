# FastAPI приложение
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import Resume, ResumeAnalysis
from .hh_client import fetch_resumes_from_hh
from .openai_utils import analyze_resumes
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search/")
async def search_resumes(position: str, city: str, description: str) -> List[ResumeAnalysis]:
    # 1. Получаем резюме с HH
    resumes = await fetch_resumes_from_hh(position, city)
    
    # 2. Анализируем через GPT
    analyzed = await analyze_resumes(resumes, description)
    
    # 3. Возвращаем топ кандидатов
    return sorted(analyzed, key=lambda x: x.score, reverse=True)[:10]

@app.get("/ping")
async def ping():
    return {"status": "ok"}