# Guía de Optimización con Algoritmos - Blog API

## 📊 Análisis de Oportunidades de Optimización

Este documento identifica dónde se pueden aplicar algoritmos avanzados (Binary Search, Recursión, B-Tree, Stack, Divide and Conquer) en el Blog API para mejorar rendimiento y escalabilidad.

---

## 1. 🔍 BINARY SEARCH

### ¿Dónde se puede aplicar?

#### 1.1 **Búsqueda de Posts por Fecha/ID**
**Ubicación**: `app/repositories/post_repository.py`
**Problema Actual**: Las búsquedas por rango de fechas pueden hacer escaneos completos de la tabla.

**Implementación Sugerida**:
```python
def get_posts_by_date_range(
    self,
    start_date: datetime,
    end_date: datetime
) -> List[Post]:
    """
    Buscar posts dentro de un rango de fechas usando índices.
    
    La base de datos usará un índice B-Tree en la columna created_at
    para hacer binary search internamente.
    """
    query = self.db.query(self.model).filter(
        self.model.created_at >= start_date,
        self.model.created_at <= end_date
    ).order_by(self.model.created_at)
    return query.all()
```

**Beneficio**: ⚡ O(log n) en lugar de O(n)

---

#### 1.2 **Búsqueda de Usuarios por ID (Ya Optimizado)**
**Ubicación**: `app/repositories/base_repository.py` - `get_by_uuid()`

```python
def get_by_uuid(self, uuid: UUID, include_deleted: bool = False):
    """
    La búsqueda por UUID es O(log n) gracias a los índices de BD.
    ✓ Ya está optimizado
    """
    query = self.db.query(self.model).filter(self.model.uuid == uuid)
    return query.first()
```

**Status**: ✅ Optimizado

---

#### 1.3 **Búsqueda de Categorías Ordenadas**
**Ubicación**: `app/repositories/category_repository.py` - `get_popular_categories()`

**Mejora Sugerida**:
```python
def get_popular_categories_optimized(
    self,
    limit: int = 10,
    include_deleted: bool = False
) -> List[Category]:
    """
    Optimizar agregaciones con índices compuestos.
    Crear índice: (deleted_at DESC, post_count DESC)
    """
    query = self.db.query(self.model).filter(
        self.model.post_count > 0  # Asume campo desnormalizado
    ).order_by(self.model.post_count.desc()).limit(limit)
    
    return query.all()  # O(log n + k) donde k=limit
```

**Beneficio**: Reduce queries costosas con agregaciones.

---

## 2. 🔄 RECURSION

### ¿Dónde se puede aplicar?

#### 2.1 **Estructura de Comentarios Anidados** ⭐ Principal
**Ubicación**: `app/models/comments.py`, `app/repositories/comment_repository.py`

**Problema**: Los comentarios pueden tener respuestas anidadas (replies).

**Implementación Sugerida**:
```python
# app/repositories/comment_repository.py

from typing import List, Dict

def get_comment_tree(
    self,
    post_uuid: UUID,
    parent_comment_uuid: Optional[UUID] = None,
    max_depth: int = 10
) -> Dict:
    """
    Construir árbol de comentarios de forma recursiva.
    
    Estructura esperada:
    {
        "comment": Comment,
        "replies": [
            {
                "comment": Comment,
                "replies": [...]
            }
        ]
    }
    """
    if max_depth == 0:
        return None
    
    # Obtener comentarios raíz
    query = self.db.query(Comment).filter(
        Comment.post_uuid == post_uuid,
        Comment.parent_comment_uuid == parent_comment_uuid
    )
    
    comments = query.all()
    
    result = []
    for comment in comments:
        comment_tree = {
            "comment": comment,
            "replies": self.get_comment_tree(
                post_uuid=post_uuid,
                parent_comment_uuid=comment.uuid,
                max_depth=max_depth - 1
            ) or []
        }
        result.append(comment_tree)
    
    return result

def get_all_comment_descendants(
    self,
    comment_uuid: UUID
) -> List[Comment]:
    """
    Obtener todos los comentarios descendientes (recursivo).
    Útil para borrar un comentario y todas sus respuestas.
    """
    # Obtener respuestas directas
    direct_replies = self.db.query(Comment).filter(
        Comment.parent_comment_uuid == comment_uuid
    ).all()
    
    all_descendants = list(direct_replies)
    
    # Recursivamente obtener descendientes de cada respuesta
    for reply in direct_replies:
        descendants = self.get_all_comment_descendants(reply.uuid)
        all_descendants.extend(descendants)
    
    return all_descendants
```

