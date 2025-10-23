# Python & Framework Concepts Explained

A comprehensive guide to understand the key Python, SQLAlchemy, Pydantic, and FastAPI concepts used in this project.

---

## Table of Contents

1. [Python Built-in Functions](#python-built-in-functions)
   - [hasattr()](#hasattr)
   - [getattr()](#getattr)
   - [setattr()](#setattr)
   - [** (Dictionary Unpacking)](#dictionary-unpacking)
   - [Tuple Unpacking](#tuple-unpacking)
   - [@property Decorator](#property-decorator)
2. [Python Type System](#python-type-system)
   - [TypeVar](#typevar)
   - [Generic Types](#generic-types)
3. [SQLAlchemy Concepts](#sqlalchemy-concepts)
   - [engine.dispose()](#enginedispose)
   - [Base.metadata.create_all()](#basemetadatacreate_all)
   - [bind Parameter](#bind-parameter)
   - [self.db.rollback()](#selfdbrollback)
   - [IntegrityError](#integrityerror)
   - [SQLAlchemyError](#sqlalchemyerror)
   - [synchronize_session=False](#synchronize_sessionfalse)
   - [ilike (Case-Insensitive Search)](#ilike-case-insensitive-search)
   - [SQL Wildcards (% and _)](#sql-wildcards--and-_)
   - [relationship()](#relationship)
4. [Pydantic Concepts](#pydantic-concepts)
   - [ConfigDict](#configdict)
   - [Field()](#field)
5. [FastAPI Concepts](#fastapi-concepts)
   - [Query() vs Field()](#query-vs-field)

---

## Python Built-in Functions

### `hasattr()`

**What it does:** Checks if an object has a specific attribute (property or method).

**Syntax:**
```python
hasattr(object, attribute_name)
```

**Returns:** `True` if the attribute exists, `False` otherwise.

**Why we use it:**
- Prevents errors when trying to access attributes that might not exist
- Makes code defensive and robust
- Useful for dynamic attribute access

**Example:**
```python
class User:
    def __init__(self):
        self.name = "John"
        self.email = "john@example.com"
        # Note: No 'age' attribute

user = User()

# Check before accessing
if hasattr(user, 'name'):
    print(user.name)  # ✅ Safe: "John"

if hasattr(user, 'age'):
    print(user.age)  # ✗ Won't execute (age doesn't exist)
else:
    print("User has no age attribute")  # ✅ This prints

# Without hasattr (dangerous):
# print(user.age)  # ❌ AttributeError!
```

**Real usage in our code:**
```python
def update(self, id: UUID, obj_in: Dict[str, Any]):
    db_obj = self.get(id)

    # Update only fields that exist in the model
    for field, value in obj_in.items():
        if hasattr(db_obj, field):  # ← Check if field exists
            setattr(db_obj, field, value)
```

**Analogy:**
Think of `hasattr()` like checking if a person has a specific skill before asking them to do a task.
```
❓ Does John have the skill "programming"?
✅ Yes → Ask John to write code
❌ No → Don't ask John to write code (would fail)
```

---

### `getattr()`

**What it does:** Gets the value of an attribute from an object dynamically.

**Syntax:**
```python
getattr(object, attribute_name, default=None)
```

**Returns:** The value of the attribute, or the default value if not found.

**Why we use it:**
- Access attributes when the name is stored in a variable
- Dynamic attribute access based on runtime data
- Safer than direct attribute access with a default fallback

**Example:**
```python
class User:
    def __init__(self):
        self.name = "John"
        self.email = "john@example.com"

user = User()

# Static access (attribute name known at compile time)
print(user.name)  # "John"

# Dynamic access (attribute name in a variable)
field_name = "email"
print(getattr(user, field_name))  # "john@example.com"

# With default value (safe)
age = getattr(user, 'age', 25)  # Returns 25 (default) since 'age' doesn't exist
print(age)  # 25

# Without default (raises AttributeError if not found)
# getattr(user, 'age')  # ❌ AttributeError!
```

**Real usage in our code:**
```python
def get_multi(self, filters: Dict[str, Any]):
    query = self.db.query(self.model)

    # Build dynamic filters
    for field, value in filters.items():
        if hasattr(self.model, field):
            # Get the model's field object dynamically
            model_field = getattr(self.model, field)
            query = query.filter(model_field == value)

    return query.all()

# Usage:
# filters = {"email": "test@example.com", "is_active": True}
# users = repo.get_multi(filters)
# → WHERE email = 'test@example.com' AND is_active = true
```

**Comparison:**
```python
# Static access (compile time)
user.name  # Fast, direct

# Dynamic access (runtime)
field = "name"
getattr(user, field)  # Flexible, programmatic
```

**Analogy:**
Think of `getattr()` like looking up information in a phonebook:
```
📖 Phonebook = User object
📝 Name in phonebook = Attribute

Static: "I want John's phone number" → Look up "John" directly
Dynamic: Someone tells you "Look up {name}" → Use getattr to find whoever they said
```

---

### `setattr()`

**What it does:** Sets the value of an attribute on an object dynamically.

**Syntax:**
```python
setattr(object, attribute_name, value)
```

**Why we use it:**
- Set attributes when the name is in a variable
- Update multiple attributes in a loop
- Dynamic attribute assignment based on runtime data
- Paired with `getattr()` for flexible data manipulation

**Example:**

```python
class User:
    def __init__(self):
        self.name = "John"
        self.email = "john@example.com"

user = User()

# Static assignment (attribute name known at compile time)
user.name = "Jane"

# Dynamic assignment (attribute name in a variable)
field_name = "email"
new_value = "jane@example.com"
setattr(user, field_name, new_value)
print(user.email)  # "jane@example.com"

# Set multiple attributes dynamically
data = {
    "name": "Alice",
    "email": "alice@example.com",
    "age": 30
}

for field, value in data.items():
    setattr(user, field, value)

print(user.name)   # "Alice"
print(user.email)  # "alice@example.com"
print(user.age)    # 30
```

**Real usage in our code:**

```python
def update(self, id: UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
    """Update an existing record."""
    db_obj = self.get(id)

    if not db_obj:
        return None

    try:
        # Update each field specified in obj_in
        for field, value in obj_in.items():
            if hasattr(db_obj, field):  # ← Check if field exists
                setattr(db_obj, field, value)  # ← Set the value dynamically

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    except SQLAlchemyError as e:
        self.db.rollback()
        raise e

# Usage:
user_repo.update(user_id, {
    "name": "New Name",
    "email": "new@email.com",
    "is_active": False
})
# ↑ Each field is set dynamically using setattr()
```

**The trio: hasattr, getattr, setattr**

```python
class User:
    def __init__(self):
        self.name = "John"
        self.email = "john@example.com"

user = User()
field = "name"

# 1. Check if attribute exists
if hasattr(user, field):  # ← Does user have 'name'?

    # 2. Get the current value
    old_value = getattr(user, field)  # ← Get value of 'name'
    print(f"Old value: {old_value}")  # "Old value: John"

    # 3. Set a new value
    setattr(user, field, "Jane")  # ← Set 'name' to "Jane"

    # 4. Verify the change
    new_value = getattr(user, field)
    print(f"New value: {new_value}")  # "New value: Jane"
```

**Comparison with direct assignment:**

```python
# Static (compile-time known)
user.name = "John"  # Direct, fast

# Dynamic (runtime determined)
field = "name"
setattr(user, field, "John")  # Flexible, programmatic

# Both achieve the same result, but setattr is needed when:
# - Field name comes from user input
# - Updating multiple fields in a loop
# - Field name is calculated or stored in a variable
```

**Advanced example with validation:**

```python
class User:
    def __init__(self):
        self.name = ""
        self.email = ""
        self.age = 0

def update_user(user, updates: Dict[str, Any]):
    """Update user with validation."""

    # Allowed fields (security: prevent setting internal attributes)
    allowed_fields = {"name", "email", "age"}

    for field, value in updates.items():
        # Validate field is allowed
        if field not in allowed_fields:
            print(f"❌ Field '{field}' not allowed")
            continue

        # Check if field exists
        if not hasattr(user, field):
            print(f"❌ Field '{field}' doesn't exist")
            continue

        # Get old value for logging
        old_value = getattr(user, field)

        # Set new value
        setattr(user, field, value)

        print(f"✓ Updated {field}: {old_value} → {value}")

user = User()
update_user(user, {
    "name": "John",
    "email": "john@example.com",
    "age": 30,
    "password": "secret"  # ← Will be rejected (not in allowed_fields)
})
# Output:
# ✓ Updated name:  → John
# ✓ Updated email:  → john@example.com
# ✓ Updated age: 0 → 30
# ❌ Field 'password' not allowed
```

**Common pattern: Bulk attribute updates**

```python
def apply_defaults(obj, defaults: Dict[str, Any]):
    """Apply default values to object attributes."""
    for field, default_value in defaults.items():
        if hasattr(obj, field):
            current_value = getattr(obj, field)
            # Only set if current value is None or empty
            if current_value is None or current_value == "":
                setattr(obj, field, default_value)

user = User()
user.name = "John"  # Already set

apply_defaults(user, {
    "name": "Default Name",  # Won't override (already set)
    "email": "default@email.com",  # Will set (currently empty)
    "age": 18  # Will set (currently 0/empty)
})

print(user.name)   # "John" (not overridden)
print(user.email)  # "default@email.com" (was empty, now set)
```

**Analogy:**

Think of `setattr()` like a universal remote control:
```
📺 TV (Object)
🔘 Buttons (Attributes)

Direct button press: tv.volume = 50
  ↑ You physically press the volume button

Universal remote: setattr(tv, "volume", 50)
  ↑ You tell the remote which button to press
  ↑ Remote presses it for you

Use remote when:
  - Button name comes from user ("Press {button_name}")
  - Pressing multiple buttons in a loop
  - Button is calculated ("Press button #{number}")

setattr() = The universal remote for object attributes
```

**Security note:**

```python
# ⚠️ Be careful with user input!

# Bad: Allow any attribute
def update_user(user, data):
    for field, value in data.items():
        setattr(user, field, value)  # ❌ Dangerous!

# User could do:
update_user(user, {
    "__class__": SomethingMalicious  # ❌ Security risk!
})

# Good: Whitelist allowed attributes
def update_user(user, data):
    allowed = {"name", "email", "age"}  # ✓ Only these fields

    for field, value in data.items():
        if field in allowed and hasattr(user, field):
            setattr(user, field, value)  # ✓ Safe!
```

---

### Dictionary Unpacking (`**`)

**What it does:** Unpacks a dictionary into keyword arguments.

**Syntax:**
```python
function(**dictionary)
```

**Why we use it:**
- Pass multiple arguments from a dictionary
- Create objects dynamically from data
- Clean, Pythonic way to handle variable arguments

**Example:**

```python
# Function that expects keyword arguments
def create_user(name: str, email: str, age: int):
    print(f"Creating user: {name}, {email}, {age}")

# Without unpacking (verbose)
data = {"name": "John", "email": "john@example.com", "age": 30}
create_user(name=data["name"], email=data["email"], age=data["age"])

# With unpacking (clean)
data = {"name": "John", "email": "john@example.com", "age": 30}
create_user(**data)  # ← Unpacks dict into keyword arguments
# Equivalent to: create_user(name="John", email="john@example.com", age=30)
```

**Real usage in our code:**
```python
class User(Base):
    __tablename__ = "users"

    def __init__(self, name: str, email: str, is_active: bool):
        self.name = name
        self.email = email
        self.is_active = is_active

# In repository:
def create(self, obj_in: Dict[str, Any]):
    # obj_in = {"name": "John", "email": "john@example.com", "is_active": True}

    # Without unpacking (tedious)
    db_obj = User(
        name=obj_in["name"],
        email=obj_in["email"],
        is_active=obj_in["is_active"]
    )

    # With unpacking (elegant)
    db_obj = self.model(**obj_in)  # ← Creates User with all fields

    self.db.add(db_obj)
    self.db.commit()
    return db_obj
```

**Visual representation:**
```python
data = {"a": 1, "b": 2, "c": 3}

# Without **
function(a=data["a"], b=data["b"], c=data["c"])

# With **
function(**data)  # ← Much cleaner!

# Both are equivalent to:
function(a=1, b=2, c=3)
```

**Analogy:**
Think of `**` like a gift unwrapper:
```
🎁 Wrapped gift (dictionary) = {"toy": "car", "color": "red", "size": "small"}

Without **: Hand each item one by one
  - "Here's the toy: car"
  - "Here's the color: red"
  - "Here's the size: small"

With **: Unwrap everything at once
  - **gift → toy=car, color=red, size=small (all at once!)
```

---

### Tuple Unpacking

**What it does:** Assigns multiple values from a tuple to multiple variables in one line.

**Syntax:**
```python
var1, var2, var3 = (value1, value2, value3)
# or
var1, var2 = function_that_returns_tuple()
```

**Why we use it:**
- Return multiple values from a function cleanly
- Assign multiple variables simultaneously
- Pythonic and readable

**Example:**

```python
# Function returns a tuple
def get_user_info():
    return ("John", 30, "john@example.com")

# Without unpacking (awkward)
result = get_user_info()
name = result[0]
age = result[1]
email = result[2]

# With unpacking (clean)
name, age, email = get_user_info()
print(name)   # "John"
print(age)    # 30
print(email)  # "john@example.com"
```

**Real usage in our code:**
```python
def get_or_create(self, defaults=None, **kwargs):
    # Try to find existing record
    instance = self.filter_by(**kwargs)

    if instance:
        return instance[0], False  # ← Returns tuple (instance, created)

    # Create new record
    instance = self.create({**kwargs, **(defaults or {})})
    return instance, True  # ← Returns tuple (instance, created)

# Usage with tuple unpacking:
user, created = user_repo.get_or_create(
    email="john@example.com",
    defaults={"name": "John"}
)

if created:
    print(f"Created new user: {user.name}")
else:
    print(f"User already exists: {user.name}")
```

**Multiple return values:**
```python
def process_data(items):
    succeeded = []
    failed = []
    total = len(items)

    for item in items:
        if validate(item):
            succeeded.append(item)
        else:
            failed.append(item)

    # Return multiple values as tuple
    return succeeded, failed, total

# Unpack all three values
good_items, bad_items, count = process_data(data)
print(f"Processed {count} items: {len(good_items)} succeeded, {len(bad_items)} failed")
```

**Analogy:**
Think of tuple unpacking like receiving a package with multiple items:
```
📦 Package arrives = (book, pen, notebook)

Without unpacking:
  - Open package
  - Take item #1 → book
  - Take item #2 → pen
  - Take item #3 → notebook

With unpacking:
  book, pen, notebook = package  # ← All assigned at once!
```

---

### `@property` Decorator

**What it does:** Converts a method into a read-only attribute (getter).

**Syntax:**
```python
class MyClass:
    @property
    def my_attribute(self):
        return some_value
```

**Why we use it:**
- Access computed values like attributes (no parentheses needed)
- Add logic when getting a value (lazy computation, validation)
- Clean, intuitive API design

**Example:**

```python
class Circle:
    def __init__(self, radius):
        self.radius = radius

    # Without @property (method)
    def get_area(self):
        return 3.14159 * self.radius ** 2

    # With @property (computed attribute)
    @property
    def area(self):
        return 3.14159 * self.radius ** 2

    @property
    def diameter(self):
        return self.radius * 2

circle = Circle(5)

# Without @property (method call)
print(circle.get_area())  # 78.53975 (needs parentheses)

# With @property (attribute access)
print(circle.area)       # 78.53975 (no parentheses!)
print(circle.diameter)   # 10
```

**Real usage in our code:**
```python
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def skip(self) -> int:
        """Calculate offset from page number."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Alias for page_size."""
        return self.page_size

# Usage:
pagination = PaginationParams(page=3, page_size=20)

# Access like attributes (no parentheses)
print(pagination.skip)   # 40 (computed: (3-1) * 20)
print(pagination.limit)  # 20

# Use in queries:
users = repo.get_multi(skip=pagination.skip, limit=pagination.limit)
```

**Benefits:**
```python
class User:
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        return f"{self.first_name[0]}.{self.last_name[0]}."

user = User("John", "Doe")

# Clean, readable access
print(user.full_name)  # "John Doe" (computed on-the-fly)
print(user.initials)   # "J.D."

# vs without @property:
# print(user.get_full_name())  # ← Less clean
# print(user.get_initials())
```

**Analogy:**
Think of `@property` like a smart label on a bottle:
```
🍾 Bottle = Object
🏷️ Label = Property

Regular attribute: Label shows static text "Wine"
@property: Label shows dynamic info "75% full" (calculated when you look at it)

You don't need to ask the bottle "How full are you?"
You just look at the label: bottle.fullness
```

---

## Python Type System

### `TypeVar`

**What it does:** Creates a type variable for generic programming.

**Syntax:**
```python
from typing import TypeVar

T = TypeVar("T")  # Generic type variable
ModelType = TypeVar("ModelType", bound=BaseModel)  # Bounded type variable
```

**Why we use it:**
- Write flexible, reusable code
- Maintain type safety across generic operations
- Tell type checkers what types are expected

**Example:**

```python
from typing import TypeVar, List

# Define a generic type variable
T = TypeVar("T")

# Generic function that works with any type
def get_first_item(items: List[T]) -> T:
    """Get first item from list, preserving its type."""
    return items[0]

# Type checker understands the return type!
numbers: List[int] = [1, 2, 3]
first_number = get_first_item(numbers)  # Type: int ✓

strings: List[str] = ["a", "b", "c"]
first_string = get_first_item(strings)  # Type: str ✓
```

**Real usage in our code:**
```python
from typing import TypeVar, Generic

# Define bounded type variable
ModelType = TypeVar("ModelType", bound=BaseModel)
# ↑ ModelType must be a subclass of BaseModel

class BaseRepository(Generic[ModelType]):
    """Generic repository for any SQLAlchemy model."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: UUID) -> Optional[ModelType]:
        """Returns instance of ModelType."""
        return self.db.query(self.model).filter(self.model.uuid == id).first()

    def get_multi(self) -> List[ModelType]:
        """Returns list of ModelType instances."""
        return self.db.query(self.model).all()

# Usage with specific models:
user_repo = BaseRepository(User, db)  # ModelType = User
user = user_repo.get(user_id)  # Type checker knows this is User ✓

category_repo = BaseRepository(Category, db)  # ModelType = Category
category = category_repo.get(cat_id)  # Type checker knows this is Category ✓
```

**Without TypeVar (loses type information):**
```python
class BaseRepository:
    def get(self, id: UUID):  # Return type unknown
        return self.db.query(self.model).filter(self.model.uuid == id).first()

user_repo = BaseRepository(User, db)
user = user_repo.get(user_id)  # ⚠️ Type: Any (no type safety!)
print(user.name)  # ⚠️ No autocomplete, no type checking
```

**With TypeVar (preserves type information):**
```python
class BaseRepository(Generic[ModelType]):
    def get(self, id: UUID) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.uuid == id).first()

user_repo: BaseRepository[User] = BaseRepository(User, db)
user = user_repo.get(user_id)  # ✓ Type: Optional[User]
print(user.name)  # ✓ Autocomplete works! Type checker validates!
```

**Analogy:**
Think of `TypeVar` like a placeholder in a form:
```
📝 Form template: "Please enter your [TypeVar: T]"

When John fills it: "Please enter your [name: John]" → T = string
When filling age: "Please enter your [age: 30]" → T = int

TypeVar is the [T] placeholder that gets replaced with the actual type!
```

---

### Generic Types

**What it does:** Makes classes/functions work with multiple types while maintaining type safety.

**Syntax:**
```python
from typing import Generic, TypeVar

T = TypeVar("T")

class Container(Generic[T]):
    def __init__(self, item: T):
        self.item = item

    def get(self) -> T:
        return self.item
```

**Why we use it:**
- Write one implementation, works for all types
- Maintain type safety and autocomplete
- Avoid code duplication

**Example:**

```python
from typing import Generic, TypeVar, List

T = TypeVar("T")

class Stack(Generic[T]):
    """Generic stack that works with any type."""

    def __init__(self):
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def peek(self) -> T:
        return self._items[-1]

# Stack of integers
int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
value = int_stack.pop()  # Type: int ✓

# Stack of strings
str_stack: Stack[str] = Stack()
str_stack.push("hello")
str_stack.push("world")
text = str_stack.pop()  # Type: str ✓

# Type checker catches errors:
# int_stack.push("hello")  # ❌ Error: Expected int, got str
```

**Real usage in our code:**
```python
ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseRepository(Generic[ModelType]):
    """
    Generic repository that works with any SQLAlchemy model.
    ModelType is replaced with actual model type when instantiated.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def create(self, obj_in: Dict) -> ModelType:
        """Returns instance of the specific model type."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        return db_obj  # Type: ModelType (User, Category, etc.)

    def get_multi(self, skip: int, limit: int) -> List[ModelType]:
        """Returns list of specific model type."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

# When you create a repository, ModelType becomes concrete:
user_repo: BaseRepository[User] = BaseRepository(User, db)
# Now every method knows it's working with User:
# - create() returns User
# - get_multi() returns List[User]
# - IDE provides User-specific autocomplete

new_user = user_repo.create({"name": "John"})
# ↑ Type: User (not generic ModelType!)
print(new_user.email)  # ✓ Autocomplete knows User has .email
```

**Benefits visualization:**
```python
# Without Generic[T] - No type safety:
class Repository:
    def get(self, id):
        return self.db.query(self.model).get(id)

repo = Repository(User, db)
user = repo.get(123)  # Type: Any ⚠️
user.name  # No autocomplete, no validation ⚠️

# With Generic[T] - Full type safety:
class Repository(Generic[ModelType]):
    def get(self, id) -> ModelType:
        return self.db.query(self.model).get(id)

repo: Repository[User] = Repository(User, db)
user = repo.get(123)  # Type: User ✓
user.name  # Autocomplete ✓, Type validation ✓
```

**Analogy:**
Think of Generic types like a universal adapter:
```
🔌 Universal adapter (Generic[T]) that works with any device type

Plug in laptop → Adapter becomes "Laptop Adapter"
  - Knows laptop voltage, connector type
  - Provides laptop-specific power

Plug in phone → Adapter becomes "Phone Adapter"
  - Knows phone voltage, connector type
  - Provides phone-specific power

Generic[ModelType] is the universal adapter for database models!
```

---

## SQLAlchemy Concepts

### `engine.dispose()`

**What it does:** Closes all database connections in the connection pool and disposes of the engine.

**Syntax:**
```python
engine.dispose()
```

**Why we use it:**
- Clean up resources when shutting down application
- Release database connections
- Prevent connection leaks

**Example:**

```python
from sqlalchemy import create_engine

# Create engine with connection pool
engine = create_engine(
    "postgresql://user:pass@localhost/mydb",
    pool_size=10,  # Maximum 10 connections
    max_overflow=20  # Allow 20 overflow connections
)

# Engine maintains a pool of connections:
# [conn1, conn2, conn3, conn4, conn5] (ready to use)

# Application runs...
# Connections are borrowed and returned to pool

# Application shutdown:
engine.dispose()
# ↑ Closes ALL connections
# ↑ Releases database resources
# ↑ Cleans up the connection pool
```

**Real usage in our code:**
```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting application...")
    with engine.connect():
        print("✓ Database connection successful")

    yield  # Application runs here

    # Shutdown
    print("Shutting down...")
    engine.dispose()  # ← Clean up all database connections
    print("✓ Database connections closed")
```

**Without dispose():**
```python
# Application exits...
# ⚠️ Connections remain open
# ⚠️ Database resources not released
# ⚠️ Connection pool not cleaned up
# ⚠️ May cause "too many connections" errors
```

**With dispose():**
```python
# Application exits...
engine.dispose()
# ✓ All connections closed gracefully
# ✓ Database resources released
# ✓ Connection pool destroyed
# ✓ Clean shutdown
```

**Analogy:**
Think of `engine.dispose()` like closing a library at the end of the day:
```
🏛️ Library (Database) with reading rooms (connections)

During the day:
  - People (queries) come and go
  - Use reading rooms (connections)
  - Return to pool when done

Closing time (shutdown):
  engine.dispose()
  - Turn off lights in all rooms
  - Lock all doors
  - Ensure everyone left
  - Security guard goes home
```

---

### `Base.metadata.create_all()`

**What it does:** Creates all tables in the database based on your model definitions.

**Syntax:**
```python
Base.metadata.create_all(bind=engine)
```

**Why we use it:**
- Create database schema from models
- Sync models with database (in development)
- Quick setup for testing/development

**⚠️ Important:** In production, use Alembic migrations instead!

**Example:**

```python
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

# Create engine
engine = create_engine("postgresql://user:pass@localhost/mydb")

# Create all tables
Base.metadata.create_all(bind=engine)
# ↑ Executes CREATE TABLE statements for User and Post
```

**What happens:**
```sql
-- SQLAlchemy generates and executes:

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    email VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR,
    user_id INTEGER REFERENCES users(id)
);
```

**Real usage in our code:**
```python
# app/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

engine = create_engine(settings.DATABASE_URL)
Base = declarative_base()

def init_db():
    """Initialize database by creating all tables."""
    # Import all models first (so Base knows about them)
    from app.models import User, Post, Category, Comment

    # Create all tables
    Base.metadata.create_all(bind=engine)
    # ↑ Creates tables for all models that inherit from Base

# In app startup:
init_db()  # Creates tables if they don't exist
```

**Development vs Production:**
```python
# Development (OK to use):
def init_db():
    Base.metadata.create_all(bind=engine)  # Quick and easy

# Production (Use Alembic instead):
# $ alembic revision --autogenerate -m "Add users table"
# $ alembic upgrade head
# ↑ Better: Version control, rollback, migrations history
```

**Analogy:**
Think of `Base.metadata.create_all()` like building furniture from instructions:
```
📋 Instructions (Models) = How furniture should look
🔨 create_all() = Build all furniture pieces at once

Models define:
  - Table name (furniture type)
  - Columns (parts: legs, top, drawers)
  - Relationships (how pieces connect)

create_all() executes:
  - Read all instructions (models)
  - Build each piece (table)
  - Assemble everything (foreign keys)
  - Result: Complete furniture set (database schema)
```

---

### `bind` Parameter

**What it does:** Connects metadata or session to a specific database engine.

**Syntax:**
```python
Base.metadata.create_all(bind=engine)
sessionmaker(bind=engine)
```

**Why we use it:**
- Tell SQLAlchemy which database to use
- Connect operations to the correct engine
- Support multiple databases

**Example:**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engines for different databases
main_engine = create_engine("postgresql://localhost/main_db")
analytics_engine = create_engine("postgresql://localhost/analytics_db")

# Bind metadata to specific engine
Base.metadata.create_all(bind=main_engine)  # ← Creates tables in main_db

# Bind session to specific engine
MainSession = sessionmaker(bind=main_engine)  # ← Sessions for main_db
AnalyticsSession = sessionmaker(bind=analytics_engine)  # ← Sessions for analytics_db

# Use different databases
main_db = MainSession()
main_db.query(User).all()  # ← Queries main_db

analytics_db = AnalyticsSession()
analytics_db.query(AnalyticsEvent).all()  # ← Queries analytics_db
```

**Real usage in our code:**
```python
# app/database/connection.py
engine = create_engine(settings.DATABASE_URL)
Base = declarative_base()

def init_db():
    # bind tells SQLAlchemy to create tables in THIS engine's database
    Base.metadata.create_all(bind=engine)

# app/database/session.py
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine  # ← All sessions use this engine
)
```

**Without bind (error):**
```python
Base.metadata.create_all()  # ❌ Error: No bind specified!
# SQLAlchemy doesn't know which database to use
```

**With bind (works):**
```python
Base.metadata.create_all(bind=engine)  # ✓ Creates tables in engine's database
```

**Multiple databases example:**
```python
# Different engines for different purposes
main_db = create_engine("postgresql://localhost/main")
cache_db = create_engine("postgresql://localhost/cache")
archive_db = create_engine("postgresql://localhost/archive")

# Bind different operations to different databases
MainBase.metadata.create_all(bind=main_db)
CacheBase.metadata.create_all(bind=cache_db)
ArchiveBase.metadata.create_all(bind=archive_db)
```

**Analogy:**
Think of `bind` like addressing a letter:
```
✉️ Letter (SQL operation) needs an address (database)

Without bind:
  "Please create tables"
  ❓ Where? Which database?

With bind:
  "Please create tables at postgresql://localhost/mydb"
  ✓ Clear destination!

bind = The address label on the envelope
```

---

### `self.db.rollback()`

**What it does:** Undoes all database changes in the current transaction.

**Syntax:**
```python
try:
    # Database operations
    db.commit()
except Exception:
    db.rollback()  # ← Undo everything
```

**Why we use it:**
- Maintain data consistency
- Prevent partial updates on errors
- Implement all-or-nothing transactions

**Example:**

```python
def transfer_money(from_account, to_account, amount):
    try:
        # Step 1: Deduct from sender
        from_account.balance -= amount
        db.add(from_account)

        # Simulate error
        if amount > 1000:
            raise ValueError("Amount too large!")

        # Step 2: Add to receiver
        to_account.balance += amount
        db.add(to_account)

        # Commit both changes together
        db.commit()
        print("Transfer successful!")

    except Exception as e:
        # Something went wrong - undo EVERYTHING
        db.rollback()
        print(f"Transfer failed: {e}")
        print("All changes reverted!")
```

**What happens:**
```python
# Scenario: Transfer $1500 (triggers error)

# Before transaction:
# from_account.balance = 2000
# to_account.balance = 500

try:
    from_account.balance -= 1500  # Now: 500 (in memory)
    db.add(from_account)

    raise ValueError("Amount too large!")  # ← Error!

    to_account.balance += 1500  # ← Never executes
    db.add(to_account)

    db.commit()  # ← Never executes

except ValueError:
    db.rollback()  # ← Reverts from_account changes!

# After rollback:
# from_account.balance = 2000  ✓ Back to original!
# to_account.balance = 500     ✓ Unchanged!
```

**Real usage in our code:**
```python
def create(self, obj_in: Dict[str, Any]) -> ModelType:
    try:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()  # ← Save to database
        self.db.refresh(db_obj)
        return db_obj

    except IntegrityError as e:
        self.db.rollback()  # ← Undo everything if constraint violated
        raise e

    except SQLAlchemyError as e:
        self.db.rollback()  # ← Undo everything on any database error
        raise e
```

**Without rollback (data corruption):**
```python
def create_user_and_profile(user_data, profile_data):
    # Create user
    user = User(**user_data)
    db.add(user)
    db.commit()  # ← User saved

    # Create profile
    profile = Profile(**profile_data, user_id=user.id)
    db.add(profile)
    db.commit()  # ← Error! Profile data invalid

    # Result: User exists but has no profile ⚠️ (inconsistent!)
```

**With rollback (data consistency):**
```python
def create_user_and_profile(user_data, profile_data):
    try:
        user = User(**user_data)
        db.add(user)

        profile = Profile(**profile_data, user_id=user.id)
        db.add(profile)

        db.commit()  # ← Save both together

    except Exception:
        db.rollback()  # ← If profile fails, user is also reverted
        raise

    # Result: Either both exist or neither exists ✓ (consistent!)
```

**Analogy:**
Think of `rollback()` like "Undo" in a text editor:
```
📝 Document (Database)

Type: "Hello World"
Type: "This is great"
Type: "sdjfhkjsdhfkj"  ← Oops! Random characters

Press Ctrl+Z (rollback):
  ← Undo random characters
  ← Back to "This is great"

Without rollback: Stuck with garbage text
With rollback: Clean document restored
```

---

### `IntegrityError`

**What it does:** Exception raised when database constraints are violated.

**Common causes:**
- Unique constraint violation (duplicate values)
- Foreign key constraint violation (referencing non-existent record)
- Not null constraint violation (required field missing)
- Check constraint violation (invalid value)

**Example:**

```python
from sqlalchemy.exc import IntegrityError

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)  # ← Unique constraint
    age = Column(Integer, nullable=False)  # ← Not null constraint

# Example 1: Unique constraint violation
try:
    user1 = User(email="john@example.com", age=30)
    db.add(user1)
    db.commit()  # ✓ Success

    user2 = User(email="john@example.com", age=25)  # ← Same email!
    db.add(user2)
    db.commit()  # ❌ IntegrityError: email must be unique!

except IntegrityError as e:
    db.rollback()
    print(f"Cannot create user: {e}")
    # "Cannot create user: duplicate key value violates unique constraint"

# Example 2: Not null constraint violation
try:
    user3 = User(email="jane@example.com")  # ← Missing age!
    db.add(user3)
    db.commit()  # ❌ IntegrityError: age cannot be null!

except IntegrityError as e:
    db.rollback()
    print(f"Invalid user data: {e}")
    # "Invalid user data: null value in column 'age' violates not-null constraint"
```

**Real usage in our code:**
```python
def create(self, obj_in: Dict[str, Any]) -> ModelType:
    try:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    except IntegrityError as e:
        self.db.rollback()
        # Handle constraint violations specifically
        if "unique" in str(e).lower():
            raise ValueError("Record with this value already exists")
        elif "foreign key" in str(e).lower():
            raise ValueError("Referenced record does not exist")
        elif "null" in str(e).lower():
            raise ValueError("Required field is missing")
        else:
            raise e
```

**Handling in FastAPI:**
```python
@router.post("/users")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user_repo = BaseRepository(User, db)

    try:
        new_user = user_repo.create(user_data.model_dump())
        return new_user

    except IntegrityError as e:
        # Check specific constraint
        if "email" in str(e) and "unique" in str(e):
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Data validation failed"
            )
```

**Common constraint violations:**
```python
# 1. Unique constraint
user = User(email="duplicate@example.com")  # Email already exists
# IntegrityError: duplicate key value violates unique constraint "users_email_key"

# 2. Foreign key constraint
post = Post(user_id=999)  # User 999 doesn't exist
# IntegrityError: foreign key constraint "posts_user_id_fkey" violated

# 3. Not null constraint
user = User(name=None)  # Name is required
# IntegrityError: null value in column "name" violates not-null constraint

# 4. Check constraint
user = User(age=-5)  # Age must be positive
# IntegrityError: check constraint "users_age_check" violated
```

**Analogy:**
Think of `IntegrityError` like validation errors at airport security:
```
🛂 Security checkpoint (Database constraints)

✓ Valid passport → Pass through (constraint satisfied)
❌ Duplicate passport → Stop! (unique constraint violated)
❌ No passport → Stop! (not null constraint violated)
❌ Expired passport → Stop! (check constraint violated)

IntegrityError = Security stops you for violating rules
```

---

### `SQLAlchemyError`

**What it does:** Base exception class for all SQLAlchemy errors.

**Why we use it:**
- Catch any database-related error
- Broader exception handling than specific errors
- Fallback for unexpected database issues

**Exception hierarchy:**
```
SQLAlchemyError (base)
├── IntegrityError (constraint violations)
├── OperationalError (database connection issues)
├── ProgrammingError (SQL syntax errors)
├── DataError (invalid data)
└── DatabaseError (other database errors)
```

**Example:**

```python
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

def create_user(user_data):
    try:
        user = User(**user_data)
        db.add(user)
        db.commit()
        return user

    except IntegrityError as e:
        # Specific handling for constraint violations
        db.rollback()
        print(f"Constraint violation: {e}")
        raise ValueError("Duplicate or invalid data")

    except OperationalError as e:
        # Specific handling for connection issues
        db.rollback()
        print(f"Database connection error: {e}")
        raise ConnectionError("Database unavailable")

    except SQLAlchemyError as e:
        # Catch-all for any other database errors
        db.rollback()
        print(f"Unexpected database error: {e}")
        raise RuntimeError("Database operation failed")
```

**Real usage in our code:**
```python
def create(self, obj_in: Dict[str, Any]) -> ModelType:
    try:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    except IntegrityError as e:
        # Handle specific constraint errors first
        self.db.rollback()
        raise e

    except SQLAlchemyError as e:
        # Catch any other database errors
        self.db.rollback()
        raise e
```

**Specific vs General handling:**
```python
# Pattern: Specific first, general last
try:
    db.commit()

except IntegrityError:
    # Handle constraint violations
    print("Data validation failed")

except OperationalError:
    # Handle connection issues
    print("Cannot connect to database")

except SQLAlchemyError:
    # Handle any other database error
    print("Unknown database error")

except Exception:
    # Handle non-database errors
    print("Unexpected error")
```

**Different error types:**
```python
# IntegrityError - Constraint violation
user = User(email="duplicate@example.com")
db.commit()  # ❌ IntegrityError

# OperationalError - Database connection issue
engine = create_engine("postgresql://wrong_host/db")
db.query(User).all()  # ❌ OperationalError

# ProgrammingError - SQL syntax error
db.execute("SELCT * FROM users")  # ❌ ProgrammingError (typo: SELCT)

# DataError - Invalid data type
user = User(age="not a number")
db.commit()  # ❌ DataError

# All caught by: SQLAlchemyError
```

**Analogy:**
Think of `SQLAlchemyError` like "Exception" in error handling:
```
🎯 Error types (most specific to most general):

FileNotFoundError (very specific)
  ↓
IOError (more general)
  ↓
OSError (even more general)
  ↓
Exception (most general)

Similarly:

IntegrityError (very specific)
  ↓
DatabaseError (more general)
  ↓
SQLAlchemyError (most general SQLAlchemy error)
  ↓
Exception (catch everything)
```

---

### `synchronize_session=False`

**What it does:** Controls how the session handles bulk update/delete operations.

**Options:**
- `synchronize_session='evaluate'` - Updates session objects (default, slow)
- `synchronize_session='fetch'` - Re-fetches affected objects (slower)
- `synchronize_session=False` - Doesn't update session (fast, but be careful!)

**Why we use `False`:**
- Much faster for bulk operations
- We're not using the session objects after the update
- We commit immediately after

**Example:**

```python
# Scenario: Update many users at once

# Method 1: synchronize_session='evaluate' (default)
query = db.query(User).filter(User.is_active == True)
query.update({"last_login": datetime.now()})
# ↑ SQLAlchemy tries to update all User objects in session
# ↑ Slow for large datasets
db.commit()

# Method 2: synchronize_session=False (faster)
query = db.query(User).filter(User.is_active == True)
query.update(
    {"last_login": datetime.now()},
    synchronize_session=False  # ← Don't update session objects
)
# ↑ Just executes UPDATE in database
# ↑ Much faster
db.commit()
```

**What happens:**

```python
# With synchronize_session='evaluate' (slow):
# 1. Execute UPDATE statement in database
# 2. Find all matching User objects in session
# 3. Update each object's last_login attribute in memory
# 4. Commit
# ⏱️ Slow for 10,000+ records

# With synchronize_session=False (fast):
# 1. Execute UPDATE statement in database
# 2. Commit
# ⏱️ Fast! No extra work
```

**Real usage in our code:**
```python
def update_multi(self, filters: Dict[str, Any], obj_in: Dict[str, Any]) -> int:
    try:
        query = self.db.query(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)

        # Exclude deleted records
        query = query.filter(self.model.deleted_at.is_(None))

        # Add updated_at timestamp
        obj_in["updated_at"] = datetime.now(timezone.utc)

        # Bulk update - synchronize_session=False for performance
        count = query.update(obj_in, synchronize_session=False)

        self.db.commit()
        return count

    except SQLAlchemyError as e:
        self.db.rollback()
        raise e

# Usage:
# Update 10,000 users at once (fast!)
count = user_repo.update_multi(
    filters={"status": "pending"},
    obj_in={"status": "processed"}
)
print(f"Updated {count} users")
```

**When to use each option:**

```python
# Use synchronize_session='evaluate' when:
# - You need session objects updated
# - Small number of records (<100)
# - You'll access objects after update

users = db.query(User).filter(User.status == "pending").all()
for user in users:
    user.status = "processed"
    # Access user later...
db.commit()

# Use synchronize_session=False when:
# - Bulk operations (1000s of records)
# - Don't need session objects after
# - Performance is critical

db.query(User).filter(User.status == "pending").update(
    {"status": "processed"},
    synchronize_session=False  # ← Much faster!
)
db.commit()
```

**Analogy:**
Think of `synchronize_session` like updating a to-do list:
```
📋 To-do list (session) vs 📊 Master database

synchronize_session='evaluate':
  1. Update master database
  2. Update your personal to-do list copy
  ⏱️ Slow: Two updates

synchronize_session=False:
  1. Update master database
  2. Ignore your personal copy
  ⏱️ Fast: One update

Use False when: You won't look at your personal copy again
```

---

### `ilike` (Case-Insensitive Search)

**What it does:** Performs case-insensitive pattern matching in SQL.

**Syntax:**
```python
Model.field.ilike(pattern)
```

**Why we use it:**
- Search without worrying about capitalization
- More user-friendly search
- Pattern matching with wildcards

**Example:**

```python
# Case-sensitive (like)
users = db.query(User).filter(User.name.like("john")).all()
# ↑ Matches: "john"
# ↑ Doesn't match: "John", "JOHN", "JoHn"

# Case-insensitive (ilike)
users = db.query(User).filter(User.name.ilike("john")).all()
# ↑ Matches: "john", "John", "JOHN", "JoHn"
# ↑ Much more user-friendly!

# With wildcards
users = db.query(User).filter(User.name.ilike("%john%")).all()
# ↑ Matches: "john", "Johnny", "johnsmith", "Mr. John", "JOHN DOE"
# ↑ % = wildcard (matches anything)
```

**Wildcard patterns:**
```python
# % = Match any characters (zero or more)
User.name.ilike("john%")    # Starts with "john": john, johnny, johnson
User.name.ilike("%john")    # Ends with "john": john, bigj john
User.name.ilike("%john%")   # Contains "john": john, johnny, mrjohn

# _ = Match exactly one character
User.name.ilike("j_hn")     # Matches: john, jahn, jihn
User.name.ilike("j__n")     # Matches: john, jean, juan
```

**Real usage in our code:**
```python
def search(
    self,
    search_fields: List[str],
    search_term: str,
    skip: int = 0,
    limit: int = 100
) -> List[ModelType]:
    query = self.db.query(self.model)

    # Build OR conditions for all search fields
    search_conditions = []
    for field in search_fields:
        if hasattr(self.model, field):
            # Case-insensitive search with wildcards
            search_conditions.append(
                getattr(self.model, field).ilike(f"%{search_term}%")
            )

    if search_conditions:
        query = query.filter(or_(*search_conditions))

    return query.offset(skip).limit(limit).all()

# Usage:
# Search for users by name or email
results = user_repo.search(
    search_fields=["name", "email"],
    search_term="john",  # Case-insensitive!
    limit=20
)
# Finds: "John Doe", "JOHNNY", "john@example.com", etc.
```

**Comparison:**

```python
# like (case-sensitive) - PostgreSQL
User.name.like("John%")
# SQL: WHERE name LIKE 'John%'
# Matches: John, Johnny
# Doesn't match: john, JOHN

# ilike (case-insensitive) - PostgreSQL
User.name.ilike("John%")
# SQL: WHERE name ILIKE 'John%'
# Matches: John, johnny, JOHN, JoHnNy

# For other databases (case-insensitive)
from sqlalchemy import func
User.name.like(func.lower("John%"))
# SQL: WHERE LOWER(name) LIKE 'john%'
```

**Real-world search example:**
```python
@router.get("/users/search")
def search_users(
    q: str = Query(..., description="Search term"),
    db: Session = Depends(get_db)
):
    user_repo = BaseRepository(User, db)

    # Search in multiple fields (case-insensitive)
    results = db.query(User).filter(
        or_(
            User.name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.username.ilike(f"%{q}%")
        )
    ).limit(20).all()

    return results

# GET /users/search?q=john
# Finds:
#   - Name: "John Doe", "Johnny Walker", "Big John"
#   - Email: "john@example.com", "JOHNNY@EMAIL.COM"
#   - Username: "john123", "JOHNSMITH"
```

**Analogy:**
Think of `ilike` like a flexible search:
```
📚 Library book search

like "Harry Potter":
  ❌ "harry potter" (lowercase)
  ✓ "Harry Potter" (exact match)
  ❌ "HARRY POTTER" (uppercase)

ilike "Harry Potter":
  ✓ "harry potter"
  ✓ "Harry Potter"
  ✓ "HARRY POTTER"
  ✓ "harry POTTER"

With wildcards ("%harry%"):
  ✓ "Harry Potter"
  ✓ "The Harry Potter Series"
  ✓ "harry potter and the..."
```

---

### SQL Wildcards (`%` and `_`)

**What are wildcards?** Special characters used in SQL pattern matching to represent unknown characters.

**Two main wildcards:**
1. **`%` (percent)** - Matches **any number of characters** (zero or more)
2. **`_` (underscore)** - Matches **exactly one character**

**Why we use them:**
- Flexible search patterns
- Find partial matches
- User-friendly search functionality
- Build powerful queries without knowing exact values

---

#### Percent Wildcard (`%`)

**What it does:** Matches zero or more characters of any type.

**Patterns:**

```python
# Pattern: "john%"  (starts with)
User.name.ilike("john%")
# Matches: "john", "johnny", "johnson", "john123", "john doe"
# Doesn't match: "abc john", "mr john"

# Pattern: "%john"  (ends with)
User.name.ilike("%john")
# Matches: "john", "bigjohn", "littlejohn", "123john"
# Doesn't match: "johnny", "johnson"

# Pattern: "%john%"  (contains)
User.name.ilike("%john%")
# Matches: "john", "johnny", "bigjohn", "mr john doe", "johnson"
# Can appear anywhere in the string!

# Pattern: "j%n"  (starts with 'j', ends with 'n')
User.name.ilike("j%n")
# Matches: "john", "jn", "jason", "julian", "jonathen"
# % matches anything (or nothing) in between

# Pattern: "%john%doe%"  (contains 'john', then 'doe')
User.name.ilike("%john%doe%")
# Matches: "john doe", "john smith doe", "mr john and ms doe"
```

**Real-world examples:**

```python
# Search emails from specific domain
User.email.ilike("%@gmail.com")
# Matches: "user@gmail.com", "john.doe@gmail.com", "test123@gmail.com"

# Search phone numbers with area code
User.phone.ilike("555%")
# Matches: "555-1234", "555-9999", "5551234567"

# Search files by extension
File.name.ilike("%.pdf")
# Matches: "document.pdf", "report.pdf", "file123.pdf"

# Search products by keyword
Product.name.ilike("%laptop%")
# Matches: "Gaming Laptop", "Dell Laptop Pro", "Best laptop 2024"
```

---

#### Underscore Wildcard (`_`)

**What it does:** Matches exactly ONE character (any character).

**Patterns:**

```python
# Pattern: "j_hn"  (j + any char + hn)
User.name.ilike("j_hn")
# Matches: "john" (o), "jahn" (a), "jihn" (i)
# Doesn't match: "jhn" (missing char), "johan" (too many chars)

# Pattern: "j__n"  (j + any 2 chars + n)
User.name.ilike("j__n")
# Matches: "john" (oh), "jean" (ea), "juan" (ua)
# Doesn't match: "jn" (not enough), "jason" (too many between j and n)

# Pattern: "___"  (exactly 3 characters)
User.code.ilike("___")
# Matches: "ABC", "123", "xyz"
# Doesn't match: "AB" (too short), "ABCD" (too long)

# Pattern: "20__-__-__"  (date pattern YYYY-MM-DD for 20XX)
Event.date.ilike("20__-__-__")
# Matches: "2024-01-15", "2099-12-31", "2000-06-22"
# Doesn't match: "2024-1-5" (missing leading zeros)
```

**Real-world examples:**

```python
# Match 3-letter airport codes
Airport.code.ilike("___")
# Matches: "LAX", "JFK", "ORD"
# Doesn't match: "LAXO" (4 letters)

# Match phone format XXX-XXXX
Phone.number.ilike("___-____")
# Matches: "555-1234", "123-4567"
# Doesn't match: "5551234" (no dash), "55-1234" (wrong format)

# Match product codes (2 letters + 4 digits)
Product.sku.ilike("__-____")
# Matches: "AB-1234", "XY-9999"

# Match license plates (3 letters + 3 digits)
Vehicle.plate.ilike("___-___")
# Matches: "ABC-123", "XYZ-789"
```

---

#### Combining Wildcards

**Power patterns using both `%` and `_`:**

```python
# Pattern: "%j_hn%"  (contains 'j', any char, 'hn')
User.name.ilike("%j_hn%")
# Matches: "john doe", "mr jahn", "jihn smith"

# Pattern: "___@%.com"  (3-char username at any domain ending in .com)
User.email.ilike("___@%.com")
# Matches: "abc@test.com", "xyz@gmail.com", "joe@x.com"
# Doesn't match: "ab@test.com" (username too short)

# Pattern: "2024-__-__"  (any day in 2024)
Event.date.ilike("2024-__-__")
# Matches: "2024-01-01", "2024-12-31"
# Doesn't match: "2024-1-1" (missing leading zero)

# Pattern: "%_@_%._%"  (valid email pattern - simplified)
User.email.ilike("%_@_%._%")
# Matches: "a@b.c", "user@example.com"
# Doesn't match: "@test.com" (no username), "user@" (no domain)
```

---

#### Escaping Wildcards

**Problem:** What if you need to search for literal `%` or `_` characters?

**Solution:** Escape them with backslash `\`:

```python
# Search for literal underscore in username
User.username.ilike("john\\_doe")
# Matches: "john_doe" (literal underscore)
# Doesn't match: "johnXdoe" (where X is any character)

# Search for literal percent in description
Product.description.ilike("%50\\%%")
# Matches: "50% off", "Get 50% discount"
# The middle % is escaped (literal), outer % are wildcards

# Search for file with underscore
File.name.ilike("report\\_2024.pdf")
# Matches: "report_2024.pdf" (literal underscore)
# Doesn't match: "reportX2024.pdf" (where X is any char)
```

---

#### Practical Usage Patterns

**1. Flexible name search:**

```python
def search_users(search_term: str):
    """Search users by name (flexible)."""
    pattern = f"%{search_term}%"  # Add wildcards around search term

    users = db.query(User).filter(
        or_(
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            User.email.ilike(pattern)
        )
    ).all()

    return users

# Usage:
search_users("john")
# Finds: "John Doe", "Johnny Walker", "Mr. John", "john@email.com"
```

**2. Autocomplete search:**

```python
def autocomplete_search(prefix: str, limit: int = 10):
    """Autocomplete search (starts with prefix)."""
    pattern = f"{prefix}%"  # Starts with prefix

    results = db.query(User.name).filter(
        User.name.ilike(pattern)
    ).limit(limit).all()

    return results

# Usage:
autocomplete_search("joh")
# Returns: ["John", "Johnny", "Johnson", "Johanna"]
```

**3. Phone number search (flexible format):**

```python
def find_phone(digits: str):
    """Find phone number (ignores formatting)."""
    # Remove all non-digits from search
    clean_digits = ''.join(c for c in digits if c.isdigit())

    # Build pattern: each digit can be followed by anything
    pattern = '%'.join(clean_digits) + '%'

    # Example: "5551234" becomes "5%5%5%1%2%3%4%"
    phones = db.query(User).filter(
        User.phone.ilike(pattern)
    ).all()

    return phones

# Usage:
find_phone("5551234")
# Matches: "555-1234", "5551234", "(555) 123-4", "555.123.4"
```

**4. Date range search:**

```python
def events_in_month(year: int, month: int):
    """Find all events in a specific month."""
    pattern = f"{year}-{month:02d}-%"  # Year-Month-AnyDay

    events = db.query(Event).filter(
        Event.date.ilike(pattern)
    ).all()

    return events

# Usage:
events_in_month(2024, 1)
# Matches: "2024-01-01", "2024-01-15", "2024-01-31"
# Pattern: "2024-01-%"
```

---

#### Wildcard Performance Tips

**⚠️ Performance considerations:**

```python
# ❌ SLOW: Leading wildcard prevents index usage
User.email.ilike("%@gmail.com")  # Scans entire table
User.name.ilike("%john")  # Scans entire table

# ✓ FASTER: No leading wildcard can use index
User.email.ilike("john%")  # Can use index on email
User.name.ilike("John%")  # Can use index on name

# ⚡ FASTEST: Exact match (no wildcards)
User.email.ilike("john@gmail.com")  # Full index usage
```

**Best practices:**

1. **Avoid leading wildcards when possible** - They prevent index usage
2. **Use full-text search for complex searches** - PostgreSQL FTS, Elasticsearch
3. **Add wildcards programmatically** - Let users type without wildcards
4. **Limit results** - Always use `.limit()` with wildcard searches
5. **Consider caching** - Wildcard searches can be expensive

---

#### Wildcard Cheat Sheet

| Pattern | Meaning | Example Match |
|---------|---------|---------------|
| `john%` | Starts with "john" | "john", "johnny", "johnson" |
| `%john` | Ends with "john" | "john", "bigjohn", "123john" |
| `%john%` | Contains "john" | "john", "johnny", "mr john doe" |
| `j%n` | Starts 'j', ends 'n' | "john", "jason", "julian" |
| `j_hn` | 'j' + any char + 'hn' | "john", "jahn", "jihn" |
| `j__n` | 'j' + 2 chars + 'n' | "john", "jean", "juan" |
| `___` | Exactly 3 characters | "ABC", "123", "xyz" |
| `%j_hn%` | Contains 'j' + char + 'hn' | "john doe", "mr jahn" |
| `20__-__-__` | Date pattern 20XX-XX-XX | "2024-01-15", "2099-12-31" |
| `john\_doe` | Literal underscore | "john_doe" (not "johnXdoe") |

---

#### Analogy

Think of wildcards like Mad Libs (fill-in-the-blank game):
```
📝 Mad Libs Template

% = [Anything goes here - any words, any length]
_ = [Exactly one word/letter]

Template: "The ___ cat sat on the ___."
         = "The big cat sat on the mat."
         = "The old cat sat on the roof."

SQL: "j%n"  = "j[anything]n"
    Matches: "john", "jason", "jn", "jurassicPeriodTimeline-station"

SQL: "j_n"  = "j[one char]n"
    Matches: "jan", "jin", "jon"
    Doesn't match: "john" (2 chars), "jn" (0 chars)
```

---

### `relationship()`

**What it does:** Defines relationships between SQLAlchemy models (tables).

**Syntax:**
```python
relationship(
    "TargetModel",
    back_populates="reverse_field",  # Two-way relationship
    backref="reverse_field",  # One-way auto-generated
    foreign_keys=[field],  # Specify FK manually
    remote_side=[field],  # For self-referential relationships
)
```

**Why we use it:**
- Access related data easily (joins handled automatically)
- Navigate between tables intuitively
- Lazy or eager loading of related data

**Types of relationships:**
1. **One-to-Many** (Parent → Children)
2. **Many-to-One** (Child → Parent)
3. **Many-to-Many** (Through association table)
4. **Self-Referential** (Model references itself)

**Example 1: One-to-Many (User has many Posts)**

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    # One user has many posts
    posts = relationship("Post", back_populates="author")
    #                    ↑ Model name   ↑ Field in Post model

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Many posts belong to one user
    author = relationship("User", back_populates="posts")
    #                     ↑ Model name   ↑ Field in User model

# Usage:
user = db.query(User).first()
print(user.posts)  # ← Automatically queries all posts by this user
# [Post(title="First Post"), Post(title="Second Post")]

post = db.query(Post).first()
print(post.author.name)  # ← Automatically joins User table
# "John Doe"
```

**Example 2: Self-Referential (Comments with Replies)**

```python
class Comment(Base):
    __tablename__ = "comments"

    uuid = Column(UUID, primary_key=True)
    content = Column(String)
    parent_comment_uuid = Column(UUID, ForeignKey("comments.uuid"))

    # Comment can have many replies (children)
    replies = relationship(
        "Comment",  # ← Same model!
        backref="parent",  # ← Auto-creates parent field
        remote_side="Comment.uuid",  # ← Which side is "remote" (parent)
        foreign_keys=[parent_comment_uuid]  # ← Which FK to use
    )

# Usage:
parent_comment = Comment(content="This is a comment")
db.add(parent_comment)
db.commit()

reply1 = Comment(content="Reply 1", parent_comment_uuid=parent_comment.uuid)
reply2 = Comment(content="Reply 2", parent_comment_uuid=parent_comment.uuid)
db.add_all([reply1, reply2])
db.commit()

# Access relationships:
print(parent_comment.replies)  # ← [reply1, reply2]
print(reply1.parent)  # ← parent_comment (auto-created by backref)
```

**Example 3: Many-to-Many (Posts and Tags)**

```python
# Association table
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id")),
    Column("tag_id", Integer, ForeignKey("tags.id"))
)

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)

    # Many posts can have many tags
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    # Many tags can belong to many posts
    posts = relationship("Post", secondary=post_tags, back_populates="tags")

# Usage:
post = Post(title="Python Tutorial")
tag1 = Tag(name="Python")
tag2 = Tag(name="Programming")

post.tags = [tag1, tag2]  # ← Assign multiple tags
db.add(post)
db.commit()

print(post.tags)  # ← [Tag(name="Python"), Tag(name="Programming")]
print(tag1.posts)  # ← [Post(title="Python Tutorial")]
```

**Relationship parameters:**

```python
relationship(
    "TargetModel",

    # Two-way relationship (both sides defined)
    back_populates="other_field",

    # One-way relationship (auto-generates reverse)
    backref="other_field",

    # Specify foreign key (when ambiguous)
    foreign_keys=[model.field],

    # For self-referential (which side is parent)
    remote_side=[model.field],

    # Loading strategy
    lazy="select",  # Load when accessed (default)
    lazy="joined",  # Always load with JOIN
    lazy="subquery",  # Load with subquery
    lazy="dynamic",  # Return query object

    # Cascade operations
    cascade="all, delete-orphan",  # Delete children when parent deleted

    # For many-to-many
    secondary=association_table,
)
```

**Real usage in our code:**

```python
# app/models/comment.py
class Comment(BaseModel):
    __tablename__ = "comments"

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    content = Column(Text, nullable=False)
    post_uuid = Column(UUID(as_uuid=True), ForeignKey("posts.uuid"))
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"))
    parent_comment_uuid = Column(UUID(as_uuid=True), ForeignKey("comments.uuid"))

    # Relationship to parent post
    post = relationship("Post", back_populates="comments")

    # Relationship to author
    author = relationship("User", back_populates="comments")

    # Self-referential relationship (nested comments)
    replies = relationship(
        "Comment",
        backref="parent",  # Auto-creates parent attribute
        remote_side="Comment.uuid",  # Parent side
        foreign_keys=[parent_comment_uuid]  # FK to use
    )

# Usage in queries:
comment = db.query(Comment).first()

# Access related data (no manual joins needed!)
print(comment.post.title)  # ← Post title (automatic JOIN)
print(comment.author.name)  # ← Author name (automatic JOIN)
print(comment.replies)  # ← List of reply comments
print(comment.parent)  # ← Parent comment (if this is a reply)
```

**Analogy:**
Think of `relationship()` like connections between pages in Wikipedia:
```
📖 Wikipedia Article (Model)

One-to-Many:
  "Python" article → Links to many "Python libraries" articles
  Author → Has written many articles

Many-to-One:
  Article → Belongs to one category

Many-to-Many:
  Articles ↔ Tags (articles can have multiple tags, tags can have multiple articles)

Self-Referential:
  Article → "See also" section (links to other articles)
  Comment → Replies (comments can reply to comments)

relationship() = The hyperlinks that connect everything together
```

---

## Pydantic Concepts

### `ConfigDict`

**What it does:** Configures how a Pydantic model behaves.

**Common settings:**
```python
model_config = ConfigDict(
    from_attributes=True,  # ORM mode (read from SQLAlchemy models)
    populate_by_name=True,  # Accept field name or alias
    str_strip_whitespace=True,  # Remove leading/trailing spaces
    use_enum_values=True,  # Use enum values instead of enum objects
    validate_assignment=True,  # Validate when assigning values
    arbitrary_types_allowed=True,  # Allow custom types
)
```

**Why we use it:**
- Control validation behavior
- Enable ORM compatibility
- Customize serialization

**Example:**

```python
from pydantic import BaseModel, ConfigDict, Field

# Without configuration (default behavior)
class UserDefault(BaseModel):
    name: str
    email: str

# With configuration
class UserConfigured(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # ← Can create from SQLAlchemy models
        str_strip_whitespace=True,  # ← Auto-strip whitespace
        validate_assignment=True,  # ← Validate on property assignment
    )

    name: str
    email: str

# Usage:

# 1. from_attributes (ORM mode)
class UserDB:  # SQLAlchemy model
    def __init__(self):
        self.name = "John"
        self.email = "john@example.com"

user_db = UserDB()

# Without from_attributes:
# UserDefault.model_validate(user_db)  # ❌ Error: Can't read from object

# With from_attributes:
user = UserConfigured.model_validate(user_db)  # ✓ Works!
print(user.name)  # "John"

# 2. str_strip_whitespace
user = UserConfigured(
    name="  John  ",  # ← Extra spaces
    email="john@example.com"
)
print(user.name)  # "John" (spaces removed!)

# 3. validate_assignment
user = UserConfigured(name="John", email="john@example.com")
user.email = "invalid"  # ✓ Validates immediately (with validate_assignment=True)
# Without it: Only validates when creating, not when assigning
```

**Real usage in our code:**

```python
# app/schemas/base.py
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # ← Enable ORM mode
        # Allows creating Pydantic models from SQLAlchemy models:
        # user_schema = UserResponse.model_validate(user_db_model)

        populate_by_name=True,  # ← Allow using field names or aliases
        # Can use either: {"user_name": "John"} or {"userName": "John"}

        str_strip_whitespace=True,  # ← Auto-clean strings
        # Input: "  John  " → Stored as: "John"

        use_enum_values=True,  # ← Use enum values, not enum objects
        # status = Status.ACTIVE → Serializes as "active", not Status.ACTIVE
    )

# All schemas inherit this configuration:
class UserResponse(BaseSchema):
    uuid: UUID
    name: str
    email: str
    # ↑ Automatically has all BaseSchema config

# Usage in FastAPI route:
@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.uuid == user_id).first()

    # from_attributes=True allows this:
    return user_db  # ← SQLAlchemy model automatically converted to Pydantic
    # FastAPI serializes using UserResponse schema
```

**from_attributes detailed:**

```python
# SQLAlchemy model
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

# Pydantic model WITHOUT from_attributes
class UserSchema1(BaseModel):
    name: str
    email: str

# Pydantic model WITH from_attributes
class UserSchema2(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: str

user_db = db.query(UserDB).first()

# Without from_attributes (fails):
# user1 = UserSchema1.model_validate(user_db)  # ❌ Error!
# Only works with dict: UserSchema1(name=user_db.name, email=user_db.email)

# With from_attributes (works):
user2 = UserSchema2.model_validate(user_db)  # ✓ Success!
print(user2.name)  # "John"
```

**Analogy:**
Think of `ConfigDict` like settings on a camera:
```
📷 Camera (Pydantic model)
⚙️ Settings (ConfigDict)

from_attributes = "Compatible with old film" (read from different format)
str_strip_whitespace = "Auto-clean lens" (clean input)
validate_assignment = "Check each photo immediately" (validate on change)
use_enum_values = "Save as JPEG, not RAW" (simple format)

ConfigDict = The settings panel that controls how the camera works
```

---

### `Field()`

**What it does:** Adds validation, metadata, and documentation to Pydantic model fields.

**Syntax:**
```python
field_name: type = Field(
    default=value,  # Default value
    default_factory=callable,  # Function to generate default
    alias="alternate_name",  # Accept alternate name
    title="Human Name",  # Display name
    description="What this field means",  # Documentation
    min_length=1,  # Minimum length (strings/lists)
    max_length=100,  # Maximum length
    gt=0,  # Greater than (numbers)
    ge=0,  # Greater than or equal
    lt=100,  # Less than
    le=100,  # Less than or equal
    pattern=r"regex",  # Regex validation
    examples=["example1", "example2"],  # Example values
)
```

**Why we use it:**
- Add validation rules
- Provide default values
- Document fields for OpenAPI
- Add constraints

**Example:**

```python
from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    # Simple field
    name: str

    # With default value
    age: int = Field(default=0)

    # With validation
    email: str = Field(
        ...,  # ← Required (no default)
        min_length=5,
        max_length=100,
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",  # Email pattern
        description="User's email address",
        examples=["john@example.com"]
    )

    # Number constraints
    score: int = Field(
        default=0,
        ge=0,  # Greater than or equal to 0
        le=100,  # Less than or equal to 100
        description="User score (0-100)"
    )

    # String constraints
    username: str = Field(
        ...,  # Required
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$",  # Alphanumeric and underscore only
        description="Unique username"
    )

    # Optional with default
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User biography"
    )

# Validation in action:

# Valid:
user = User(
    name="John",
    email="john@example.com",
    username="john_doe",
    score=85
)

# Invalid - too short:
# User(name="Jo", email="ab", username="jo")
# ValidationError: email must be at least 5 characters

# Invalid - out of range:
# User(name="John", email="john@example.com", username="john_doe", score=150)
# ValidationError: score must be <= 100
```

**Real usage in our code:**

```python
# app/schemas/user.py
from pydantic import EmailStr, Field
from app.schemas.base import CreateSchema, UpdateSchema

class UserCreate(CreateSchema):
    """Schema for creating a new user."""

    email: EmailStr = Field(
        ...,  # Required
        description="User's email address",
        examples=["john@example.com"]
    )

    name: str = Field(
        ...,  # Required
        min_length=1,
        max_length=100,
        description="User's full name",
        examples=["John Doe"]
    )

    password: str = Field(
        ...,  # Required
        min_length=8,
        max_length=100,
        description="User's password (min 8 characters)",
        examples=["SecurePass123!"]
    )

    is_active: bool = Field(
        default=True,
        description="Whether the user account is active"
    )

class UserUpdate(UpdateSchema):
    """Schema for updating a user (all fields optional)."""

    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address"
    )

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New name"
    )

    password: Optional[str] = Field(
        default=None,
        min_length=8,
        description="New password"
    )
```

**Field() in action (FastAPI route):**

```python
@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    user_data: UserCreate,  # ← Field() validation happens here!
    db: Session = Depends(get_db)
):
    # If we reach here, data is already validated by Pydantic:
    # ✓ email is valid
    # ✓ name is 1-100 characters
    # ✓ password is at least 8 characters

    user_repo = BaseRepository(User, db)
    new_user = user_repo.create(user_data.model_dump())
    return new_user

# Request with invalid data:
# POST /users
# {
#   "email": "invalid",  ← Invalid email
#   "name": "",  ← Too short
#   "password": "short"  ← Too short
# }
#
# Response: 422 Unprocessable Entity
# {
#   "detail": [
#     {"loc": ["body", "email"], "msg": "invalid email format"},
#     {"loc": ["body", "name"], "msg": "ensure this value has at least 1 characters"},
#     {"loc": ["body", "password"], "msg": "ensure this value has at least 8 characters"}
#   ]
# }
```

**Analogy:**
Think of `Field()` like a form with instructions:
```
📝 Registration form

Name: [_________]
  ↑ Field(min_length=1, max_length=50)
  Instructions: "1-50 characters"

Email: [_________]
  ↑ Field(pattern=email_regex)
  Instructions: "Must be valid email"

Age: [_________]
  ↑ Field(ge=0, le=120)
  Instructions: "Must be 0-120"

Bio: [_________] (optional)
  ↑ Field(default=None, max_length=500)
  Instructions: "Optional, max 500 characters"

Field() = The instructions and validation rules on each form field
```

---

## FastAPI Concepts

### `Query()` vs `Field()`

**What's the difference?**

| Aspect | `Query()` | `Field()` |
|--------|-----------|-----------|
| **Used for** | URL query parameters | Request body fields |
| **Location** | FastAPI route parameters | Pydantic model fields |
| **Example** | `?page=1&limit=20` | `{"name": "John", "age": 30}` |
| **Import** | `from fastapi import Query` | `from pydantic import Field` |

**Query() - For URL parameters:**

```python
from fastapi import Query

@router.get("/users")
def get_users(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number"
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Items per page"
    ),
    search: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search term"
    )
):
    # URL: /users?page=2&limit=50&search=john
    return {"page": page, "limit": limit, "search": search}
```

**Field() - For request body:**

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(
        ...,  # Required
        min_length=1,
        max_length=100,
        description="User's name"
    )
    email: str = Field(
        ...,
        description="User's email"
    )
    age: int = Field(
        ge=0,
        le=120,
        description="User's age"
    )

@router.post("/users")
def create_user(user: UserCreate):
    # Request body:
    # {
    #   "name": "John",
    #   "email": "john@example.com",
    #   "age": 30
    # }
    return user
```

**Complete example showing both:**

```python
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()

# Schema for request body (uses Field)
class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Post title"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Post content"
    )

# Route with both query parameters and request body
@router.post("/posts")
def create_post(
    # Query parameters (uses Query)
    publish: bool = Query(
        default=False,
        description="Publish immediately"
    ),
    notify: bool = Query(
        default=True,
        description="Send notifications"
    ),
    # Request body (uses Field internally)
    post_data: PostCreate
):
    # URL: /posts?publish=true&notify=false
    # Body: {"title": "My Post", "content": "Post content..."}

    return {
        "post": post_data,
        "publish": publish,
        "notify": notify
    }
```

**When to use each:**

```python
# Use Query() when:
# - Data comes from URL (?key=value)
# - Optional filters, pagination, search
# - GET, DELETE requests (no body)

@router.get("/items")
def get_items(
    category: Optional[str] = Query(None),  # ← Query parameter
    min_price: float = Query(0, ge=0),  # ← Query parameter
):
    pass

# Use Field() when:
# - Data comes from request body (JSON)
# - POST, PUT, PATCH requests
# - Complex nested data structures

class ItemCreate(BaseModel):
    name: str = Field(...)  # ← Body field
    price: float = Field(gt=0)  # ← Body field

@router.post("/items")
def create_item(item: ItemCreate):  # ← Request body
    pass
```

**Analogy:**
```
🌐 Web request

Query() = Questions in the URL
  GET /search?q=python&page=1&limit=20
  ↑ All visible in address bar
  ↑ Optional filters and settings
  ↑ Use Query()

Field() = Form data you fill out
  POST /users
  Body: {"name": "John", "email": "john@example.com"}
  ↑ Sent in request body (not visible in URL)
  ↑ Complex structured data
  ↑ Use Field()
```

---

## Summary

This guide covered essential Python, SQLAlchemy, Pydantic, and FastAPI concepts:

**Python Built-ins:**
- `hasattr()` / `getattr()` - Safe attribute access
- `**` - Dictionary unpacking
- Tuple unpacking - Multiple return values
- `@property` - Computed attributes

**Type System:**
- `TypeVar` / `Generic` - Generic programming with type safety

**SQLAlchemy:**
- `engine.dispose()` - Clean database shutdown
- `Base.metadata.create_all()` - Create tables
- `bind` - Connect to database
- `rollback()` - Undo transactions
- `IntegrityError` / `SQLAlchemyError` - Exception handling
- `synchronize_session=False` - Bulk operation performance
- `ilike` - Case-insensitive search
- `relationship()` - Model relationships

**Pydantic:**
- `ConfigDict` - Model configuration
- `Field()` - Field validation and documentation

**FastAPI:**
- `Query()` vs `Field()` - URL parameters vs body fields

Each concept includes examples, real usage, and analogies to make understanding easier!
