import asyncpg
from app.core.config import settings
from pathlib import Path
'''
The connection pool to the database in use.
'''
pool : asyncpg.pool.Pool 

'''
The database configurations to identify and connect to
the used database in our case the Postgres database.
'''
DATABASE_CONFIG = {
    "user":settings.database_user,
    "host":settings.database_host,
    "database":settings.database_name,
    "port":settings.database_port,
    "password":settings.database_password
}

'''
As we use the pool globally, we use the initialized pool
as the instance of the created pool to connect to the database.
'''
async def connect():
    global pool
    pool = await asyncpg.create_pool(**DATABASE_CONFIG,statement_cache_size=0)
'''
To create all the tables in the database.
'''
async def init_db():
    sql = (Path(__file__).parent / "db_creation.sql").read_text()
    async with pool.acquire() as conn:
        await conn.execute(sql)

'''
To close the created pool on app shutdown.
'''
async def close():
    global pool
    await pool.close()

'''
Function to get the pool 
'''
def get_pool():
    global pool
    return pool