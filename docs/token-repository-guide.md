# Token Repository - Guía de Implementación

Guía completa para implementar el `TokenRepository` en el proyecto Blog API, incluyendo métodos esenciales, casos de uso y mejores prácticas de seguridad.

---

## Tabla de Contenidos

1. [¿Para qué sirve el Token Repository?](#para-qué-sirve-el-token-repository)
2. [Modelo Token](#modelo-token)
3. [Métodos Esenciales](#métodos-esenciales)
4. [Implementación Completa](#implementación-completa)
5. [Casos de Uso](#casos-de-uso)
6. [Seguridad y Mejores Prácticas](#seguridad-y-mejores-prácticas)

---

## ¿Para qué sirve el Token Repository?

El **Token Repository** gestiona los tokens de autenticación (JWT) almacenados en la base de datos. Sus responsabilidades principales son:

### Responsabilidades

1. **Almacenar tokens activos** - Guardar JWT tokens cuando los usuarios hacen login
2. **Validar tokens** - Verificar si un token es válido y no ha expirado
3. **Revocar tokens** - Invalidar tokens en logout o cuando se comprometen
4. **Limpiar tokens expirados** - Mantener la base de datos limpia
5. **Gestionar refresh tokens** - Para renovar tokens sin re-autenticación

### Beneficios de almacenar tokens en BD

- ✅ **Revocación instantánea** - Puedes invalidar tokens inmediatamente (logout forzado)
- ✅ **Auditoría** - Registrar cuándo y desde dónde se usan los tokens
- ✅ **Seguridad** - Detectar tokens robados o uso anormal
- ✅ **Control de sesiones** - Limitar número de dispositivos conectados simultáneamente

---

## Modelo Token

Basándome en `docs/design_system.pdf` y las relaciones del proyecto:

```python
# app/models/tokens.py
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class TokenType(enum.Enum):
    """Types of tokens."""
    ACCESS = "ACCESS"      # Short-lived JWT for API access
    REFRESH = "REFRESH"    # Long-lived token to get new access tokens


class Token(BaseModel):
    """
    Tokens table for storing JWT tokens.

    This allows token revocation, session management, and security auditing.
    """

    __tablename__ = "tokens"

    # Token data
    token = Column(String(500), unique=True, index=True, nullable=False)
    type = Column(Enum(TokenType), default=TokenType.ACCESS, nullable=False)

    # Relationships
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    user = relationship("User", back_populates="tokens")

    # Token lifecycle
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata (optional pero útil)
    ip_address = Column(String(45), nullable=True)  # IPv6 = max 45 chars
    user_agent = Column(String(255), nullable=True)

    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        return not self.revoked and not self.is_expired() and not self.deleted_at
```

---

## Métodos Esenciales

### Métodos CRUD Básicos (heredados de BaseRepository)

```python
# Ya disponibles sin implementar:
create(obj_in)           # Crear nuevo token
get(uuid)                # Obtener token por UUID
update(uuid, obj_in)     # Actualizar token
delete(uuid)             # Soft delete token
```

### Métodos Específicos que DEBES implementar

| Método | Descripción | Cuándo usarlo |
|--------|-------------|---------------|
| `get_by_token()` | Buscar token por string | Validar en cada request |
| `get_user_tokens()` | Tokens de un usuario | Ver sesiones activas |
| `get_valid_token()` | Token válido (no expirado/revocado) | Middleware de autenticación |
| `revoke_token()` | Marcar token como revocado | Logout |
| `revoke_user_tokens()` | Revocar todos los tokens de un usuario | Logout de todos los dispositivos |
| `revoke_all_except()` | Revocar todos menos uno | "Cerrar otras sesiones" |
| `cleanup_expired()` | Eliminar tokens expirados | Tarea programada (cron) |
| `count_active_sessions()` | Contar sesiones activas | Límite de dispositivos |

---

## Implementación Completa

```python
# app/repositories/token_repository.py
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models import Token, TokenType
from app.repositories.base_repository import BaseRepository


class TokenRepository(BaseRepository[Token]):
    """
    Repository for Token model operations.

    Manages JWT tokens stored in database for revocation,
    session management, and security auditing.
    """

    def __init__(self, db: Session):
        """Initialize TokenRepository with Token model."""
        super().__init__(Token, db)

    # ====================================================================
    # TOKEN LOOKUP METHODS
    # ====================================================================

    def get_by_token(
        self,
        token: str,
        include_deleted: bool = False
    ) -> Optional[Token]:
        """
        Get a token by its string value.

        Args:
            token: The token string (JWT)
            include_deleted: If True, includes soft-deleted tokens

        Returns:
            Token instance if found, None otherwise

        Example:
            token_obj = token_repo.get_by_token("eyJhbGc...")
        """
        query = self.db.query(self.model).filter(
            self.model.token == token
        )

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def get_valid_token(
        self,
        token: str,
        token_type: Optional[TokenType] = None
    ) -> Optional[Token]:
        """
        Get a token only if it's valid (not expired, not revoked).

        This is the main method for authentication middleware.

        Args:
            token: The token string
            token_type: Optional filter by token type

        Returns:
            Token instance if valid, None otherwise

        Example:
            # In authentication middleware
            token_obj = token_repo.get_valid_token(token_string)
            if not token_obj:
                raise HTTPException(401, "Invalid or expired token")
        """
        query = self.db.query(self.model).filter(
            and_(
                self.model.token == token,
                self.model.revoked.is_(False),
                self.model.deleted_at.is_(None),
                self.model.expires_at > datetime.now(timezone.utc)
            )
        )

        if token_type:
            query = query.filter(self.model.type == token_type)

        return query.first()

    # ====================================================================
    # USER TOKEN MANAGEMENT
    # ====================================================================

    def get_user_tokens(
        self,
        user_uuid: UUID,
        token_type: Optional[TokenType] = None,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> List[Token]:
        """
        Get all tokens for a specific user.

        Args:
            user_uuid: The user's UUID
            token_type: Optional filter by token type
            include_revoked: If True, includes revoked tokens
            include_expired: If True, includes expired tokens

        Returns:
            List of token instances

        Example:
            # Get all active access tokens for a user
            active_tokens = token_repo.get_user_tokens(
                user_uuid=user.uuid,
                token_type=TokenType.ACCESS
            )
        """
        filters = {"user_uuid": user_uuid}

        if token_type:
            filters["type"] = token_type

        tokens = self.filter_by(
            include_deleted=False,
            **filters
        )

        # Filter by revoked/expired status
        result = []
        for token in tokens:
            if not include_revoked and token.revoked:
                continue
            if not include_expired and token.is_expired():
                continue
            result.append(token)

        return result

    def count_active_sessions(
        self,
        user_uuid: UUID,
        token_type: TokenType = TokenType.ACCESS
    ) -> int:
        """
        Count active (valid) sessions for a user.

        Useful for enforcing maximum concurrent sessions.

        Args:
            user_uuid: The user's UUID
            token_type: Token type to count (default: ACCESS)

        Returns:
            Number of active sessions

        Example:
            # Enforce max 5 devices
            if token_repo.count_active_sessions(user.uuid) >= 5:
                raise HTTPException(429, "Too many active sessions")
        """
        tokens = self.get_user_tokens(
            user_uuid=user_uuid,
            token_type=token_type,
            include_revoked=False,
            include_expired=False
        )
        return len(tokens)

    # ====================================================================
    # TOKEN REVOCATION
    # ====================================================================

    def revoke_token(
        self,
        token: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Revoke a specific token (logout from one device).

        Args:
            token: The token string to revoke
            hard_delete: If True, permanently delete. Default: mark as revoked

        Returns:
            True if revoked, False if not found

        Example:
            # In logout endpoint
            if token_repo.revoke_token(token_string):
                return {"message": "Logged out successfully"}
        """
        token_obj = self.get_by_token(token)

        if not token_obj:
            return False

        if hard_delete:
            return self.delete(token_obj.uuid, hard_delete=True)
        else:
            # Mark as revoked
            self.update(token_obj.uuid, {
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc)
            })
            return True

    def revoke_user_tokens(
        self,
        user_uuid: UUID,
        token_type: Optional[TokenType] = None,
        except_token: Optional[str] = None
    ) -> int:
        """
        Revoke all tokens for a user (logout from all devices).

        Args:
            user_uuid: The user's UUID
            token_type: Optional filter by token type
            except_token: Optional token to NOT revoke (current session)

        Returns:
            Number of tokens revoked

        Example:
            # Logout from all devices
            count = token_repo.revoke_user_tokens(user.uuid)
            return {"message": f"Logged out from {count} devices"}

            # Logout from all OTHER devices (keep current)
            count = token_repo.revoke_user_tokens(
                user.uuid,
                except_token=current_token
            )
        """
        tokens = self.get_user_tokens(
            user_uuid=user_uuid,
            token_type=token_type,
            include_revoked=False
        )

        count = 0
        now = datetime.now(timezone.utc)

        for token in tokens:
            # Skip the exception token (current session)
            if except_token and token.token == except_token:
                continue

            self.update(token.uuid, {
                "revoked": True,
                "revoked_at": now
            })
            count += 1

        return count

    def revoke_all_except(
        self,
        user_uuid: UUID,
        keep_token: str
    ) -> int:
        """
        Revoke all user tokens except one (close other sessions).

        Alias for revoke_user_tokens with except_token parameter.

        Args:
            user_uuid: The user's UUID
            keep_token: Token to keep active (current session)

        Returns:
            Number of tokens revoked

        Example:
            # "Close other sessions" button
            count = token_repo.revoke_all_except(
                user.uuid,
                keep_token=current_token
            )
        """
        return self.revoke_user_tokens(
            user_uuid=user_uuid,
            except_token=keep_token
        )

    # ====================================================================
    # CLEANUP AND MAINTENANCE
    # ====================================================================

    def cleanup_expired(
        self,
        hard_delete: bool = True,
        older_than_days: int = 7
    ) -> int:
        """
        Delete or soft-delete expired tokens.

        This should be run periodically (cron job) to keep DB clean.

        Args:
            hard_delete: If True, permanently delete. Default: True
            older_than_days: Only delete tokens expired for X days

        Returns:
            Number of tokens deleted

        Example:
            # In a scheduled task (Celery, cron, etc.)
            deleted = token_repo.cleanup_expired()
            logger.info(f"Cleaned up {deleted} expired tokens")
        """
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        # Find expired tokens
        expired_tokens = self.db.query(self.model).filter(
            and_(
                self.model.expires_at < cutoff_date,
                self.model.deleted_at.is_(None)
            )
        ).all()

        count = 0
        for token in expired_tokens:
            if self.delete(token.uuid, hard_delete=hard_delete):
                count += 1

        return count

    def cleanup_revoked(
        self,
        hard_delete: bool = True,
        older_than_days: int = 30
    ) -> int:
        """
        Delete revoked tokens older than X days.

        Args:
            hard_delete: If True, permanently delete
            older_than_days: Only delete tokens revoked X days ago

        Returns:
            Number of tokens deleted

        Example:
            # Monthly cleanup of old revoked tokens
            deleted = token_repo.cleanup_revoked(older_than_days=30)
        """
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        revoked_tokens = self.db.query(self.model).filter(
            and_(
                self.model.revoked.is_(True),
                self.model.revoked_at < cutoff_date,
                self.model.deleted_at.is_(None)
            )
        ).all()

        count = 0
        for token in revoked_tokens:
            if self.delete(token.uuid, hard_delete=hard_delete):
                count += 1

        return count

    # ====================================================================
    # SECURITY AND AUDITING
    # ====================================================================

    def get_suspicious_tokens(
        self,
        user_uuid: UUID,
        current_ip: str
    ) -> List[Token]:
        """
        Find tokens used from different IP addresses.

        Useful for detecting stolen tokens.

        Args:
            user_uuid: The user's UUID
            current_ip: The current IP address

        Returns:
            List of tokens used from different IPs

        Example:
            # In authentication middleware
            suspicious = token_repo.get_suspicious_tokens(user.uuid, request_ip)
            if suspicious:
                # Send alert email
                # Auto-revoke suspicious tokens
                for token in suspicious:
                    token_repo.revoke_token(token.token)
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.user_uuid == user_uuid,
                self.model.revoked.is_(False),
                self.model.deleted_at.is_(None),
                self.model.ip_address != current_ip,
                self.model.ip_address.isnot(None)
            )
        ).all()

    def token_exists(self, token: str) -> bool:
        """
        Check if a token exists in database.

        Args:
            token: The token string

        Returns:
            True if exists, False otherwise

        Example:
            if token_repo.token_exists(token_string):
                raise HTTPException(409, "Token already exists")
        """
        return self.db.query(self.model.uuid).filter(
            self.model.token == token
        ).filter(self.model.deleted_at.is_(None)).first() is not None
```

---

## Casos de Uso

### 1. Login - Crear Token

```python
# app/services/auth_service.py

def login(self, credentials: LoginRequest) -> TokenResponse:
    # 1. Validar credenciales
    user = self.user_repo.get_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")

    # 2. Crear access token
    access_token = create_access_token(user.uuid)

    # 3. Guardar en BD
    token_obj = self.token_repo.create({
        "token": access_token,
        "type": TokenType.ACCESS,
        "user_uuid": user.uuid,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    })

    return TokenResponse(access_token=access_token)
```

### 2. Logout - Revocar Token

```python
# app/services/auth_service.py

def logout(self, token: str) -> MessageResponse:
    # Revocar el token actual
    if not self.token_repo.revoke_token(token):
        raise HTTPException(404, "Token not found")

    return MessageResponse(message="Logged out successfully")
```

### 3. Logout de Todos los Dispositivos

```python
def logout_all_devices(self, user_uuid: UUID) -> MessageResponse:
    count = self.token_repo.revoke_user_tokens(user_uuid)
    return MessageResponse(message=f"Logged out from {count} devices")
```

### 4. Cerrar Otras Sesiones (mantener la actual)

```python
def logout_other_sessions(self, user_uuid: UUID, current_token: str):
    count = self.token_repo.revoke_all_except(
        user_uuid=user_uuid,
        keep_token=current_token
    )
    return MessageResponse(
        message=f"Closed {count} other sessions. Current session remains active."
    )
```

### 5. Middleware de Autenticación

```python
# app/api/dependencies.py

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    token_repo = TokenRepository(db)

    # Verificar que el token esté en BD y sea válido
    token_obj = token_repo.get_valid_token(token)

    if not token_obj:
        raise HTTPException(401, "Invalid or expired token")

    # Obtener usuario
    user_repo = UserRepository(db)
    user = user_repo.get(token_obj.user_uuid)

    if not user:
        raise HTTPException(401, "User not found")

    return user
```

### 6. Tarea Programada - Limpiar Tokens Expirados

```python
# app/tasks/cleanup_tasks.py
from celery import Celery

@celery.task
def cleanup_expired_tokens():
    """Run daily to clean up expired tokens."""
    from app.database.connection import SessionLocal
    from app.repositories.token_repository import TokenRepository

    db = SessionLocal()
    try:
        token_repo = TokenRepository(db)

        # Delete tokens expired more than 7 days ago
        deleted = token_repo.cleanup_expired(older_than_days=7)

        print(f"Cleaned up {deleted} expired tokens")
        return deleted
    finally:
        db.close()
```

### 7. Limitar Sesiones Concurrentes

```python
def login(self, credentials: LoginRequest) -> TokenResponse:
    user = self.authenticate_user(credentials)

    # Limitar a 5 dispositivos máximo
    active_sessions = self.token_repo.count_active_sessions(user.uuid)

    if active_sessions >= 5:
        raise HTTPException(
            429,
            "Maximum number of active sessions reached. "
            "Please logout from another device."
        )

    # Crear nuevo token...
```

### 8. Detección de Tokens Sospechosos

```python
async def check_suspicious_activity(
    user: User,
    token: str,
    request: Request,
    db: Session
):
    token_repo = TokenRepository(db)

    # Buscar tokens usados desde otras IPs
    suspicious = token_repo.get_suspicious_tokens(
        user_uuid=user.uuid,
        current_ip=request.client.host
    )

    if suspicious:
        # Enviar email de alerta
        send_security_alert(user.email, suspicious)

        # Auto-revocar tokens sospechosos
        for suspicious_token in suspicious:
            token_repo.revoke_token(suspicious_token.token)

        # Log para auditoría
        logger.warning(
            f"Suspicious activity detected for user {user.uuid}. "
            f"Revoked {len(suspicious)} tokens."
        )
```

---

## Seguridad y Mejores Prácticas

### 1. **Nunca almacenes el token en texto plano (opcional pero recomendado)**

```python
import hashlib

def hash_token(token: str) -> str:
    """Hash token before storing in database."""
    return hashlib.sha256(token.encode()).hexdigest()

# Al crear token:
self.token_repo.create({
    "token": hash_token(access_token),  # Store hash, not raw token
    ...
})

# Al validar:
token_hash = hash_token(received_token)
token_obj = token_repo.get_by_token(token_hash)
```

### 2. **Establecer Expiración Apropiada**

```python
# Access Token: Corto (1-2 horas)
access_expires = datetime.now(timezone.utc) + timedelta(hours=1)

# Refresh Token: Largo (7-30 días)
refresh_expires = datetime.now(timezone.utc) + timedelta(days=7)
```

### 3. **Limpiar Tokens Regularmente**

```python
# Ejecutar diariamente con cron o Celery
# 0 2 * * * python -m app.tasks.cleanup_tokens

def daily_cleanup():
    token_repo = TokenRepository(db)

    # Delete expired tokens
    token_repo.cleanup_expired(older_than_days=7)

    # Delete old revoked tokens
    token_repo.cleanup_revoked(older_than_days=30)
```

### 4. **Implementar Rate Limiting en Login**

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # Max 5 intentos por minuto
async def login(credentials: LoginRequest):
    ...
```

### 5. **Logging y Auditoría**

```python
import logging

logger = logging.getLogger(__name__)

def create_token(self, user_uuid: UUID, ip: str) -> Token:
    token_obj = self.token_repo.create({...})

    # Log para auditoría
    logger.info(
        f"Token created for user {user_uuid} from IP {ip}",
        extra={
            "user_uuid": str(user_uuid),
            "ip_address": ip,
            "token_uuid": str(token_obj.uuid)
        }
    )

    return token_obj
```

### 6. **Revocar Todos los Tokens al Cambiar Contraseña**

```python
def change_password(self, user_uuid: UUID, new_password: str):
    # 1. Cambiar contraseña
    user_repo.update(user_uuid, {
        "hashed_password": hash_password(new_password)
    })

    # 2. Revocar TODOS los tokens (forzar re-login)
    token_repo.revoke_user_tokens(user_uuid)

    # 3. Enviar email de confirmación
    send_email(user.email, "Password changed. All devices logged out.")
```

### 7. **Índices de Base de Datos**

```sql
-- Mejorar performance de búsquedas frecuentes
CREATE INDEX idx_tokens_token ON tokens(token);
CREATE INDEX idx_tokens_user_uuid ON tokens(user_uuid);
CREATE INDEX idx_tokens_expires_at ON tokens(expires_at);
CREATE INDEX idx_tokens_revoked ON tokens(revoked);

-- Índice compuesto para validación rápida
CREATE INDEX idx_tokens_valid ON tokens(token, revoked, expires_at)
WHERE deleted_at IS NULL;
```

---

## Resumen

### Métodos Mínimos Necesarios

1. ✅ `get_by_token()` - Buscar token
2. ✅ `get_valid_token()` - Validar token (principal)
3. ✅ `get_user_tokens()` - Tokens de usuario
4. ✅ `revoke_token()` - Logout
5. ✅ `revoke_user_tokens()` - Logout all
6. ✅ `cleanup_expired()` - Mantenimiento

### Métodos Opcionales pero Recomendados

7. ⭐ `count_active_sessions()` - Limitar dispositivos
8. ⭐ `revoke_all_except()` - "Cerrar otras sesiones"
9. ⭐ `get_suspicious_tokens()` - Seguridad
10. ⭐ `cleanup_revoked()` - Mantenimiento avanzado

---

## Referencias

- **BaseRepository:** `app/repositories/base_repository.py`
- **Design System:** `docs/design_system.pdf` - Sección de autenticación
- **Authentication Guide:** `docs/authentication-simple-guide.md`
- **Implementation Order:** `docs/implementation-order.md`

---

**Siguiente paso:** Implementa el `TokenRepository` siguiendo esta guía y pruébalo en tus endpoints de autenticación! 🔐
