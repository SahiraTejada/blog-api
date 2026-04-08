# Project Assessment - Blog API

> Reviewer: Senior Backend Engineer perspective
> Date: 2026-03-29
> Stack: FastAPI + SQLAlchemy 2.0 + PostgreSQL + Pydantic 2.x

---

## Score: 7.5 / 10

Un proyecto bien estructurado con arquitectura limpia y patrones solidos. Le falta testing, rate limiting, y algunos detalles de produccion para ser un 9+.

---

## Lo que esta bien hecho

### Arquitectura (9/10)
- Separacion de capas clara: Routes -> Services -> Repositories -> Models
- `BaseRepository` generico con CRUD completo, pagination, search, soft-delete
- `BaseService` generico que envuelve el repo con manejo de excepciones
- Patron Repository bien implementado - ningun route accede directo a la DB
- Dependency Injection via FastAPI `Depends()` en todo el proyecto

### Seguridad (7/10)
- bcrypt con 12 rounds para passwords
- JWT con access + refresh tokens
- Token revocation almacenado en DB
- Roles USER/ADMIN con `RoleChecker`
- Ownership verification en update/delete de posts y comments
- Soft-delete en vez de hard-delete (protege datos)
- `SECRET_KEY` validado con minimo 32 chars

### Modelos y DB (8/10)
- SQLAlchemy 2.0 con `Mapped[T]` syntax (moderno)
- UUID como PK en todas las entidades
- Soft-delete consistente via `deleted_at`
- Composite PKs correctos en Likes y Follows
- Migraciones con Alembic configuradas
- `pool_pre_ping=True` para detectar conexiones muertas

### Manejo de errores (8/10)
- Jerarquia de excepciones clara: `AppException` base con subclases por dominio
- Error handler centralizado con 6 handlers especificos
- Codigos de error estandarizados (`ErrorCode` enum)
- Respuestas diferentes en dev vs produccion (sin stack traces en prod)
- Logging estructurado con contexto del request

### Code Quality (7/10)
- Type hints en todo el codebase
- `@overload` para type narrowing en metodos con Union returns
- Docstrings detallados
- `utc_now()` centralizado para manejo de fechas
- flake8, mypy, black, isort configurados
- Pre-commit hooks configurados

---

## Lo que falta (por prioridad)

### 1. Testing (CRITICO) - No existe

**Estado actual:** 0 tests. Solo un `tests/__init__.py` vacio.

**Impacto:** Sin tests no puedes:
- Refactorizar con confianza
- Detectar regresiones
- Validar business rules
- Hacer CI/CD confiable

**Lo que necesitas:**
```
tests/
  conftest.py              -> fixtures (db session, test client, auth headers)
  factories/               -> model factories (UserFactory, PostFactory)
  unit/
    services/              -> test business logic aislada
    repositories/          -> test queries con DB de test
  integration/
    routes/                -> test endpoints end-to-end
```

**Minimo viable:**
- Tests para auth (register, login, refresh, logout)
- Tests para authorization (user no puede editar post de otro)
- Tests para soft-delete (borrar no elimina, restaurar funciona)
- Tests para pagination (pagina 1, ultima pagina, pagina vacia)

---

### 2. Rate Limiting (ALTO) - Archivo vacio

**Estado actual:** `app/api/middleware/rate_limiter.py` tiene 0 lineas.

**Riesgo:** Sin rate limiting:
- Login brute-force ilimitado
- Spam de registros
- DoS por queries costosas (search, pagination)

**Solucion recomendada:** `slowapi` (wrapper de `limits` para FastAPI)

**Endpoints criticos:**
| Endpoint | Limite sugerido |
|----------|----------------|
| `POST /auth/login` | 5/min por IP |
| `POST /auth/register` | 3/min por IP |
| `POST /auth/refresh` | 10/min por token |
| `POST /likes/` | 30/min por user |
| `POST /follow/` | 20/min por user |

---

### 3. Archivos vacios (MEDIO)

