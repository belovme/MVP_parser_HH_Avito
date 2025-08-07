# Клиент HH API
import httpx
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, HttpUrl
import logging
from .models import ResumeCreate
from .utils import rate_limit

# Настройка логгера
logger = logging.getLogger(__name__)

# Модели данных для API HH
class HHVacancyArea(BaseModel):
    id: str
    name: str

class HHSalary(BaseModel):
    from_: Optional[int] = None
    to: Optional[int] = None
    currency: Optional[str] = None
    gross: Optional[bool] = None

class HHResume(BaseModel):
    id: str
    title: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime
    age: int
    area: HHVacancyArea
    salary: Optional[HHSalary] = None
    experience: List[Dict[str, Any]]
    skills: List[Dict[str, str]]
    contacts: Optional[Dict[str, Any]] = None
    education: List[Dict[str, Any]]]
    total_experience: Optional[Dict[str, Any]] = None

class HHClient:
    def __init__(self, client_id: str, client_secret: str):
        self.base_url = "https://api.hh.ru"
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.rate_limit_semaphore = asyncio.Semaphore(20)  # 20 запросов в секунду (лимит HH)

    async def _get_access_token(self) -> str:
        """Получение OAuth токена для доступа к API"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                logger.error(f"Ошибка получения токена: {response.text}")
                raise Exception("Не удалось получить токен доступа")

            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires = datetime.now() + timedelta(seconds=data["expires_in"])
            return self.access_token

    @rate_limit(20)  # Ограничение 20 запросов в секунду
    async def _make_request(self, endpoint: str, params: Optional[dict] = None) -> Dict[str, Any]:
        """Базовый метод для выполнения запросов к API HH"""
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "MVP-Parser-Bot/1.0 (likesme77@example.com)"
        }

        async with self.rate_limit_semaphore:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 429:
                    logger.warning("Превышен лимит запросов, ожидание...")
                    await asyncio.sleep(1)
                    return await self._make_request(endpoint, params)

                response.raise_for_status()
                return response.json()

    async def search_resumes(
        self,
        position: str,
        area: str = "1",  # Москва по умолчанию
        experience: Optional[str] = None,
        period: int = 30,  # За последние 30 дней
        per_page: int = 100,
        page: int = 0
    ) -> List[HHResume]:
        """Поиск резюме по параметрам"""
        params = {
            "text": position,
            "area": area,
            "period": period,
            "per_page": per_page,
            "page": page,
            "order_by": "publication_time"
        }

        if experience:
            params["experience"] = experience

        try:
            data = await self._make_request("/resumes", params)
            return [HHResume(**item) for item in data.get("items", [])]
        except Exception as e:
            logger.error(f"Ошибка поиска резюме: {e}")
            return []

    async def get_resume_details(self, resume_id: str) -> Optional[HHResume]:
        """Получение полной информации о резюме"""
        try:
            data = await self._make_request(f"/resumes/{resume_id}")
            return HHResume(**data)
        except Exception as e:
            logger.error(f"Ошибка получения резюме {resume_id}: {e}")
            return None

    async def fetch_resumes_from_hh(
        self,
        position: str,
        city: str = "Москва",
        limit: int = 1000
    ) -> List[ResumeCreate]:
        """Основной метод для получения резюме из HH и преобразования в нашу модель"""
        # Сначала получаем ID региона по названию города
        area_id = await self._get_area_id(city)
        if not area_id:
            logger.warning(f"Не найден регион для города {city}")
            return []

        resumes = []
        page = 0
        total_fetched = 0

        while total_fetched < limit:
            hh_resumes = await self.search_resumes(
                position=position,
                area=area_id,
                per_page=min(100, limit - total_fetched),
                page=page
            )

            if not hh_resumes:
                break

            for hh_resume in hh_resumes:
                resume = await self._convert_hh_resume(hh_resume)
                if resume:
                    resumes.append(resume)
                    total_fetched += 1

            page += 1
            if len(hh_resumes) < 100 or total_fetched >= limit:
                break

        return resumes

    async def _get_area_id(self, city_name: str) -> Optional[str]:
        """Получение ID региона по названию города"""
        try:
            areas = await self._make_request("/areas")
            for country in areas:
                for area in country["areas"]:
                    if area["name"].lower() == city_name.lower():
                        return area["id"]
                    for sub_area in area.get("areas", []):
                        if sub_area["name"].lower() == city_name.lower():
                            return sub_area["id"]
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска региона: {e}")
            return None

    async def _convert_hh_resume(self, hh_resume: HHResume) -> Optional[ResumeCreate]:
        """Преобразование резюме из формата HH в нашу модель"""
        try:
            # Получаем полную информацию о резюме
            full_resume = await self.get_resume_details(hh_resume.id)
            if not full_resume:
                return None

            # Извлекаем опыт работы
            experience_years = 0
            if full_resume.total_experience:
                months = full_resume.total_experience.get("months", 0)
                experience_years = round(months / 12, 1)

            # Извлекаем навыки
            skills = [skill["name"] for skill in full_resume.skills]

            # Извлекаем ожидаемую зарплату
            salary_expect = None
            if full_resume.salary:
                salary_expect = full_resume.salary.to or full_resume.salary.from_

            # Извлекаем контакты (если доступны)
            contacts = {}
            if full_resume.contacts:
                contacts = {
                    "email": full_resume.contacts.get("email"),
                    "phone": full_resume.contacts.get("phone")
                }

            return ResumeCreate(
                source="hh",
                source_id=hh_resume.id,
                fio=hh_resume.title,
                city=hh_resume.area.name,
                experience_years=experience_years,
                position=hh_resume.title.split(",")[0].strip(),
                skills=skills,
                salary_expect=salary_expect,
                published_at=hh_resume.updated_at,
                json_raw={
                    "hh_data": full_resume.dict(),
                    "contacts": contacts
                }
            )
        except Exception as e:
            logger.error(f"Ошибка преобразования резюме {hh_resume.id}: {e}")
            return None