**Beneficio**: 
- ✅ Estructura más legible y mantenible
- ✅ Fácil implementación de limitadores de profundidad
- ⚠️ Cuidado: Usar límites de profundidad para evitar stack overflow

**Optimización**: Usar **memoization** para evitar queries duplicadas:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _get_cached_comment(comment_uuid: UUID):
    return self.db.query(Comment).filter(
        Comment.uuid == comment_uuid
    ).first()
```

---

#### 2.2 **Jerarquía de Categorías (Si existen subcategorías)**
**Ubicación**: `app/models/categories.py`

**Implementación Sugerida**:
```python
def get_category_hierarchy(
    self,
    parent_category_uuid: Optional[UUID] = None
) -> Dict:
    """
    Si hay categorías anidadas, construir jerarquía recursiva.
    
    Asume:
    - Category tiene campo 'parent_category_uuid'
    - O relación many-to-one consigo misma
    """
    categories = self.db.query(Category).filter(
        Category.parent_category_uuid == parent_category_uuid,
        Category.deleted_at.is_(None)
    ).all()
    
    result = []
    for category in categories:
        hierarchy = {
            "category": category,
            "subcategories": self.get_category_hierarchy(category.uuid)
        }
        result.append(hierarchy)
    
    return result
```

---

## 3. 🌳 B-TREE

### ¿Dónde se puede aplicar?

#### 3.1 **Indexación de Base de Datos** ✅ Ya Existe
**Ubicación**: Todas las tablas con modelos SQLAlchemy

**Status Actual**: SQLAlchemy y PostgreSQL/MySQL utilizan B-Trees por defecto.

**Recomendación - Crear Índices Compuestos en `alembic/`**:
```python
# En una migración de Alembic

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Índice para búsquedas de posts por autor y fecha
    op.create_index(
        'idx_post_author_date',
        'post',
        ['author_uuid', 'created_at'],
        unique=False
    )
    
    # Índice para búsquedas de posts por estado
    op.create_index(
        'idx_post_status',
        'post',
        ['status', 'created_at'],
        unique=False
    )
    
    # Índice para búsquedas de categorías
    op.create_index(
        'idx_category_name',
        'category',
        ['name'],
        unique=True
    )
    
    # Índice para comentarios por post
    op.create_index(
        'idx_comment_post_date',
        'comment',
        ['post_uuid', 'created_at'],
        unique=False
    )
```

**Beneficio**: ⚡ Reduce tiempo de búsqueda de O(n) a O(log n)

#### 3.2 **Campos Hash para Búsquedas Rápidas**
```python
# app/models/users.py
from sqlalchemy import Index

class User(Base):
    __tablename__ = "user"
    
    uuid = Column(UUID, primary_key=True)
    email = Column(String, unique=True, index=True)  # Índice simple
    username = Column(String, unique=True, index=True)
    
    # Índice compuesto para búsquedas frecuentes
    __table_args__ = (
        Index('idx_user_email_status', 'email', 'status'),
        Index('idx_user_created_at', 'created_at', 'deleted_at'),
    )
```

---

## 4. 📚 STACK (PILA)

### ¿Dónde se puede aplicar?

#### 4.1 **Validación en Cadena (Pipeline)**
**Ubicación**: `app/api/middleware/` y `app/utils/validators.py`

**Implementación Sugerida**:
```python
# app/utils/validation_stack.py

from typing import Any, Callable, List

