from uuid import UUID
from typing import List, Optional, Tuple
import asyncpg
import json
from app.schemas.resources import ResourceInDB

class ResourceRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        
    async def get_all(self, page: int = 1, limit: int = 10, search: Optional[str] = None, type: Optional[str] = None, subject: Optional[str] = None) -> Tuple[List[ResourceInDB], int]:
        offset = (page - 1) * limit
        
        where_clauses = []
        params = []
        param_idx = 1
        
        if search:
            where_clauses.append(f"(title ILIKE ${param_idx} OR description ILIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1
            
        if type:
            where_clauses.append(f"type = ${param_idx}")
            params.append(type)
            param_idx += 1

        if subject:
            where_clauses.append(f"subject ILIKE ${param_idx}")
            params.append(f"%{subject}%")
            param_idx += 1
            
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM resources{where_sql}"
        total = await self.connection.fetchval(count_query, *params)
        
        # Get items
        params.extend([limit, offset])
        query = f"""
            SELECT id, title, description, type, class_range, subject, file_url, pages, rating, downloads, topics, created_at 
            FROM resources 
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        rows = await self.connection.fetch(query, *params)
        items = []
        for row in rows:
            d = dict(row)
            if isinstance(d.get('topics'), str):
                try:
                    d['topics'] = json.loads(d['topics'])
                except:
                    d['topics'] = []
            items.append(ResourceInDB(**d))
        
        return items, total

    async def create(self, data: dict) -> ResourceInDB:
        topics_json = json.dumps(data.get("topics", []))
        query = """
            INSERT INTO resources (title, description, type, class_range, subject, file_url, pages, rating, downloads, topics)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, title, description, type, class_range, subject, file_url, pages, rating, downloads, topics, created_at
        """
        row = await self.connection.fetchrow(
            query,
            data["title"],
            data.get("description"),
            data["type"],
            data["class_range"],
            data["subject"],
            data["file_url"],
            data.get("pages", 0),
            data.get("rating", 0.0),
            data.get("downloads", 0),
            topics_json
        )
        d = dict(row)
        if isinstance(d.get('topics'), str):
            try:
                d['topics'] = json.loads(d['topics'])
            except:
                d['topics'] = []
        return ResourceInDB(**d)

    async def get_by_id(self, id: UUID) -> Optional[ResourceInDB]:
        query = "SELECT id, title, description, type, class_range, subject, file_url, pages, rating, downloads, topics, created_at FROM resources WHERE id = $1"
        row = await self.connection.fetchrow(query, id)
        if row:
            d = dict(row)
            if isinstance(d.get('topics'), str):
                try:
                    d['topics'] = json.loads(d['topics'])
                except:
                    d['topics'] = []
            return ResourceInDB(**d)
        return None

    async def delete(self, id: UUID) -> bool:
        query = "DELETE FROM resources WHERE id = $1"
        result = await self.connection.execute(query, id)
        return result == "DELETE 1"
