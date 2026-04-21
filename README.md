## Project Overview

Welcome to "Envision HR Project"! This project is a full-stack web application. It consists of four main components: a FastAPI backend, a Next.js frontend, a PostgreSQL database, and an Adminer service for database management. All services are containerized using Docker and orchestrated using Docker Compose, simplifying the setup and deployment process.

## Project Structure

- **Backend**: A FastAPI service that serves as the backend API.
- **Frontend**: A Next.js service that serves as the frontend interface.
- **Database**: A PostgreSQL database to store the application data.

## Prerequisites

Before running this project, ensure you have the following tools installed:

- Docker
- Docker Compose
- Make

## Setup Instructions

### Environment Variables

Create a `.env` file in the project root directory. You can use the provided `.env.example` as a template.

```sh
cp .env.example .env
```

### Building and Running the Containers

#### Development Environment

To build and run the services in development mode, navigate to the project root directory and execute:

```sh
make dev-build
```

This command will build the Docker images and start the containers for the backend, frontend, database, and Adminer in development mode.

#### Production Environment

To build and run the services in production mode:

```sh
docker compose up --build -d
```

### Database Migrations

To handle database migrations, use the provided `Makefile` commands. These commands are designed to work seamlessly with the project setup.

Initialize the database with existing migrations:

```sh
make init
```

## Backend Development Guide

### Module Structure

The backend follows a consistent modular structure. Each module should contain the following files:

- `router.py` - FastAPI route definitions
- `schemas.py` - Pydantic models for request/response validation
- `service.py` - Business logic and database operations
- `models.py` - SQLAlchemy database models

**Example**: The `auth` module (`/backend/src/auth/`) demonstrates this structure:
```
backend/src/auth/
├── __init__.py
├── router.py
├── schemas.py
├── service.py
├── models.py
└── utils.py
```

### Adding a New Module

When creating a new module, follow these steps:

1. **Create the module directory** in `/backend/src/your_module_name/`

2. **Create the required files** following the established pattern:
   ```
   backend/src/your_module_name/
   ├── __init__.py
   ├── router.py     # API endpoints
   ├── schemas.py    # Pydantic models
   ├── service.py    # Business logic
   └── models.py     # Database models
   ```

3. **Define your database models** in `models.py` using SQLAlchemy

4. **Import your models in `env.py`** - This is crucial for SQLAlchemy to recognize your models:
   ```python
   # In backend/alembic/env.py
   from src.your_module_name.models import YourModel
   ```

5. **Generate migration files** after creating/modifying models:
   ```sh
   make mms
   ```

6. **Apply the migrations** to update the database:
   ```sh
   make init
   ```

### Database Migration Workflow

When working with database models during development:

1. **Start your development environment**:
   ```sh
   make dev-build
   ```

2. **Create or modify your models** in the respective `models.py` files

3. **Import new models** in `/backend/alembic/env.py`:
   ```python
   from src.your_module.models import YourNewModel
   ```

4. **Generate migration files** (run from project root):
   ```sh
   make mms
   ```
   This creates a new migration file in `/backend/alembic/versions/`

5. **Apply the migrations**:
   ```sh
   make init
   ```

6. **Verify the migration** was applied:
   ```sh
   make head
   ```

7. **Register your router** in `/backend/src/main.py`:
   ```python
   from src.your_module import router as your_module_router
   
   app.include_router(your_module_router.router, tags=["Your Module"], prefix="/your-module")
   ```

### Hot Reloading and Dependencies

The development environment is configured with **hot reloading**, which means:

- **Code changes**: The backend automatically reloads when you modify Python files
- **New dependencies**: If you add packages to `requirements.txt` or modify the `Dockerfile`, you must restart the containers to rebuild with new dependencies:
  ```sh
  make dev-restart
  ```

### Important Notes

- **Always run commands from the project root**, not from the `/backend/` directory
- **Import all models in `env.py`** to avoid SQLAlchemy detection issues
- **Follow the established module structure** for consistency
- **Register new routers in `main.py`** to make endpoints available
- **Restart containers after dependency changes** to rebuild with new packages
- **Test your migrations** in development before deploying