class ValidationStack:
    """
    Usar stack para ejecutar validaciones en orden.
    Last-In-First-Out (LIFO) - cada validación procesa el resultado anterior.
    """
    
    def __init__(self):
        self.validators: List[Callable] = []
    
    def push(self, validator: Callable) -> 'ValidationStack':
        """Añadir validador a la pila."""
        self.validators.append(validator)
        return self
    
    def validate(self, data: Any) -> tuple[bool, Any, str]:
        """
        Ejecutar todas las validaciones en orden.
        """
        result = data
        
        # Ejecutar en orden LIFO (al revés del orden de push)
        for validator in reversed(self.validators):
            is_valid, result, error = validator(result)
            if not is_valid:
                return False, result, error
        
        return True, result, ""

# Uso en rutas
def validate_post_creation(data: dict):
    """
    Ejemplo: Validar creación de post
    """
    stack = ValidationStack()
    
    stack.push(validate_title_not_empty) \
         .push(validate_title_length) \
         .push(validate_content_not_empty) \
         .push(validate_content_length) \
         .push(validate_categories_exist) \
         .push(sanitize_html_content)
    
    is_valid, cleaned_data, error = stack.validate(data)
    
    if not is_valid:
        raise ValidationException(error)
    
    return cleaned_data

# Validadores individuales
def validate_title_not_empty(data: dict) -> tuple[bool, dict, str]:
    if not data.get('title', '').strip():
        return False, data, "Title cannot be empty"
    return True, data, ""

def validate_title_length(data: dict) -> tuple[bool, dict, str]:
    if len(data['title']) > 200:
        return False, data, "Title exceeds 200 characters"
    return True, data, ""
```

**Beneficio**: 
- ✅ Orden claro de validaciones
- ✅ Fácil de testear cada validador
- ✅ Reutilizable en diferentes contextos

---

#### 4.2 **DFS (Depth-First Search) con Stack para Recorrido de Comentarios**
```python
# app/repositories/comment_repository.py

def get_all_comments_iterative(
    self,
    post_uuid: UUID
) -> List[Comment]:
    """
    Obtener todos los comentarios usando stack (iterativo).
    Alternativa a la recursividad para evitar stack overflow.
    
    Usar stack en lugar de recursión cuando hay muchos comentarios anidados.
    """
    stack = []
    comments = []
    
    # Obtener comentarios raíz
    root_comments = self.db.query(Comment).filter(
        Comment.post_uuid == post_uuid,
        Comment.parent_comment_uuid.is_(None)
    ).all()
    
    # Inicializar stack con comentarios raíz
    stack.extend(root_comments)
    
    # Procesar hasta que el stack esté vacío
    while stack:
        current_comment = stack.pop()  # LIFO
        comments.append(current_comment)
        
        # Obtener respuestas del comentario actual
        replies = self.db.query(Comment).filter(
            Comment.parent_comment_uuid == current_comment.uuid
        ).all()
        
        # Añadir respuestas al stack
        stack.extend(replies)
    
    return comments
```

**Beneficio**: ⚡ Mejor que recursión para estructuras profundas (evita stack overflow)

---

## 5. ⚔️ DIVIDE AND CONQUER

### ¿Dónde se puede aplicar?

#### 5.1 **Búsqueda Compleja Multi-Campo**
**Ubicación**: `app/repositories/base_repository.py` - `filter_by_multi()`

**Implementación Sugerida**:
```python
# app/repositories/base_repository.py

from typing import List, Dict, Any

