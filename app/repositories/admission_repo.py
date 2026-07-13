from uuid import UUID
from typing import List, Optional, Tuple
import asyncpg
from app.schemas.admissions import AdmissionInDB

class AdmissionRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        
    async def get_all(self, page: int = 1, limit: int = 10, search: Optional[str] = None, status: Optional[str] = None) -> Tuple[List[AdmissionInDB], int]:
        offset = (page - 1) * limit
        
        where_clauses = []
        params = []
        param_idx = 1
        
        if search:
            where_clauses.append(f"(name ILIKE ${param_idx} OR email ILIKE ${param_idx} OR phone ILIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1
            
        if status:
            where_clauses.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
            
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM admissions{where_sql}"
        total = await self.connection.fetchval(count_query, *params)
        
        # Get items
        params.extend([limit, offset])
        query = f"""
            SELECT id, name, email, phone, course, status, created_at 
            FROM admissions 
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        rows = await self.connection.fetch(query, *params)
        items = [AdmissionInDB(**dict(row)) for row in rows]
        
        return items, total

    async def update_status(self, id: UUID, status: str) -> Optional[AdmissionInDB]:
        query = """
            UPDATE admissions
            SET status = $1
            WHERE id = $2
            RETURNING id, name, email, phone, course, status, created_at
        """
        row = await self.connection.fetchrow(query, status, id)
        if row:
            return AdmissionInDB(**dict(row))
        return None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM admissions WHERE id = $1"
        result = await self.connection.execute(query, id)
        return result == "DELETE 1"
