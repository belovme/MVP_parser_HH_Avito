# MVP_parser_HH_Avito

Назначение: Бот принимает описание вакансии, вытягивает резюме, прогоняет через GPT и присылает топ-кандидатов в чат

Функционал:
1. Принимает от UI запрос (должность, город, фильтры);
2. Получает резюме из HeadHunter и Avito Job через официальные API;
3. Нормализует, хранит в PostgreSQL и исключает дубли;
4. Отдаёт данные JSON / NDJSON / CSV и показывает их в простой админ‑панели;
5. Разворачивается одной командой docker‑compose up под Linux, работает за
6. Nginx‑reverse‑proxy.

Стек:
1. Python async
httpx[http2] + asyncio
( await client.get(...) )

2. API HH
github.com/hhru/api + datamodelcodegen

3. API Avito github.com/alekskdr/avito-api

4. Web‑framework FastAPI + uvicorn

5. DB PostgreSQL 15 + pgvector 0.6

6. ORM
SQLModel 

7. Cache Redis 7 (aio‑driver aioredis )

8. Admin UI 
Fork Streamlit‑Admin‑Dashboard

9. Контейнеры
Docker‑compose (+ Dockerfile
для API и UI)

10. Reverse‑proxy 
Nginx (docker‑image)

11. CI 
GitHub Actions