def search_posts_advanced(
    self,
    query_params: Dict[str, Any]
) -> List[Post]:
    """
    Divide and Conquer: Dividir búsqueda en múltiples criterios.
    Conquistar: Combinar resultados.
    
    Ejemplo: Buscar posts que cumplan TODAS las condiciones:
    - Autor específico
    - Rango de fechas
    - Estado publicado
    - Categoría específica
    - Contienen cierta palabra clave
    """
    
    # DIVIDE: Separar criterios
    author_uuid = query_params.get('author_uuid')
    start_date = query_params.get('start_date')
    end_date = query_params.get('end_date')
    status = query_params.get('status', PostStatus.PUBLISHED)
    category_uuid = query_params.get('category_uuid')
    search_term = query_params.get('search_term')
    
    # CONQUER: Construir query por partes
    query = self.db.query(Post)
    
    # Aplicar cada filtro de forma independiente
    if author_uuid:
        query = query.filter(Post.author_uuid == author_uuid)
    
    if start_date and end_date:
        query = query.filter(
            Post.created_at.between(start_date, end_date)
        )
    
    if status:
        query = query.filter(Post.status == status)
    
    if category_uuid:
        query = query.join(Post.categories).filter(
            Category.uuid == category_uuid
        )
    
    if search_term:
        query = query.filter(
            or_(
                Post.title.ilike(f"%{search_term}%"),
                Post.content.ilike(f"%{search_term}%")
            )
        )
    
    return query.all()
```

---

#### 5.2 **Procesamiento de Datos en Lotes (Batch Processing)**
**Ubicación**: `app/services/`, procesamiento de múltiples items

**Implementación Sugerida**:
```python
# app/services/base_service.py

from typing import List, Callable, TypeVar

T = TypeVar('T')
R = TypeVar('R')

def process_in_batches(
    items: List[T],
    batch_size: int = 100,
    process_func: Callable[[List[T]], List[R]] = None
) -> List[R]:
    """
    Divide and Conquer para procesamiento de grandes listas.
    
    Divide: Partir items en lotes
    Conquer: Procesar cada lote
    Combine: Unir resultados
    """
    results = []
    
    # DIVIDE: Crear lotes
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # CONQUER: Procesar lote
        batch_results = process_func(batch)
        
        # COMBINE: Acumular resultados
        results.extend(batch_results)
    
    return results

# Uso: Procesar múltiples comentarios para indexación
def index_comments_batch(comment_uuids: List[UUID]):
    """
    Indexar comentarios en lotes para búsqueda full-text.
    """
    def index_batch(batch: List[UUID]):
        comments = db.query(Comment).filter(
            Comment.uuid.in_(batch)
        ).all()
        
        # Indexar cada comentario (enviar a Elasticsearch, etc.)
        for comment in comments:
            search_engine.index(comment)
        
        return comments
    
    return process_in_batches(comment_uuids, 100, index_batch)
```

**Beneficio**: ✅ Procesamiento eficiente de grandes volúmenes

---

#### 5.3 **Merge Sort para Ordenamiento de Comentarios**
```python
# app/utils/sorting.py

def merge_sort_comments(comments: List[Comment]) -> List[Comment]:
    """
    Divide and Conquer: Merge Sort para ordenar comentarios.
    
    Útil cuando necesitas ordenamientos complejos sin cargar BD.
    
    Complejidad: O(n log n)
    """
    
    if len(comments) <= 1:
        return comments
    
    # DIVIDE: Partir en mitades
    mid = len(comments) // 2
    left = comments[:mid]
    right = comments[mid:]
    
    # CONQUER: Ordenar recursivamente
    left_sorted = merge_sort_comments(left)
    right_sorted = merge_sort_comments(right)
    
    # COMBINE: Mezclar
    return merge(left_sorted, right_sorted)

