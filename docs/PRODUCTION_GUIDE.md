# TaskFlow — Complete Technical Documentation

This document covers all production-level features implemented in TaskFlow, including authentication, authorization, filtering, caching, query optimization, and containerization.

---

## Table of Contents

1. [JWT & Authentication](#jwt--authentication)
2. [Authorization & Permissions](#authorization--permissions)
3. [Query Optimization & N+1 Problems](#query-optimization--n1-problems)
4. [Caching with Redis](#caching-with-redis)
5. [Filtering, Search & Pagination](#filtering-search--pagination)
6. [Docker & Containerization](#docker--containerization)
7. [Interview Questions](#interview-questions-comprehensive-set)
8. [Production Best Practices](#production-best-practices)

---

## JWT & Authentication

### What is JWT?

JWT (JSON Web Token) is a stateless authentication mechanism consisting of three parts:
- **Header**: Token type and hashing algorithm (e.g., HS256).
- **Payload**: Claims (data) like user ID, expiry, scopes.
- **Signature**: HMAC signed with SECRET_KEY to prevent tampering.

### SimpleJWT in TaskFlow

SimpleJWT provides:
- `TokenObtainPairView`: POST credentials → get `access` and `refresh` tokens.
- `TokenRefreshView`: POST refresh token → get new `access` token.
- `JWTAuthentication`: Validates tokens and sets `request.user`.

### Token Flow

1. User POSTs credentials to `/api/token/`.
2. Server validates, issues short-lived `access` and longer-lived `refresh` tokens.
3. Client includes `Authorization: Bearer <access>` in request headers.
4. DRF validates token and sets `request.user`.
5. When `access` expires, client POSTs `refresh` to `/api/token/refresh/` for a new `access`.

### Security Considerations

- **Never log tokens**: Tokens are credentials.
- **HTTPS only**: Tokens are vulnerable over plaintext HTTP.
- **Short-lived access**: Limit exposure window (e.g., 5 minutes).
- **Refresh rotation**: Consider rotating refresh tokens on use.
- **Token revocation**: Use a blacklist for logout or use short lifetimes.

Q: Why is the signature critical in JWTs?
- A: The signature prevents tampering. If an attacker modifies the payload, the signature becomes invalid because it's computed using the SECRET_KEY, which only the server knows.

---

## Authorization & Permissions

### Authentication vs Authorization

- **Authentication**: Verifies identity (who you are). Handled by JWT.
- **Authorization**: Determines access (what you can do). Handled by permission classes.

### Permission Classes in TaskFlow

#### HasPermission (List/Create)
Runs before object lookup. Examples:
- `IsAuthenticated`: User is logged in.

#### HasObjectPermission (Retrieve/Update/Delete)
Runs per object. Examples:
- `IsTeamOwnerOrMemberReadOnly`: Team owner has full access; members can only read.
- `IsProjectOwnerOrTeamMemberReadOnly`: Project creators/team owners can write; team members can read.
- `IsTaskCreatorOrTeamMemberReadOnly`: Task creators can write; team members can read.

### Role-based Behavior

```python
# Owner can do anything; member can read
if team.owner == request.user:
    return True  # Full access

if request.method in SAFE_METHODS:  # GET, HEAD, OPTIONS
    return request.user in team.members.all()

return False  # Unsafe methods forbidden for members
```

### Queryset Filtering

Prevent data leakage by filtering querysets:

```python
def get_queryset(self):
    user = self.request.user
    if user.is_superuser:
        return Task.objects.all()
    return Task.objects.filter(
        Q(project__team__owner=user) | Q(project__team__members=user)
    ).distinct()
```

Q: Why filter querysets even with object-level permissions?
- A: Filtering prevents users from seeing/listing objects they shouldn't access. Permissions prevent unauthorized changes, but filters prevent even seeing records.

Q: What's the difference between `has_permission` and `has_object_permission`?
- A: `has_permission` runs before object retrieval (e.g., list/create); `has_object_permission` runs per object after retrieval (retrieve/update/delete).

---

## Query Optimization & N+1 Problems

### The N+1 Query Problem

When fetching a list of objects, if each object access causes a database query, you get N+1 queries:
1. One query to fetch the list.
2. N queries, one per object (e.g., to fetch related objects).

**Bad Example**:
```python
tasks = Task.objects.all()  # 1 query
for task in tasks:
    print(task.assigned_to.username)  # N queries (one per task)
```

Result: 1 + N queries.

**Why it's slow**: Serializers and list endpoints always iterate and access related objects. With 100 tasks and 3 ForeignKey fields, you get 301 queries!

### select_related() for ForeignKey

Use `select_related()` to JOIN and fetch ForeignKey/OneToOne relationships in one query.

```python
# BAD: N+1 queries
tasks = Task.objects.all()

# GOOD: 1 query with JOINs
tasks = Task.objects.select_related('project', 'assigned_to', 'created_by')

# Multiple levels: task → project → team
tasks = Task.objects.select_related('project__team', 'assigned_to', 'created_by')
```

**When to use**:
- Foreign keys (always).
- OneToOne relationships.
- Few related objects expected.

**When NOT to use**:
- Many-to-many (use prefetch_related).
- Reverse relationships (use prefetch_related).
- If the join would be huge (use pagination + lazy loading).

### prefetch_related() for Reverse Relationships

Use `prefetch_related()` for reverse ForeignKey and ManyToMany (makes separate queries but fetches all at once).

```python
# BAD: N+1 queries
comments = Comment.objects.all()
for comment in comments:
    print(comment.author.username)  # N queries

# GOOD: 2 queries (comments + authors in one shot)
comments = Comment.objects.prefetch_related('author')

# Nested: comments with related task and project
comments = Comment.objects.prefetch_related(
    'task__project__team'
).select_related('author')
```

**When to use**:
- Reverse ForeignKeys (Task.comments).
- Many-to-many (Team.members).
- Complex nested relationships.

**When NOT to use**:
- ForeignKeys (use select_related).
- If filtering the related set (use filter + subquery).

### Aggregation & Annotation

Use `aggregate()` and `annotate()` to compute statistics without fetching all objects.

```python
# Aggregate: Single result across queryset
Task.objects.aggregate(
    total=Count('id'),
    avg_priority=Avg('priority'),
    max_created=Max('created_at')
)
# Result: {'total': 50, 'avg_priority': 2.5, 'max_created': datetime(2024, 1, 1)}

# Annotate: Add computed field to each object
Task.objects.annotate(
    comment_count=Count('comments')
).values('id', 'title', 'comment_count')
# Result: [{'id': 1, 'title': 'Task 1', 'comment_count': 3}, ...]
```

### SQL Generated

With `select_related('project', 'assigned_to', 'created_by')`:
```sql
SELECT "tasks_task".*, "projects_project".*, "auth_user"."assigned_to", "auth_user"."created_by"
FROM "tasks_task"
LEFT JOIN "projects_project" ON "tasks_task"."project_id" = "projects_project"."id"
LEFT JOIN "auth_user" ON "tasks_task"."assigned_to_id" = "auth_user"."id"
LEFT JOIN "auth_user" ON "tasks_task"."created_by_id" = "auth_user"."id";
```

Without optimization:
```sql
SELECT * FROM tasks;
SELECT * FROM projects WHERE id = ?;  -- repeated for each task
SELECT * FROM auth_user WHERE id = ?;  -- repeated for assigned_to
SELECT * FROM auth_user WHERE id = ?;  -- repeated for created_by
```

Q: When is it safe to use select_related?
- A: When joining a small number of rows (FK relationships that don't explode the result set).

Q: How does prefetch_related differ from select_related in terms of SQL?
- A: prefetch_related uses separate queries (one for each table), then Python joins them in memory. select_related uses SQL JOINs in a single query.

---

## Caching with Redis

### What is Redis?

Redis is an in-memory data store that acts as a cache layer between the application and the database.

**Why it's fast**:
- In-memory (RAM): microseconds vs. disk I/O (milliseconds).
- Simple key-value structure: O(1) lookups.
- No query parsing: Direct byte operations.

### Cache Hit vs Cache Miss

- **Cache Hit**: Data found in Redis; return immediately (usually <1ms).
- **Cache Miss**: Data not in Redis; fetch from database, store in cache, return.

### Cache Invalidation

When data changes, remove stale cache entries. Strategies:

1. **Time-based (TTL)**: Cache expires after N seconds (simple, stale data risk).
2. **Event-based (Signals)**: Delete cache on create/update/delete.
3. **Manual**: App explicitly invalidates on complex operations.

### TaskFlow Caching Strategy

```python
# Invalidate task caches when a task changes
@receiver(post_save, dispatch_uid="invalidate_task_cache_on_save")
def invalidate_task_cache_on_save(sender, instance, created, **kwargs):
    if sender is Task:
        cache.delete('tasks:list')
        cache.delete(f'tasks:detail:{instance.id}')
        cache.delete('dashboard:stats')
```

### Cache Timeouts

- Dashboard stats: 5 minutes (aggregation is expensive).
- Task list: Invalidated on change (event-based).
- User detail: 1 hour (stable data).

Q: What happens if you forget to invalidate cache?
- A: Stale data is served. Users see outdated information until the cache TTL expires. Data corruption risk if cached data conflicts with DB.

Q: Is Redis a database?
- A: No, Redis is a volatile cache. Data is lost on server restart unless persistence (AOF/RDB) is enabled. Use a true database (PostgreSQL) for permanent storage.

---

## Filtering, Search & Pagination

### Query Parameters

Query parameters are passed in the URL query string and extracted by DRF:
- `GET /api/tasks/?status=TODO&priority=HIGH&page=2&page_size=20`

DRF uses **filter backends** to process these:

1. **DjangoFilterBackend**: Exact/custom filtering (e.g., status, priority).
2. **SearchFilter**: Full-text search (e.g., title, description).
3. **OrderingFilter**: Sorting (e.g., created_at, due_date).

### TaskFilter Implementation

```python
class TaskFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    priority = django_filters.CharFilter(field_name='priority', lookup_expr='iexact')
    assigned_to = django_filters.NumberFilter(field_name='assigned_to_id')
    project = django_filters.NumberFilter(field_name='project_id')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'assigned_to', 'project']
```

Usage:
- `GET /api/tasks/?status=TODO&priority=HIGH` → filters tasks with status TODO and priority HIGH.
- `GET /api/tasks/?search=bug` → searches title and description for "bug".
- `GET /api/tasks/?ordering=-created_at` → sorts by created_at descending.

### Pagination

Without pagination, large datasets are slow and memory-intensive. Pagination breaks results into pages.

**Custom Pagination**:
```python
class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'total_pages': self.page.paginator.num_pages,
            'results': data,
        })
```

Response:
```json
{
    "count": 150,
    "page": 2,
    "page_size": 10,
    "total_pages": 15,
    "results": [...]
}
```

Q: Why limit page_size to max_page_size?
- A: Prevent DoS attacks where clients request millions of records at once. Limits memory/database load.

---

## Docker & Containerization

### Container vs Image

- **Image**: Blueprint (like a class). Contains code, dependencies, and runtime.
- **Container**: Instance of an image (like an object). Isolated process running the image.

### Dockerfile Multi-stage Build

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["gunicorn", ...]
```

**Why**: Removes build tools from the final image, reducing size (builder stage ~500MB, runtime ~300MB).

### Volumes

Persistent storage that survives container restart.

```yaml
volumes:
  postgres_data:/var/lib/postgresql/data
```

Use cases:
- Database storage (postgres_data).
- Application code (for development).
- Logs.

### Networks

Containers on the same network can communicate by service name.

```yaml
services:
  web:
    networks:
      - taskflow_network
  db:
    networks:
      - taskflow_network
```

In code: `DATABASE_URL=postgresql://user:pass@db:5432/taskflow` (uses `db` hostname from network DNS).

### Health Checks

Docker monitors container health and restarts if unhealthy.

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/me/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Multi-service Architecture

TaskFlow stack:
- **Web**: Django app (port 8000).
- **DB**: PostgreSQL (port 5432).
- **Redis**: Cache/broker (port 6379).
- **Celery Worker**: Background tasks.
- **Celery Beat**: Scheduled tasks.

Each service is isolated, scalable, and replaceable.

Q: Why use Docker for development?
- A: Ensures consistency between dev and production. Eliminates "works on my machine" issues.

Q: What's the difference between volumes and bind mounts?
- A: Volumes are managed by Docker (better for production). Bind mounts are direct host paths (good for development).

---

## Interview Questions (Comprehensive Set)

### General

1. Explain the full authentication flow from login to API call in TaskFlow.
2. What's the difference between authentication and authorization?
3. How would you implement role-based access control (RBAC)?
4. What's the purpose of DEFAULT_PERMISSION_CLASSES in DRF settings?

### JWT & Tokens

5. How does JWT prevent tampering?
6. Why should access tokens be short-lived?
7. How would you implement token revocation?
8. What's a refresh token and why do you need it?

### Permissions

9. When would you use object-level permissions vs list-level permissions?
10. How does `has_permission` differ from `has_object_permission`?
11. Why is queryset filtering important even with permissions?
12. How do you prevent data leakage in multi-tenant systems?

### Query Optimization

13. Explain the N+1 query problem and how to detect it.
14. When should you use `select_related` vs `prefetch_related`?
15. What SQL does `select_related` generate?
16. How would you optimize a queryset that includes nested relationships?
17. When should you use `annotate()` instead of fetching and processing in Python?
18. How do you measure the performance impact of query optimization?

### Caching

19. What's a cache miss and what's the performance impact?
20. How would you implement cache invalidation for a complex relationship?
21. What's the difference between TTL-based and event-based invalidation?
22. When should you NOT cache data?
23. How would you debug stale cache issues?

### Filtering & Pagination

24. How do query parameters work in REST APIs?
25. Why is pagination critical for large datasets?
26. What's the difference between offset pagination and cursor pagination?
27. How would you implement search across multiple fields?

### Docker

28. What's the difference between an image and a container?
29. Why use multi-stage builds?
30. How do containers on the same network communicate?
31. What are volumes used for?
32. How would you scale the Celery workers?
33. Why use health checks in Docker?

---

## Production Best Practices

### Security

- **Never commit secrets**: Use environment variables for API keys, database passwords.
- **HTTPS always**: Transport JWT tokens over HTTPS only.
- **Short-lived tokens**: 5-15 minutes for access; hours/days for refresh.
- **Validate input**: Serializer validation catches malformed requests early.
- **Rate limiting**: Use Django Ratelimit or DRF throttling to prevent abuse.
- **CORS carefully**: Restrict origins to trusted domains only.

### Performance

- **Optimize querysets**: Always use `select_related` and `prefetch_related`.
- **Cache aggressively**: Cache expensive aggregations and frequently-accessed data.
- **Paginate large results**: Never return all records at once.
- **Use indexes**: Index foreign keys and filter fields.
- **Monitor slow queries**: Use Django Debug Toolbar (dev) or slow query logs (prod).

### Reliability

- **Health checks**: Monitor container health.
- **Database backups**: Automated daily backups to S3/cloud.
- **Graceful shutdown**: Handle SIGTERM and close connections cleanly.
- **Error logging**: Log all errors to a centralized system (e.g., Sentry).
- **Circuit breakers**: Fail fast on dependency failures (e.g., Redis down).

### Scalability

- **Horizontal scaling**: Run multiple web containers behind a load balancer.
- **Asynchronous tasks**: Offload long operations to Celery workers.
- **Read replicas**: Use PostgreSQL replicas for read-heavy operations.
- **CDN**: Cache static files on a CDN.
- **Microservices**: Consider splitting into separate services as complexity grows.

---

## Deployment Checklist

- [ ] Set `DEBUG=False` in production.
- [ ] Use environment variables for all secrets.
- [ ] Enable HTTPS/TLS.
- [ ] Configure database backups.
- [ ] Set up monitoring and alerting.
- [ ] Load test before going live.
- [ ] Plan a rollback strategy.
- [ ] Document all configuration.
- [ ] Test disaster recovery.
- [ ] Implement rate limiting and DDoS protection.

---

End of documentation. For more details on each section, refer to the code comments and official Django/DRF docs.
