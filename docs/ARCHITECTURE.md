# MeterRide Backend Architecture Guide

This guide establishes the architectural boundaries, coding conventions, and folder responsibilities for all backend developers working on the MeterRide platform.

---

## 1. Architectural Layers & Separation of Concerns

MeterRide enforces a strict 3-tier unidirectional architecture:

```
Request ──> [ Routers Layer ] ──> [ Services Layer ] ──> [ Database Layer ] ──> Storage
                   │                       │
             Input Validation        Business Logic
             (Pydantic Schemas)      & Orchestration
```

### Layer Rules:

1. **Routers (`app/routers/`)**:
   - Solely responsible for HTTP interface concerns (request parsing, route decorators, status codes, dependency injection).
   - Must **NEVER** contain business logic, calculations, or raw database queries.
   - Delegates work directly to service functions or service classes.

2. **Services (`app/services/`)**:
   - Contains pure domain logic and business rules (e.g., fare calculations, matching algorithms, token generation).
   - Consumes database sessions injected from routes or repositories.
   - Independent of HTTP transport details (does not inspect `Request` objects or raise direct raw HTTP responses without abstraction).

3. **Models (`app/models/`)**:
   - Contains SQLAlchemy declarative models inheriting from `app.database.base.Base`.
   - Defines database tables, columns, indexes, foreign keys, and relationships.

4. **Schemas (`app/schemas/`)**:
   - Contains Pydantic models for request validation, data transfer, and response serialization.
   - Decoupled from database models to prevent over-exposing internal database structures.

5. **Core (`app/core/`)**:
   - Cross-cutting application configuration (`config.py`) and security primitives (`security.py`).

6. **Utils (`app/utils/`)**:
   - Generic, reusable utility functions and helpers (formatting, datetime helpers, etc.).

---

## 2. Planned Router Modules

Future feature branches will add the following modules to `app/routers/` and register them via `app.include_router(...)` in `app/main.py`:

- `auth.py`: Authentication, token generation, login, registration
- `users.py`: Rider profile management and preferences
- `drivers.py`: Driver onboarding, status (online/offline), documents
- `vehicles.py`: Vehicle registrations, inspection records
- `rides.py`: Ride request, ride acceptance, status updates
- `matching.py`: Proximity-based driver matching and dispatching
- `location.py`: Driver location telemetry and GPS tracking
- `pricing.py`: Fare quotes, dynamic pricing, surge rates
- `payments.py`: Payment methods, charges, invoices, webhooks
- `notifications.py`: Push notifications, SMS alerts, templates
- `ratings.py`: Ratings and reviews for riders and drivers
- `safety.py`: SOS alarms, emergency contact alerts
- `admin.py`: Operational dashboards and administrative actions

---

## 3. Database & Migrations Workflow

1. Define SQLAlchemy models inside `app/models/`.
2. Ensure new models are imported in `app/models/__init__.py` or `alembic/env.py` so they are registered with `Base.metadata`.
3. Generate a revision:
   ```bash
   alembic revision --autogenerate -m "describe changes"
   ```
4. Inspect the generated migration in `alembic/versions/`.
5. Apply migration:
   ```bash
   alembic upgrade head
   ```