def merge(left: List[Comment], right: List[Comment]) -> List[Comment]:
    """Mezclar dos listas ordenadas de comentarios."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        # Comparar por fecha de creación
        if left[i].created_at <= right[j].created_at:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Añadir elementos restantes
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result
```

---

## 📈 Resumen de Mejoras de Rendimiento

| Algoritmo | Ubicación | Antes | Después | Beneficio |
|-----------|-----------|-------|---------|-----------|
| **Binary Search** | Repositorios (búsquedas) | O(n) | O(log n) | ⚡⚡⚡ Crítico |
| **Recursion** | Comments anidados | Código plano | Árbol limpio | ✅ Legibilidad |
| **B-Tree** | Índices BD | Sin índices | Con índices | ⚡⚡⚡ Crítico |
| **Stack** | Validaciones | Interdependencias | Pipeline claro | ✅ Mantenibilidad |
| **Divide & Conquer** | Búsquedas complejas | Múltiples queries | Query única | ⚡⚡ Alto impacto |

---

## 🎯 Prioridad de Implementación

### 1. **ALTA PRIORIDAD** (Máximo impacto inmediato)
- ✅ Crear índices B-Tree en BD (fácil, impacto inmediato)
- ✅ Optimizar búsquedas con Divide & Conquer

### 2. **MEDIA PRIORIDAD** (Buena relación effort/benefit)
- ⏳ Implementar recursión para comentarios anidados
- ⏳ Stack para validación en cadena

### 3. **BAJA PRIORIDAD** (Mejoras futuras)
- 📅 Procesamiento en lotes (cuando crezca volumen)
- 📅 Merge Sort (solo si necesitas ordenamientos complejos)

---

## 📝 Ejemplo de Implementación Completa

```python
# app/repositories/post_repository_optimized.py

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class OptimizedPostRepository(PostRepository):
    """
    Versión optimizada del repositorio de posts
    con Binary Search, Divide & Conquer, y Stack.
    """
    
    # 1. BINARY SEARCH - Búsqueda por fecha
    def search_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        pagination: Optional[PaginationParams] = None
    ) -> List[Post]:
        """Binary Search usando índice de BD."""
        query = self.db.query(Post).filter(
            Post.created_at.between(start_date, end_date),
            Post.status == PostStatus.PUBLISHED
        ).order_by(Post.created_at.desc())
        
        return paginate(query, pagination)
    
    # 2. DIVIDE & CONQUER - Búsqueda avanzada
    def search_advanced(
        self,
        filters: Dict[str, Any]
    ) -> List[Post]:
        """Divide and Conquer: dividir criterios, conquista cada uno."""
        query = self.db.query(Post)
        
        # Aplicar cada filtro independientemente
        for field, value in filters.items():
            if field == 'author_uuid':
                query = query.filter(Post.author_uuid == value)
            elif field == 'category_uuid':
                query = query.join(Post.categories).filter(
                    Category.uuid == value
                )
            elif field == 'search_term':
                query = query.filter(
                    Post.title.ilike(f"%{value}%") |
                    Post.content.ilike(f"%{value}%")
                )
        
        return query.all()
    
    # 3. RECURSION - Obtener posts relacionados
    def get_related_posts(
        self,
        post_uuid: UUID,
        max_depth: int = 2
    ) -> List[Post]:
        """Obtener posts relacionados recursivamente por categoría."""
        if max_depth == 0:
            return []
        
        original_post = self.get_by_uuid(post_uuid)
        if not original_post:
            return []
        
        # Obtener posts de las mismas categorías
        related_posts = self.db.query(Post).filter(
            Post.uuid != post_uuid,
            Post.categories.any(
                Category.uuid.in_(
                    [cat.uuid for cat in original_post.categories]
                )
            )
        ).all()
        
        return related_posts
```

---

## 🚀 Próximos Pasos

1. **Fase 1**: Crear índices B-Tree en migración Alembic
2. **Fase 2**: Implementar búsquedas optimizadas con Divide & Conquer
3. **Fase 3**: Agregar recursión para comentarios anidados
4. **Fase 4**: Stack para validaciones en cadena
5. **Fase 5**: Benchmarking y monitoreo de performance

---

## 📚 Referencias

- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [SQLAlchemy Query Guide](https://docs.sqlalchemy.org/en/14/orm/query.html)
- [Algoritmos: Binary Search](https://en.wikipedia.org/wiki/Binary_search_algorithm)
- [Divide and Conquer Algorithms](https://en.wikipedia.org/wiki/Divide_and_conquer_algorithms)

---

**Fecha**: 2026-02-09
**Autor**: Análisis de Optimización de Blog API
**Status**: ✅ Listo para Implementación
