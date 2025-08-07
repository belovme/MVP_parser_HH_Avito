# Операции с БД
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from typing import List, Optional
import uuid
from datetime import datetime
from .models import Resume, ResumeCreate, ResumeUpdate, Duplicate

class CRUDResume:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, resume_data: ResumeCreate) -> Resume:
        """Создание нового резюме в базе"""
        db_resume = Resume(
            id=uuid.uuid4(),
            source=resume_data.source,
            source_id=resume_data.source_id,
            fio=resume_data.fio,
            city=resume_data.city,
            experience_years=resume_data.experience_years,
            position=resume_data.position,
            skills=resume_data.skills,
            salary_expect=resume_data.salary_expect,
            published_at=resume_data.published_at,
            json_raw=resume_data.json_raw
        )
        self.session.add(db_resume)
        await self.session.commit()
        await self.session.refresh(db_resume)
        return db_resume

    async def get(self, resume_id: uuid.UUID) -> Optional[Resume]:
        """Получение резюме по ID"""
        result = await self.session.execute(
            select(Resume).where(Resume.id == resume_id)
        return result.scalars().first()

    async def get_by_source(self, source: str, source_id: str) -> Optional[Resume]:
        """Получение резюме по источнику и ID источника"""
        result = await self.session.execute(
            select(Resume)
            .where(Resume.source == source)
            .where(Resume.source_id == source_id)
        )
        return result.scalars().first()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        q: Optional[str] = None,
        city: Optional[str] = None,
        exp_min: Optional[int] = None,
        exp_max: Optional[int] = None
    ) -> List[Resume]:
        """Получение списка резюме с фильтрами"""
        query = select(Resume)
        
        if q:
            query = query.where(
                or_(
                    Resume.position.ilike(f"%{q}%"),
                    Resume.skills.any(q),
                    Resume.fio.ilike(f"%{q}%")
                )
            )
        
        if city:
            query = query.where(Resume.city.ilike(f"%{city}%"))
        
        if exp_min is not None:
            query = query.where(Resume.experience_years >= exp_min)
        
        if exp_max is not None:
            query = query.where(Resume.experience_years <= exp_max)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, resume_id: uuid.UUID, resume_data: ResumeUpdate) -> Optional[Resume]:
        """Обновление данных резюме"""
        db_resume = await self.get(resume_id)
        if not db_resume:
            return None
        
        update_data = resume_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_resume, field, value)
        
        db_resume.updated_at = datetime.utcnow()
        self.session.add(db_resume)
        await self.session.commit()
        await self.session.refresh(db_resume)
        return db_resume

    async def delete(self, resume_id: uuid.UUID) -> bool:
        """Удаление резюме"""
        db_resume = await self.get(resume_id)
        if not db_resume:
            return False
        
        await self.session.delete(db_resume)
        await self.session.commit()
        return True

    async def count(self) -> int:
        """Количество резюме в базе"""
        result = await self.session.execute(select(func.count(Resume.id)))
        return result.scalar()

    async def find_duplicates(self, resume_id: uuid.UUID) -> List[Resume]:
        """Поиск дубликатов резюме"""
        # Здесь можно реализовать логику поиска дубликатов
        # по телефону, email или другим параметрам
        current_resume = await self.get(resume_id)
        if not current_resume:
            return []
        
        # Пример простой проверки по ФИО и позиции
        query = select(Resume).where(
            Resume.fio == current_resume.fio,
            Resume.position == current_resume.position,
            Resume.id != current_resume.id
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def mark_as_duplicate(self, original_id: uuid.UUID, duplicate_id: uuid.UUID) -> Duplicate:
        """Пометка резюме как дубликата"""
        duplicate = Duplicate(
            id=uuid.uuid4(),
            orig=original_id,
            dup=duplicate_id
        )
        self.session.add(duplicate)
        await self.session.commit()
        await self.session.refresh(duplicate)
        return duplicate

    async def get_duplicates(self, resume_id: uuid.UUID) -> List[Duplicate]:
        """Получение информации о дубликатах"""
        query = select(Duplicate).where(
            or_(
                Duplicate.orig == resume_id,
                Duplicate.dup == resume_id
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()