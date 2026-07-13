from uuid import UUID
from typing import List, Optional, Tuple
import asyncpg
from app.schemas.contact import ContactInDB

class ContactRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        
    async def get_all(self, page: int = 1, limit: int = 10, search: Optional[str] = None, status: Optional[str] = None) -> Tuple[List[ContactInDB], int]:
        offset = (page - 1) * limit
        
        where_clauses = []
        params = []
        param_idx = 1
        
        if search:
            where_clauses.append(f"(name ILIKE ${param_idx} OR email ILIKE ${param_idx} OR subject ILIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1
            
        if status:
            where_clauses.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
            
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        count_query = f"SELECT COUNT(*) FROM contacts{where_sql}"
        total = await self.connection.fetchval(count_query, *params)
        
        params.extend([limit, offset])
        query = f"""
            SELECT id, name, email, phone, subject, message, status, created_at 
            FROM contacts 
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        rows = await self.connection.fetch(query, *params)
        items = [ContactInDB(**dict(row)) for row in rows]
        
        return items, total

    async def get_by_id(self, id: UUID) -> Optional[ContactInDB]:
        query = "SELECT id, name, email, phone, subject, message, status, created_at FROM contacts WHERE id = $1"
        row = await self.connection.fetchrow(query, id)
        if row:
            return ContactInDB(**dict(row))
        return None

    async def create(self, data: dict) -> ContactInDB:
        query = """
            INSERT INTO contacts (name, email, phone, subject, message, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, name, email, phone, subject, message, status, created_at
        """
        row = await self.connection.fetchrow(
            query,
            data["name"],
            data["email"],
            data.get("phone"),
            data["subject"],
            data["message"],
            data.get("status", "New")
        )
        return ContactInDB(**dict(row))

    async def update_status(self, id: UUID, status: str) -> Optional[ContactInDB]:
        query = """
            UPDATE contacts
            SET status = $1
            WHERE id = $2
            RETURNING id, name, email, phone, subject, message, status, created_at
        """
        row = await self.connection.fetchrow(query, status, id)
        if row:
            return ContactInDB(**dict(row))
        return None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM contacts WHERE id = $1"
        result = await self.connection.execute(query, id)
        return result == "DELETE 1"