### Sample Module Tutorial

For a complete example of creating a new module with CRUD operations and AI features, see [SAMPLE_MODULE.md](SAMPLE_MODULE.md). This tutorial demonstrates:

- Creating a complete module structure
- Implementing CRUD operations
- Adding AI features with LangChain
- Proper model relationships and migrations
- Best practices and patterns

## Service Details

### Backend

The backend is a FastAPI application defined in the `backend` directory. It handles API requests and interacts with the PostgreSQL database.

- **Dockerfile**: Located in the `backend` directory
- **Ports**: 8000  

### Frontend

The frontend is a Next.js application defined in the `frontend` directory. It provides the user interface for the application.

- **Dockerfile**: Located in the `frontend` directory
- **Ports**: 3000

### Database

The database is a PostgreSQL instance used to store application data.

- **Docker Image**: `postgres:15-alpine`
- **Ports**: 5432

## Available Make Commands

### Development Commands
- `make dev-up` - Start development containers
- `make dev-down` - Stop development containers
- `make dev-restart` - Restart development containers with rebuild
- `make dev-build` - Build and start development containers

### Production Commands
- `make up` - Start production containers
- `make down` - Stop production containers
- `make restart` - Restart production containers with rebuild

### Database Commands
- `make init` - Apply database migrations
- `make mms` - Generate new migration files
- `make migrate` - Apply migrations (alternative)
- `make head` - Show current migration version

### Utility Commands
- `make rm_vol` - Remove all Docker volumes
- `make vol_ls` - List Docker volumes

## Additional Commands

- **Stopping the development environment**:
```sh
make dev-down
```

- **Stopping the production environment**:
```sh
docker-compose down
```

## Deployment Considerations

### NEXT_PUBLIC_API_URL

The `NEXT_PUBLIC_API_URL` environment variable, currently set to `http://localhost:8000` for local development, needs to be updated to the deployed API URL once the application is deployed. For example:

```
NEXT_PUBLIC_API_URL=https://your-deployed-backend-url.com
```

## Downloading Project Files from EC2

To download the project from your EC2 instance to your local machine:

### 1. SSH into the EC2 instance and create the zip

```sh
ssh -i YOUR-KEY.pem ubuntu@YOUR-EC2-PUBLIC-IP
cd /home/ubuntu/envision-benefits-marketing
bash package-for-download.sh
```

This creates `/home/ubuntu/envision-benefits-marketing.zip`, excluding `.git`, `node_modules`, build artifacts, and `.env`.

### 2. Download the zip via SCP (run on your local machine)

**Windows (PowerShell / Command Prompt):**
```
scp -i YOUR-KEY.pem ubuntu@YOUR-EC2-PUBLIC-IP:/home/ubuntu/envision-benefits-marketing.zip C:\Users\kristin\Desktop\
```

**macOS / Linux:**
```sh
scp -i YOUR-KEY.pem ubuntu@YOUR-EC2-PUBLIC-IP:/home/ubuntu/envision-benefits-marketing.zip ~/Desktop/
```

Replace `YOUR-KEY.pem` with the path to your EC2 key pair file and `YOUR-EC2-PUBLIC-IP` with the instance's public IP address.

## Useful Links

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

For any issues or contributions, please refer to the contributing guidelines provided in the project's documentation or contact the project maintainers.

## Important Security Reminder

- Use Strong Passwords: Always use strong, unique passwords for database users and application credentials.
- Secure .env Files: Do not commit .env files or any files containing sensitive information to version control systems if the repository is public.
- Regularly Update Secrets: Regularly update your API keys and secrets, and revoke any that are no longer in use.
- Monitor Services: Keep an eye on your services for any unusual activity or performance issues.
- Firewall Settings: Ensure your server's firewall settings only allow necessary traffic.

If you encounter any issues or have questions, please refer to the documentation of the respective services or reach out for support.

This README should provide a comprehensive guide for setting up and running the "Fitness AI Project". If you have any further questions or need more details, explore the included documentation or reach out to support.