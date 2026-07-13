from uuid import UUID
from typing import List, Optional, Tuple
import asyncpg
from app.schemas.courses import CourseInDB

class CourseRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        
    async def get_all(self, page: int = 1, limit: int = 10, search: Optional[str] = None) -> Tuple[List[CourseInDB], int]:
        offset = (page - 1) * limit
        
        where_clauses = []
        params = []
        param_idx = 1
        
        if search:
            where_clauses.append(f"(title ILIKE ${param_idx} OR category ILIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1
            
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM courses{where_sql}"
        total = await self.connection.fetchval(count_query, *params)
        
        # Get items
        params.extend([limit, offset])
        query = f"""
            SELECT id, title, category, price, is_active, created_at 
            FROM courses 
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        rows = await self.connection.fetch(query, *params)
        items = [CourseInDB(**dict(row)) for row in rows]
        
        return items, total

    async def create(self, data: dict) -> CourseInDB:
        query = """
            INSERT INTO courses (title, category, price, is_active)
            VALUES ($1, $2, $3, $4)
            RETURNING id, title, category, price, is_active, created_at
        """
        row = await self.connection.fetchrow(
            query,
            data["title"],
            data["category"],
            data["price"],
            data.get("is_active", True)
        )
        return CourseInDB(**dict(row))

    async def update(self, id: UUID, data: dict) -> Optional[CourseInDB]:
        # Only update provided fields dynamically
        set_clauses = []
        params = []
        param_idx = 1
        
        for key, value in data.items():
            if value is not None:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1
                
        if not set_clauses:
            return await self.get_by_id(id)
            
        params.append(id)
        set_sql = ", ".join(set_clauses)
        
        query = f"""
            UPDATE courses
            SET {set_sql}
            WHERE id = ${param_idx}
            RETURNING id, title, category, price, is_active, created_at
        """
        row = await self.connection.fetchrow(query, *params)
        if row:
            return CourseInDB(**dict(row))
        return None

    async def get_by_id(self, id: UUID) -> Optional[CourseInDB]:
        query = "SELECT id, title, category, price, is_active, created_at FROM courses WHERE id = $1"
        row = await self.connection.fetchrow(query, id)
        if row:
            return CourseInDB(**dict(row))
        return None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM courses WHERE id = $1"
        result = await self.connection.execute(query, id)
        return result == "DELETE 1"
