# Parcel Tracer Backend

The backend service for the Parcel Tracer platform. It handles real-time parcel tracking, user and agent management, and parcel request workflows. It provides RESTful APIs and WebSocket endpoints for parcel requests, status updates, agent availability, and live location tracking.

## Tech Stack Used

* **Framework:** FastAPI
* **Database:** PostgreSQL
* **Database Driver:** asyncpg (async raw SQL queries)
* **Authentication:** JWT (access + refresh tokens via PyJWT)
* **Password Hashing:** pwdlib (Argon2)
* **Real-time:** WebSockets
* **Caching / Pub-Sub:** Redis
* **API Documentation:** Built-in Swagger UI (provided by FastAPI)

## Prerequisites

* Python: 3.14+
* PostgreSQL instance (local or remote)
* Redis instance (local or remote)
* `.env` file with required environment variables (see below)

## Running Locally

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd backend-v1
```

### 2. Create & Activate a Virtual Environment

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or if using `uv`:

```bash
uv sync
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root and fill in the required variables:

```env
# Database
database_name = "your_database_name"
database_password = "your_password"
database_port = 5432

# Token secret
SECRET_KEY = "your-secret-key"
```

### 5. Start the FastAPI Server

```bash
uvicorn app.main:app --reload
```

The API will be available at: **http://localhost:8000**  
Swagger docs will be available at: **http://localhost:8000/docs**

## API Overview

### Auth (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user |
| POST | `/login` | Login and receive tokens |
| GET | `/refresh` | Refresh access token |
| GET | `/profile` | Get current user profile |
| GET | `/logout` | Logout current user |

### Parcels (`/api/parcel`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/request` | Create a parcel request (customer only) |
| POST | `/accept` | Accept a parcel request (customer only) |
| POST | `/decline` | Decline a parcel request (customer only) |
| POST | `/status/update` | Update parcel status (agent only) |
| GET | `/get-request` | Get a parcel request by ID |
| GET | `/sent-requests` | Get all sent parcel requests |
| GET | `/received-requests` | Get all received parcel requests |
| GET | `/parcels` | Get parcels created or to receive |
| GET | `/read` | Get a single parcel by ID |
| WS | `/receive_notification/{user_id}` | WebSocket for real-time parcel notifications |

### Agents (`/api/agent`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/go-online/{user_id}` | WebSocket for agent to go online |
| WS | `/search-agents/{user_id}` | WebSocket to search for nearby agents |