| Archivo | Estado | Accion |
|---------|--------|--------|
| `app/utils/decorators.py` | 0 bytes | Eliminar o implementar |
| `app/utils/validator_utils.py` | 0 bytes | Eliminar (ya existe `validators.py` con contenido) |
| `app/api/middleware/rate_limiter.py` | 0 bytes | Implementar (ver punto 2) |

Archivos vacios en el repo son deuda tecnica visible. Si no se van a usar, eliminarlos.

---

### 4. CORS en produccion (ALTO)

**Estado actual:**
```python
ALLOWED_ORIGINS: list[str] = ["*"]   # Acepta todo
ALLOWED_HOSTS: list[str] = ["*"]     # Acepta todo
```

**Problema:** El default `["*"]` esta bien para desarrollo pero NUNCA debe llegar a produccion.

**Solucion:** Documentar en `.env.example` que en produccion DEBE ser:
```env
ALLOWED_ORIGINS=["https://mi-frontend.com"]
ALLOWED_HOSTS=["api.mi-dominio.com"]
```

---

### 5. Logging estructurado (MEDIO)

**Estado actual:** `logging.getLogger(__name__)` en algunos archivos, pero sin configuracion global. No hay formato estandar, nivel configurable, ni output a archivo/servicio.

**Lo que falta:**
- Configuracion centralizada de logging (nivel, formato, handlers)
- Request ID en cada log para tracing
- Formato JSON para log aggregators (ELK, Datadog, etc.)

---

### 6. Request ID middleware (MEDIO)

**Estado actual:** `error_handler.py` referencia `request.state.request_id` pero nada lo setea.

**Impacto:** Sin request ID no puedes correlacionar logs de un mismo request cuando debuggeas en produccion.

**Solucion:** Middleware que genere UUID por request y lo ponga en `request.state` y en response headers.

---

### 7. Caching (BAJO - futuro)

No hay caching. Para un blog API, estos endpoints son candidatos:
- `GET /posts` (listado publico) - cache 30-60s
- `GET /posts/{uuid}` (post individual) - cache 60s, invalidar en update
- `GET /follow/{uuid}/count` (contadores) - cache 30s
- `GET /likes/post/{uuid}/count` (contadores) - cache 15s

No es urgente, pero cuando el trafico crezca, Redis como cache layer es el paso natural.

---

### 8. Docker / CI-CD (BAJO - infraestructura)

No hay `Dockerfile`, `docker-compose.yml`, ni pipeline de CI/CD.

**Minimo para produccion:**
- `Dockerfile` multi-stage (build + runtime)
- `docker-compose.yml` con app + postgres + redis
- GitHub Actions: lint + type-check + tests en cada PR

---

## Resumen de scores por area

| Area | Score | Notas |
|------|-------|-------|
| Arquitectura | 9/10 | Capas bien separadas, generics, DI |
| Modelos / DB | 8/10 | SQLAlchemy 2.0, soft-delete, UUIDs |
| Seguridad | 7/10 | JWT + bcrypt + roles, falta rate limiting |
| Error handling | 8/10 | Centralizado, estructurado, dev/prod diferenciado |
| Code quality | 7/10 | Types, linting, overloads. Falta tests |
| Testing | 0/10 | No existe |
| Produccion readiness | 4/10 | Sin rate limit, sin Docker, sin CI/CD, sin logging config |
| Documentacion | 7/10 | Docstrings buenos, falta API docs externas |

---

## Roadmap sugerido

```
Sprint 1 (inmediato):
  - Implementar test suite basico (auth + authorization + CRUD)
  - Implementar rate limiting en auth endpoints
  - Eliminar archivos vacios

Sprint 2:
  - Request ID middleware
  - Logging estructurado con configuracion
  - Docker + docker-compose
  - CI pipeline (lint + mypy + tests)

Sprint 3:
  - Tests de integracion completos (>80% coverage)
  - Caching con Redis para endpoints publicos
  - API docs con ejemplos (Swagger ya lo genera, pero mejorar)
  - Health check que verifique DB connectivity

Sprint 4 (pre-produccion):
  - Load testing (locust o k6)
  - Security audit final
  - Monitoring setup (Prometheus metrics)
  - Deploy pipeline (staging -> produccion)
```
