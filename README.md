# TaskFlow — Production-Grade Task Management API

A fully-featured Django REST Framework task management system with JWT authentication, team-based access control, query optimization, caching, and containerization.

## Features

✅ **Authentication & Authorization**
- JWT-based token authentication (SimpleJWT)
- Role-based access control (owner vs. member)
- Team-scoped data isolation
- Object-level permissions

✅ **API Usability**
- Advanced filtering (status, priority, assigned user, project)
- Full-text search (title, description)
- Custom pagination with metadata
- Query optimization (N+1 prevention)

✅ **Performance**
- Redis caching with TTL and event-based invalidation
- Database query optimization (select_related, prefetch_related)
- Aggregation and annotation for dashboards
- Celery for background tasks

✅ **Containerization**
- Multi-service Docker setup (Django, PostgreSQL, Redis, Celery)
- Health checks and graceful shutdown
- Multi-stage builds for optimized image size
- Environment-based configuration

## Technology Stack

- **Backend**: Django 6.0+, Django REST Framework
- **Database**: PostgreSQL (or SQLite for dev)
- **Cache**: Redis
- **Task Queue**: Celery with Celery Beat
- **Authentication**: SimpleJWT
- **Containerization**: Docker & docker-compose
- **Python**: 3.11+

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Redis (optional for local dev without caching)
- PostgreSQL (optional; SQLite works for dev)

### Setup

1. Clone the repo:
```bash
git clone https://github.com/anilreddysbs/TaskFlow.git
cd TaskFlow
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment (copy .env.example to .env and update):
```bash
cp .env.example .env
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Access the API:
- Admin: http://127.0.0.1:8000/admin/
- API Root: http://127.0.0.1:8000/api/
- Docs: http://127.0.0.1:8000/api/schema/ (if you add drf-spectacular)

### Obtain JWT Token

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Use the `access` token in subsequent requests:
```bash
curl http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Docker Setup (Production)

### Prerequisites

- Docker and docker-compose

### Quick Start

1. Copy environment template:
```bash
cp .env.example .env
```

2. Update `.env` with production values (ESPECIALLY `DJANGO_SECRET_KEY`):
```bash
DJANGO_SECRET_KEY=your-super-secret-key
DEBUG=False
DB_PASSWORD=strong_password_here
```

3. Build and start services:
```bash
docker-compose up -d
```

4. Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

5. Create superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

6. Access the API:
- Web: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

### View Logs

```bash
docker-compose logs -f web          # Django logs
docker-compose logs -f celery_worker # Celery worker logs
docker-compose logs -f db           # PostgreSQL logs
```

### Stop Services

```bash
docker-compose down       # Stop all containers
docker-compose down -v    # Stop and remove volumes (destroys data!)
```

## Project Structure

```
TaskFlow/
├── taskflow/              # Project settings
│   ├── settings.py       # Django settings (cache, DB, JWT, Celery)
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py         # Celery configuration
│
├── api/                   # REST API layer
│   ├── views.py          # ViewSets with optimized queries
│   ├── serializers.py    # DRF serializers
│   ├── permissions.py    # Authorization (IsTeamOwner, etc.)
│   ├── filters.py        # Task filtering
│   ├── pagination.py     # Custom pagination
│   ├── cache_utils.py    # Cache management & invalidation
│   └── optimization_mixins.py  # Query optimization helpers
│
├── users/                # Custom User model
├── teams/                # Team management
├── projects/             # Projects within teams
├── tasks/                # Task management
├── comments/             # Task comments
├── notifications/        # Notification system
│
├── docs/
│   ├── INTERVIEW_AND_PRACTICES.md   # Interview Q&A
│   └── PRODUCTION_GUIDE.md          # Detailed technical guide
│
├── requirements.txt      # Python dependencies
├── Dockerfile            # Multi-stage Docker image
├── docker-compose.yml    # Multi-service orchestration
├── .env.example          # Environment template
├── .gitignore
├── manage.py
└── README.md            # This file
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/token/` | Obtain JWT token |
| POST | `/api/token/refresh/` | Refresh access token |
| GET | `/api/me/` | Get current user |

### Resources

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/teams/` | List/create teams |
| GET/POST | `/api/projects/` | List/create projects |
| GET/POST | `/api/tasks/` | List/create tasks |
| GET/POST | `/api/comments/` | List/create comments |

