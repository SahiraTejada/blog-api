# Blog API - Plan de Implementacion y Correcciones

**Fecha:** 2026-04-08
**Branch:** `review-code`
**Alcance:** Correcciones de codigo, performance, seguridad y mejoras. Sin tests.

---

## Indice

1. [Bugs y Correcciones Inmediatas](#1-bugs-y-correcciones-inmediatas)
2. [Performance - Eliminacion de N+1 Queries](#2-performance---eliminacion-de-n1-queries)
3. [Seguridad - Hardening](#3-seguridad---hardening)
4. [Observabilidad - Logging y Monitoring](#4-observabilidad---logging-y-monitoring)
5. [Mejoras de Codigo](#5-mejoras-de-codigo)
6. [Archivos Muertos](#6-archivos-muertos)

---

## 1. Bugs y Correcciones Inmediatas

### 1.1 `__repr__` roto en Follow model

**Archivo:** `app/models/follows.py:81`
**Problema:** Falta parentesis de cierre en el f-string.

```python
# ACTUAL (bug)
return f"<{self.__class__.__name__}(follower_uuid={self.follower_uuid},followee_uuid={self.followee_uuid}>"

# CORRECCION
return f"<{self.__class__.__name__}(follower_uuid={self.follower_uuid},followee_uuid={self.followee_uuid})>"
```

---

### 1.2 JWT `exp` usa datetime en vez de Unix timestamp

**Archivo:** `app/services/token_service.py:132-137`
**Problema:** El campo `exp` del payload JWT deberia ser un Unix timestamp (`int`), no un objeto `datetime`. Aunque PyJWT acepta ambos, el estandar RFC 7519 especifica NumericDate (seconds since epoch). Esto puede causar incompatibilidades con otros servicios que consuman los tokens.

```python
# ACTUAL
payload: Dict[str, Any] = {
    "sub": str(user_uuid),
    "type": token_type.value,
    "exp": expires_at,               # datetime object
    "iat": utc_now()                  # datetime object
}

# CORRECCION
payload: Dict[str, Any] = {
    "sub": str(user_uuid),
    "type": token_type.value,
    "exp": int(expires_at.timestamp()),   # Unix timestamp
    "iat": int(utc_now().timestamp())     # Unix timestamp
}
```

---

### 1.3 `type: ignore` en schema de usuario

**Archivo:** `app/schemas/user.py:104-107`
**Problema:** El `type: ignore[return-value]` oculta un mismatch de tipos. `v.lower()` retorna `str`, pero el tipo esperado es `Optional[EmailStr]`.

```python
# ACTUAL
@field_validator("email")
@classmethod
def normalize_email(cls, v: Optional[EmailStr]) -> Optional[EmailStr]:
    if v is not None:
        return v.lower()  # type: ignore[return-value]
    return v

# CORRECCION - EmailStr acepta str en validacion
@field_validator("email")
@classmethod
def normalize_email(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        return v.lower()
    return v
```

---

### 1.4 Property `full_name` duplicada

**Archivo:** `app/schemas/user.py`
**Problema:** La property `full_name` esta definida identicamente en `UserBaseSchema` (linea 30) y en `UserPublicSchema` (linea 173). Se debe extraer a una clase mixin o solo a la base.

**Solucion:** Crear un mixin `FullNameMixin` o hacer que `UserPublicSchema` herede de `UserBaseSchema` si el schema lo permite. Alternativamente, si los schemas tienen campos diferentes, crear:

```python
class FullNameMixin:
    first_name: str
    last_name: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

---

### 1.5 Post repository: join sin `distinct()` en filtro por categoria

**Archivo:** `app/repositories/post_repository.py:186`
**Problema:** Al filtrar posts por `category_uuid`, el join con la tabla many-to-many puede retornar duplicados si un post tiene multiples categorias.

```python
# ACTUAL
if category_uuid:
    base_query = self.db.query(self.model).join(self.model.categories).filter(Category.uuid == category_uuid)

# CORRECCION
if category_uuid:
    base_query = (
        self.db.query(self.model)
        .join(self.model.categories)
        .filter(Category.uuid == category_uuid)
        .distinct()
    )
```

---

## 2. Performance - Eliminacion de N+1 Queries

### 2.1 CRITICO: Eliminar properties `likes_count` y `comments_count` del modelo Post

**Archivo:** `app/models/posts.py:82-112`
**Problema:** Cada acceso a `.likes_count` o `.comments_count` ejecuta una query SQL independiente. Al listar 50 posts, esto genera 100 queries adicionales.

**Solucion:** Eliminar las properties del modelo y mover la logica de conteo al repositorio usando `func.count()` con subqueries o `outerjoin`. El conteo se calcula en la query principal, no por instancia.

```python
# ELIMINAR del modelo Post las properties likes_count y comments_count

# EN PostRepository - agregar metodo que retorna posts con contadores:
from sqlalchemy import func, select

def get_posts_with_counts(self, ...):
    likes_subq = (
        select(func.count())
        .where(Likes.post_uuid == Post.uuid)
        .where(Likes.deleted_at.is_(None))
        .correlate(Post)
        .scalar_subquery()
        .label("likes_count")
    )
    comments_subq = (
        select(func.count())
        .where(Comments.post_uuid == Post.uuid)
        .where(Comments.deleted_at.is_(None))
        .correlate(Post)
        .scalar_subquery()
        .label("comments_count")
    )
    query = self.db.query(self.model, likes_subq, comments_subq)
    # ... aplicar filtros, paginacion, etc.
```

**Impacto:** De N+1 queries (201 para 100 posts) a 1 sola query.

---

### 2.2 CRITICO: Token repository filtra en Python en vez de SQL

**Archivo:** `app/repositories/token_repository.py:122-136`
**Problema:** `get_user_tokens()` carga TODOS los tokens del usuario y filtra `is_revoked` / `is_expired` en Python.

**Solucion:**

```python
# CORRECCION - Mover filtros a SQL
def get_user_tokens(
    self,
    user_uuid: UUID,
    token_type: Optional[TokenType] = None,
    include_revoked: bool = False,
    include_expired: bool = False
) -> List[Token]:
    query = self.db.query(self.model).filter(
        self.model.user_uuid == user_uuid,
        self.model.deleted_at.is_(None)
    )

    if token_type:
        query = query.filter(self.model.type == token_type)

    if not include_revoked:
        query = query.filter(self.model.revoked_at.is_(None))

    if not include_expired:
        query = query.filter(self.model.expires_at > utc_now())

    return query.all()
```

---

### 2.3 ALTO: `count_active_sessions` carga tokens para contar

**Archivo:** `app/repositories/token_repository.py:138-166`
**Problema:** Llama a `get_user_tokens()` y luego `len()`. Deberia usar `COUNT(*)` en SQL.

**Solucion:**

```python
def count_active_sessions(
    self,
    user_uuid: UUID,
    token_type: TokenType = TokenType.ACCESS
) -> int:
    from sqlalchemy import func
    return self.db.query(func.count()).filter(
        self.model.user_uuid == user_uuid,
        self.model.type == token_type,
        self.model.revoked_at.is_(None),
        self.model.deleted_at.is_(None),
        self.model.expires_at > utc_now()
    ).scalar() or 0
```

---

### 2.4 ALTO: Cleanup de tokens es iterativo

**Archivo:** `app/repositories/token_repository.py:286-359`
**Problema:** `cleanup_expired()` y `cleanup_revoked()` hacen `.all()` y luego `delete()` uno por uno en un loop.

**Solucion:** Usar bulk delete con una sola query:

```python
def cleanup_expired(self, older_than_days: int = 7) -> int:
    cutoff_date = utc_now() - timedelta(days=older_than_days)
    count = self.db.query(self.model).filter(
        self.model.expires_at < cutoff_date,
        self.model.deleted_at.is_(None)
    ).delete(synchronize_session="fetch")
    self.db.commit()
    return count
```

---

### 2.5 MEDIO: `get_comment_depth()` es O(N) queries

**Archivo:** `app/repositories/comment_repository.py:224-246`
**Problema:** Recorre la cadena de padres con un loop, ejecutando una query por nivel de profundidad.

**Solucion:** Usar recursive CTE:

```python
from sqlalchemy import literal, union_all

def get_comment_depth(self, comment_uuid: UUID) -> int:
    # CTE recursivo para calcular profundidad en una sola query
    base = (
        self.db.query(
            Comments.uuid,
            Comments.parent_comment_uuid,
            literal(0).label("depth")
        )
        .filter(Comments.uuid == comment_uuid)
        .cte(name="comment_chain", recursive=True)
    )

    recursive = (
        self.db.query(
            Comments.uuid,
            Comments.parent_comment_uuid,
            (base.c.depth + 1).label("depth")
        )
        .join(base, Comments.uuid == base.c.parent_comment_uuid)
    )

    cte = base.union_all(recursive)
    result = self.db.query(func.max(cte.c.depth)).scalar()
    return result or 0
```

---

### 2.6 MEDIO: Paginacion con doble query en follows y likes repositories

**Archivos:** `app/repositories/follows_repository.py`, `app/repositories/likes_repository.py`
**Problema:** La paginacion ejecuta `COUNT(*)` y luego `SELECT` por separado.

**Solucion:** Usar window function para obtener total en la misma query:

```python
from sqlalchemy import func, over

# En la query de paginacion:
total = func.count().over().label("total_count")
query = self.db.query(self.model, total).filter(...)
results = query.offset(offset).limit(limit).all()
# total_count esta en cada fila, tomar de la primera
```

**Nota:** Esta optimizacion es de menor prioridad. La doble query es aceptable para tablas pequenas/medianas.

---

## 3. Seguridad - Hardening

### 3.1 CRITICO: Defaults inseguros en configuracion

**Archivo:** `app/core/config.py`

```python
# ACTUAL - defaults peligrosos
DEBUG: bool = True
ALLOWED_ORIGINS: list[str] = ["*"]
ALLOWED_HOSTS: list[str] = ["*"]

# CORRECCION - defaults seguros
DEBUG: bool = False
ALLOWED_ORIGINS: list[str] = []
ALLOWED_HOSTS: list[str] = []

# Agregar validadores
@field_validator("ALLOWED_ORIGINS")
@classmethod
def validate_origins(cls, v: list[str]) -> list[str]:
    if "*" in v and len(v) > 1:
        raise ValueError("ALLOWED_ORIGINS cannot mix '*' with specific origins")
    return v
```

---

### 3.2 CRITICO: `.env` con secretos en el repositorio

**Archivo:** `.env`
**Problema:** El archivo `.env` contiene `SECRET_KEY` y credenciales de base de datos reales y esta tracked en git.

**Acciones:**
1. Agregar `.env` a `.gitignore`
2. Remover `.env` del tracking de git: `git rm --cached .env`
3. Rotar el `SECRET_KEY` y password de base de datos en el servidor
4. Asegurarse que `.env.example` no tenga valores reales (ya esta correcto)

---

### 3.3 ALTO: Agregar security headers middleware

**Archivo:** `app/main.py`
**Problema:** No hay headers de seguridad HTTP.

**Implementacion:** Crear middleware personalizado:

```python
# app/api/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
```

Y registrarlo en `app/main.py`.

---

### 3.4 ALTO: Implementar rate limiting

**Archivo:** `app/api/middleware/rate_limiter.py` (actualmente vacio)

**Implementacion:** Usar `slowapi`:

```python
# app/api/middleware/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Y decorar endpoints criticos:

```python
# Ejemplo en auth routes
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...

# Ejemplo en POST endpoints
@router.post("/")
@limiter.limit("30/minute")
async def create_post(request: Request, ...):
    ...
```

**Dependencia a agregar:** `slowapi` en `requirements.txt`.

---

### 3.5 MEDIO: Validacion de config en startup

**Archivo:** `app/main.py` (dentro del lifespan)

**Implementacion:** Validar que la configuracion sea segura al iniciar:

```python
# En lifespan, despues de la conexion a DB
if settings.DEBUG:
    logger.warning("DEBUG mode is ON - do not use in production")
if settings.ALLOWED_ORIGINS == ["*"]:
    logger.warning("CORS allows all origins - not recommended for production")
if settings.ALLOWED_HOSTS == ["*"]:
    logger.warning("TrustedHost allows all hosts - not recommended for production")
```

---

### 3.6 MEDIO: Deshabilitar docs en produccion

**Archivo:** `app/main.py`

```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)
```

---

### 3.7 BAJO: Usar `model_config` en vez de `class Config` (Pydantic v2)

**Archivo:** `app/core/config.py:33-34`

```python
# ACTUAL (deprecated en Pydantic v2)
class Config:
    env_file = ".env"

# CORRECCION
model_config = SettingsConfigDict(env_file=".env")
```

---

## 4. Observabilidad - Logging y Monitoring

### 4.1 Implementar configuracion de logging estructurado

**Archivo:** `app/core/logger.py` (actualmente vacio)

```python
# app/core/logger.py
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reducir ruido de librerias terceras
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
```

Llamar `setup_logging()` al inicio del lifespan en `app/main.py`.

---

### 4.2 Health check con verificacion de base de datos

**Archivo:** `app/api/v1/routes/health.py`

```python
# ACTUAL - solo retorna dict estatico
@router.get("/")
async def health_check():
    return {"status": "healthy", ...}

# CORRECCION - verificar DB y retornar schema tipado
from sqlalchemy import text
from app.database.session import get_db

@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=utc_now(),
        service=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
    )
```

Crear `HealthResponse` en `app/schemas/` o directamente en el archivo de health.

---

## 5. Mejoras de Codigo

### 5.1 `uvicorn.run()` con configuracion hardcodeada

**Archivo:** `app/main.py:73-76`

```python
# ACTUAL
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# CORRECCION
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
```

---

### 5.2 Likes model: agregar `foreign_keys` explicito

**Archivo:** `app/models/likes.py`
**Problema:** A diferencia del modelo Follow que tiene `foreign_keys=[...]` en sus relaciones, Likes no lo tiene. Aunque SQLAlchemy puede inferirlos, es mejor ser explicito para consistencia y claridad.

```python
# Agregar foreign_keys a las relaciones
user: Mapped["User"] = relationship(
    "User",
    foreign_keys=[user_uuid],
    back_populates="likes"
)
post: Mapped["Post"] = relationship(
    "Post",
    foreign_keys=[post_uuid],
    back_populates="likes"
)
```

---

### 5.3 Import de `UserRole` desde models en schemas

**Archivo:** `app/schemas/user.py:5`
**Problema:** `from app.models.users import UserRole` - el schema importa directamente del modelo, creando acoplamiento entre capas.

**Solucion:** Mover `UserRole` a un modulo compartido como `app/core/enums.py` o `app/models/enums.py` e importar desde ahi en ambas capas.

```python
# app/core/enums.py (nuevo)
import enum

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"

class PostStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"

class TokenType(enum.Enum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"
    RESET_PASSWORD = "RESET_PASSWORD"
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
```

**Nota:** Este cambio es de baja prioridad. El import actual funciona y no causa circularidad.

---

### 5.4 Base exception: class attributes mutables

**Archivo:** `app/core/exceptions/base.py:38-40`
**Problema menor:** `message`, `code`, y `status_code` son class-level attributes que se sobreescriben en `__init__`. Esto es un patron valido en Python pero puede confundir con la herencia. Las subclases definen estos como class attributes y el `__init__` los usa como defaults.

**Solucion:** No requiere cambio inmediato. El patron funciona correctamente y es intencionado para que las subclases puedan definir defaults sin sobreescribir `__init__`.

---

## 6. Archivos Muertos

### Archivos vacios que deben implementarse o eliminarse

| Archivo | Decision | Razon |
|---------|----------|-------|
| `app/core/logger.py` | **Implementar** | Ver seccion 4.1 |
| `app/core/constans.py` | **Eliminar** | Vacio + typo en nombre. Si se necesitan constantes, crear `app/core/constants.py` |
| `app/utils/validators.py` | **Eliminar** | Vacio. Ya existe `app/utils/validator_utils.py` con la logica |
| `app/utils/decorators.py` | **Eliminar** | Vacio. No se usa en ningun lugar |
| `app/api/middleware/rate_limiter.py` | **Implementar** | Ver seccion 3.4 |

---

## Orden de Ejecucion

### Prioridad 1 - Bugs y seguridad critica
1. Fix `__repr__` de Follow model
2. Fix JWT `exp` a Unix timestamp
3. Fix defaults inseguros en `config.py` (`DEBUG`, CORS, hosts)
4. Remover `.env` del tracking de git
5. Fix `type: ignore` en `user.py`

### Prioridad 2 - Performance critico
6. Eliminar properties N+1 de Post model (likes_count, comments_count)
7. Token repository: filtros SQL en vez de Python
8. Token repository: `count_active_sessions` con SQL COUNT
9. Token repository: cleanup bulk en vez de iterativo

### Prioridad 3 - Seguridad adicional
10. Security headers middleware
11. Rate limiting con slowapi
12. Deshabilitar docs en produccion
13. Validacion de config en startup

### Prioridad 4 - Observabilidad
14. Implementar `logger.py` con configuracion estructurada
15. Health check con DB verification

### Prioridad 5 - Mejoras de codigo
16. Fix `distinct()` en post repository
17. Fix `uvicorn.run` con config dinamica
18. Property `full_name` duplicada
19. `foreign_keys` explicito en Likes model
20. Pydantic v2 `model_config` en Settings
21. Eliminar archivos muertos

### Prioridad 6 - Opcional / futuro
22. Recursive CTE para `get_comment_depth()`
23. Window functions para paginacion
24. Extraer enums a modulo compartido

---

## Resumen de Impacto

| Tipo | Cantidad | Archivos afectados |
|------|----------|-------------------|
| Bug fixes | 5 | 4 archivos |
| Performance | 6 | 3 archivos |
| Seguridad | 7 | 4 archivos + 2 nuevos |
| Observabilidad | 2 | 2 archivos |
| Mejoras codigo | 6 | 6 archivos |
| Limpieza | 3 | 3 archivos eliminados |
| **Total** | **29 items** | **~12 archivos** |
