import asyncpg
from app.core.config import settings
'''
The connection pool to the database in use.
'''
pool : asyncpg.pool.Pool 

'''
The database configurations to identify and connect to
the used database in our case the Postgres database.
'''
DATABASE_CONFIG = {
    "user":"postgres",
    "host":"localhost",
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
    pool = await asyncpg.create_pool(**DATABASE_CONFIG)


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