### Query Parameters (Tasks)

```
GET /api/tasks/?status=TODO&priority=HIGH&assigned_to=5&project=2&search=bug&ordering=-created_at&page=1&page_size=20
```

- `status`: Filter by status (TODO, IN_PROGRESS, DONE, BLOCKED)
- `priority`: Filter by priority (LOW, MEDIUM, HIGH, CRITICAL)
- `assigned_to`: Filter by assigned user ID
- `project`: Filter by project ID
- `search`: Full-text search on title and description
- `ordering`: Sort by field (use `-` for descending)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)

## Performance Optimization

### Query Optimization

All ViewSets use `select_related()` and `prefetch_related()` to prevent N+1 queries:

```python
# Bad: N+1 queries
tasks = Task.objects.all()  # 1 query
for task in tasks:
    print(task.project.name)  # N queries

# Good: Single query with JOINs
tasks = Task.objects.select_related('project', 'project__team', 'assigned_to', 'created_by')
```

### Caching

Redis caches expensive operations:
- **Task list**: 5-minute TTL (invalidated on change)
- **Dashboard stats**: 5-minute TTL
- **User teams**: 1-hour TTL

Manual invalidation happens on `post_save` and `post_delete` signals.

### Pagination

Large result sets are paginated to limit memory usage and improve response time.

```json
{
  "count": 150,
  "page": 1,
  "page_size": 10,
  "total_pages": 15,
  "results": [...]
}
```

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `DJANGO_SECRET_KEY` (generate with `secrets.token_urlsafe(50)`)
- [ ] Database password set in environment variables
- [ ] HTTPS enabled (nginx/load balancer in front)
- [ ] CORS configured for trusted origins only
- [ ] Rate limiting enabled
- [ ] Monitoring and alerting setup
- [ ] Database backups automated
- [ ] Secrets not logged or exposed in errors

## Common Commands

### Django

```bash
python manage.py makemigrations    # Create migrations
python manage.py migrate           # Apply migrations
python manage.py createsuperuser   # Create admin user
python manage.py collectstatic     # Collect static files
python manage.py shell             # Interactive Python shell
```

### Docker

```bash
docker-compose ps                  # List running containers
docker-compose exec web bash       # Bash into web container
docker-compose logs -f web         # Follow logs
docker-compose restart web         # Restart service
docker-compose scale celery_worker=3  # Scale workers
```

### Celery

```bash
celery -A taskflow worker --loglevel=info       # Start worker
celery -A taskflow beat --loglevel=info         # Start beat scheduler
celery -A taskflow inspect active               # Check active tasks
```

## Monitoring & Debugging

### Enable Django Debug Toolbar (Development Only)

```bash
pip install django-debug-toolbar
# Add to INSTALLED_APPS in settings.py
# Configure as per DRF docs
```

### View Database Queries

```python
from django.db import connection
print(connection.queries)  # Print all SQL queries executed
```

### Monitor Celery

```bash
pip install flower
celery -A taskflow flower   # Start Flower at http://localhost:5555
```

## Testing

```bash
python manage.py test                   # Run all tests
python manage.py test api.tests        # Run specific app tests
python manage.py test --verbosity=2    # Verbose output
```

## Deployment to Production

Refer to [PRODUCTION_GUIDE.md](docs/PRODUCTION_GUIDE.md) for detailed deployment steps, security hardening, and scalability strategies.

## Interview Questions & Learning

Refer to [INTERVIEW_AND_PRACTICES.md](docs/INTERVIEW_AND_PRACTICES.md) and [PRODUCTION_GUIDE.md](docs/PRODUCTION_GUIDE.md) for comprehensive interview questions on:
- JWT & Authentication (5+ questions)
- Authorization & Permissions (8+ questions)
- Query Optimization & N+1 (7+ questions)
- Caching & Redis (5+ questions)
- Filtering & Pagination (4+ questions)
- Docker & Containerization (6+ questions)

## Contributing

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "feat: add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a pull request.

## License

MIT License. See LICENSE file for details.

## Support

For issues, questions, or feedback, open an issue on GitHub or contact the maintainers.

---

**Built with ❤️ for production-grade Django development.**
