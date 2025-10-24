# Authentication Made Simple: JWT, Sessions & OAuth

A beginner-friendly guide to understanding and implementing authentication in web applications.

---

## Table of Contents

1. [Authentication Basics](#authentication-basics)
2. [Password Hashing, Salt & How Password Verification Works](#password-hashing-salt--how-password-verification-works)
3. [What is JWT? (Simple Explanation)](#what-is-jwt-simple-explanation)
4. [What are Sessions? (Simple Explanation)](#what-are-sessions-simple-explanation)
5. [JWT vs Sessions: Which One Should I Use?](#jwt-vs-sessions-which-one-should-i-use)
6. [Implementing JWT (Step by Step)](#implementing-jwt-step-by-step)
7. [Implementing Sessions (Step by Step)](#implementing-sessions-step-by-step)
8. [What is OAuth? (Login with Google/GitHub)](#what-is-oauth-login-with-googlegithub)
9. [Security Tips (Keep Your App Safe)](#security-tips-keep-your-app-safe)
10. [Common Mistakes and How to Avoid Them](#common-mistakes-and-how-to-avoid-them)

---

## Authentication Basics

### What is Authentication?

**Authentication** is proving who you are. It's like showing your ID at the airport.

**Real-life examples:**
- Logging into Facebook with email + password
- Unlocking your phone with fingerprint
- Showing your driver's license to buy alcohol

### Why Do We Need It?

Without authentication:
- Anyone could access your private data
- Strangers could post as you
- Your account could be stolen

### Two Main Questions

1. **Who are you?** (Authentication) → Login with username/password
2. **What can you do?** (Authorization) → Admin vs regular user permissions

---

## Password Hashing, Salt & How Password Verification Works

### The Problem: Why We Can't Store Plain Passwords

Imagine you have a diary with all your secrets. Would you leave it on your desk where anyone can read it? **NO!** You'd lock it up.

The same goes for passwords. If you store them like this in your database:

```
❌ TERRIBLE IDEA:
User: John
Password: mypassword123
```

**What happens if a hacker breaks in?**
- They see everyone's passwords
- They can login as anyone
- They can use those passwords on other websites (people reuse passwords!)

**Real-world example:** In 2013, Adobe was hacked. 38 million passwords were stolen. Many were stored in plain text. People's accounts on OTHER websites were also hacked because they reused passwords.

---

### The Solution: Password Hashing

**Hashing** is like turning your password into scrambled eggs. Once it's scrambled, you **can't unscramble it** back to the original password.

#### Real-Life Analogy

Think of hashing like this:

```
You have a glass of orange juice 🧃
→ You pour it into a blender with ice and sugar
→ You blend it into a smoothie 🥤
→ You can NEVER turn that smoothie back into plain orange juice
→ But you can always make the SAME smoothie from the same juice
```

#### How It Works

```python
# User registers with password
password = "mypassword123"

# We hash it (scramble it)
hashed = hash_password("mypassword123")
# Result: "$2b$12$KIXz7e8QrLxV9PqH3f5G0uF6F3r4oXy4ZqJ9k..."

# We save the HASH to database, NOT the original password
database.save(user="John", password=hashed)
```

**In the database:**
```
✅ SAFE:
User: John
Password: $2b$12$KIXz7e8QrLxV9PqH3f5G0uF6F3r4oXy4ZqJ9k...
```

Even if a hacker steals this, they can't use it! It's gibberish.

---

### What is Salt? (Secret Ingredient)

#### The Problem with Basic Hashing

Imagine two users have the same password:

```python
User1: password = "123456"
User2: password = "123456"

# Without salt, they get the SAME hash
hash("123456") = "abc123xyz..."
hash("123456") = "abc123xyz..."  # Same!
```

**Problem:** If a hacker sees two users have the same hash, they know those users have the same password!

**Bigger problem:** Hackers have "rainbow tables" - huge lists of common passwords and their hashes.

```
Hacker's rainbow table:
"123456" → "abc123xyz..."
"password" → "def456uvw..."
"qwerty" → "ghi789rst..."
```

They can instantly crack millions of passwords!

#### The Solution: Salt

**Salt** is a random string added to each password BEFORE hashing.

**Real-Life Analogy:**

```
Making cookies 🍪

Without salt:
- Everyone uses the same recipe
- All chocolate chip cookies taste the same
- Easy to copy

With salt (secret ingredient):
- Each baker adds their own secret ingredient
- Your cookies taste unique
- Hard to copy exactly
```

#### How Salt Works

```python
# User 1 registers
password1 = "123456"
salt1 = generate_random_salt()  # "xyz789abc"

# Add salt to password and hash it
hash1 = hash(password1 + salt1)
# hash("123456xyz789abc") = "aaa111bbb222..."

# Save BOTH the hash AND the salt
database.save(
    user="User1",
    password_hash="aaa111bbb222...",
    salt="xyz789abc"
)

# User 2 registers with SAME password
password2 = "123456"
salt2 = generate_random_salt()  # "qqq999www" (different!)

# Add salt to password and hash it
hash2 = hash(password2 + salt2)
# hash("123456qqq999www") = "zzz888yyy777..." (different result!)

# Save to database
database.save(
    user="User2",
    password_hash="zzz888yyy777...",
    salt="qqq999www"
)
```

**Result:**
```
User1: password="123456", hash="aaa111bbb222...", salt="xyz789abc"
User2: password="123456", hash="zzz888yyy777...", salt="qqq999www"

Even though passwords are the same, hashes are DIFFERENT! ✅
```

**Why this is good:**
- Rainbow tables don't work anymore
- Each password is unique even if people use the same password
- Hackers must crack each password individually (very slow!)

---

### How Password Comparison Works (The Magic!)

When a user tries to login, we need to check if their password is correct. But we only have the scrambled hash in the database. How do we check?

#### The Process (Step by Step)

**Scenario:** User "John" tries to login

```python
# Step 1: User sends their password
login_attempt = "mypassword123"

# Step 2: Get John's data from database
from_database = {
    "username": "John",
    "password_hash": "$2b$12$KIXz7e8QrLxV9PqH...",
    "salt": "xyz789abc"  # Some libraries include salt in the hash itself
}

# Step 3: Take the password the user just entered
user_entered = "mypassword123"

# Step 4: Hash it THE SAME WAY as when they registered
# (using the SAME salt that's stored in database)
new_hash = hash(user_entered + from_database["salt"])

# Step 5: Compare the new hash with the stored hash
if new_hash == from_database["password_hash"]:
    print("Password correct! ✅")
    # Login successful
else:
    print("Password wrong! ❌")
    # Login failed
```

#### Visual Explanation

```
REGISTRATION TIME:
User types: "mypassword123"
    ↓
Add salt: "mypassword123" + "xyz789abc"
    ↓
Hash it: "$2b$12$KIXz7e8QrLxV9PqH..."
    ↓
Save to database: "$2b$12$KIXz7e8QrLxV9PqH..." + salt

─────────────────────────────────────────────

LOGIN TIME:
User types: "mypassword123"
    ↓
Get salt from database: "xyz789abc"
    ↓
Add salt: "mypassword123" + "xyz789abc"
    ↓
Hash it: "$2b$12$KIXz7e8QrLxV9PqH..."
    ↓
Compare with database hash:
  New hash:   "$2b$12$KIXz7e8QrLxV9PqH..."
  Saved hash: "$2b$12$KIXz7e8QrLxV9PqH..."
    ↓
MATCH! ✅ Login successful
```

**If user enters WRONG password:**
```
User types: "wrongpassword"
    ↓
Add salt: "wrongpassword" + "xyz789abc"
    ↓
Hash it: "$2b$12$DifferentHash123..."
    ↓
Compare with database:
  New hash:   "$2b$12$DifferentHash123..."
  Saved hash: "$2b$12$KIXz7e8QrLxV9PqH..."
    ↓
NO MATCH! ❌ Login failed
```

---

### Real Code Example (Complete)

```python
# app/core/security.py

from passlib.context import CryptContext

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The "bcrypt" algorithm automatically handles salt for you!
# You don't need to manually generate or store salt


def hash_password(password: str) -> str:
    """
    Hash a password for storing.

    This function:
    1. Generates a random salt
    2. Combines password + salt
    3. Hashes the combination
    4. Returns the hash (salt is included inside!)

    Example:
        password = "mypassword123"
        hashed = hash_password(password)
        # hashed = "$2b$12$KIXz7e8QrLxV9PqH3f5G0uF6F3r4oXy4ZqJ9k..."

        The hash includes:
        - $2b$ = bcrypt algorithm
        - $12$ = cost factor (how many rounds of hashing)
        - Rest = salt + actual hash (all mixed together)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a password matches the hash.

    This function:
    1. Extracts the salt from the hashed_password
    2. Hashes the plain_password with that salt
    3. Compares the new hash with the stored hash
    4. Returns True if they match

    Example:
        # During registration
        hashed = hash_password("mypassword123")
        # Save hashed to database

        # During login
        user_input = "mypassword123"
        is_correct = verify_password(user_input, hashed)
        # is_correct = True ✅

        wrong_input = "wrongpassword"
        is_correct = verify_password(wrong_input, hashed)
        # is_correct = False ❌
    """
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────────────────────────────
# USAGE IN YOUR APPLICATION
# ─────────────────────────────────────────────────────────────────

# 1. REGISTRATION (storing password)
def register_user(email: str, password: str):
    """Register a new user."""
    # Hash the password before saving
    hashed_password = hash_password(password)

    # Save to database
    user = User(
        email=email,
        password=hashed_password  # ← Store the HASH, not the plain password!
    )
    database.save(user)

    return user


# 2. LOGIN (checking password)
def login_user(email: str, password: str):
    """Login a user."""
    # Get user from database
    user = database.get_user_by_email(email)

    if not user:
        raise Exception("User not found")

    # Compare the password user entered with the hash in database
    is_password_correct = verify_password(password, user.password)

    if not is_password_correct:
        raise Exception("Wrong password")

    # Password is correct!
    return user
```

---

### Complete Flow: Registration → Database → Login

#### 1. User Registers

```python
# Frontend sends
POST /register
{
  "email": "john@example.com",
  "password": "mypassword123"
}

# Backend processes
@router.post("/register")
def register(email: str, password: str):
    # Hash the password
    hashed = hash_password("mypassword123")
    # Result: "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."

    # Save to database
    user = User(
        email="john@example.com",
        password="$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."  # ← Hashed!
    )
    db.save(user)
```

**Database now looks like:**
```
┌─────────────────────┬──────────────────────────────────────┐
│ email               │ password                             │
├─────────────────────┼──────────────────────────────────────┤
│ john@example.com    │ $2b$12$Xk5f7H8j9L2mN4pQ6rS8tU...   │
└─────────────────────┴──────────────────────────────────────┘
```

#### 2. User Tries to Login

```python
# Frontend sends
POST /login
{
  "email": "john@example.com",
  "password": "mypassword123"  # User enters password
}

# Backend processes
@router.post("/login")
def login(email: str, password: str):
    # 1. Get user from database
    user = get_user_by_email("john@example.com")
    # user.password = "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."

    # 2. Verify the password
    is_correct = verify_password(
        "mypassword123",                        # What user entered
        "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."     # What's in database
    )

    # 3. Behind the scenes, verify_password does:
    #    - Extract salt from the hash
    #    - Hash "mypassword123" with that salt
    #    - Compare new hash with stored hash
    #    - Return True if they match

    if is_correct:
        # Create JWT token or session
        token = create_token(user.id)
        return {"token": token}
    else:
        raise Exception("Wrong password")
```

---

### Why Bcrypt is Special

We use **bcrypt** for password hashing. Here's why:

#### 1. Automatic Salt
You don't need to manually generate or store salt. Bcrypt does it for you!

```python
# You just do this
hashed = hash_password("mypassword123")

# Bcrypt automatically:
# 1. Generates random salt
# 2. Combines password + salt
# 3. Hashes the combination
# 4. Stores salt inside the hash
```

#### 2. Intentionally Slow
Bcrypt is designed to be slow (on purpose!).

**Why slow is good:**
```
Bad hash (MD5):
- Hacker can try 1 BILLION passwords per second
- Cracks "password123" in 0.001 seconds

Good hash (Bcrypt):
- Hacker can try 1,000 passwords per second (1000x slower!)
- Takes weeks to crack even simple passwords
```

#### 3. Adjustable Difficulty
Bcrypt has a "cost factor" that makes it slower as computers get faster.

```python
# Cost factor = 12 (default)
# Takes about 0.3 seconds to hash
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

# Cost factor = 14 (more secure, slower)
# Takes about 1.2 seconds to hash
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=14)
```

Higher cost = more secure = slower for hackers (and you).

---

### Common Questions

#### Q1: Can I "decrypt" a hashed password back to the original?

**A: NO!** That's the whole point. Hashing is **one-way**.

```
Original → Hash ✅
Hash → Original ❌ (impossible!)
```

It's like asking "Can I turn scrambled eggs back into raw eggs?" No!

#### Q2: If I can't decrypt it, how do I check if password is correct?

**A:** You hash the new password and compare the hashes:

```python
# Registration
original_password = "mypassword123"
hash1 = hash(original_password)  # "$2b$12$Xk5f7..."
save_to_database(hash1)

# Login (user enters same password)
user_entered = "mypassword123"
hash2 = hash(user_entered)       # "$2b$12$Xk5f7..." (SAME!)

if hash1 == hash2:
    print("Correct!")
```

#### Q3: What if two users have the same password?

**A:** Thanks to salt, they'll have different hashes!

```python
User1: password="123456" → hash="$2b$12$aaa..."
User2: password="123456" → hash="$2b$12$zzz..." (different!)
```

Each user gets a unique salt, so same password = different hash.

#### Q4: Where is the salt stored?

**A:** With bcrypt, the salt is stored INSIDE the hash!

```python
hash = "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tUvWxYz..."
       └──┴──└──────────┴───────────────────┘
        │  │      │              │
   Algorithm │    Salt      Actual hash
         Cost factor

You don't need a separate salt column in database!
```

#### Q5: Is this 100% secure?

**A:** Nothing is 100% secure, but bcrypt is very good:

```
✅ Used by major companies (Google, Facebook, etc.)
✅ Resisted attacks for 20+ years
✅ Recommended by security experts
✅ Automatically handles salt
✅ Intentionally slow (frustrates hackers)

But you still need:
- HTTPS (encrypt data in transit)
- Strong passwords (8+ characters, mixed)
- Rate limiting (block brute force attacks)
```

---

### Summary: The Complete Picture

```
USER REGISTERS:
1. User types password: "mypassword123"
2. Backend hashes it: "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."
3. Save hash to database (NOT the original password!)

USER LOGS IN:
1. User types password: "mypassword123"
2. Backend gets hash from database: "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."
3. Backend hashes what user typed: "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."
4. Compare them:
   - If SAME → Login successful ✅
   - If DIFFERENT → Wrong password ❌

HACKER BREAKS IN:
1. Hacker sees hash: "$2b$12$Xk5f7H8j9L2mN4pQ6rS8tU..."
2. Hacker tries to crack it (try every possible password)
3. Thanks to bcrypt + salt:
   - Takes YEARS to crack even simple passwords
   - Rainbow tables don't work
   - Each password must be cracked individually
```

**Key Takeaways:**

1. **Never store plain passwords** - always hash them
2. **Use bcrypt** - it handles salt automatically
3. **Salt makes each hash unique** - even for same passwords
4. **Comparison is done by hashing again** - not by decrypting
5. **Hashing is one-way** - you can't reverse it

**Remember:** Think of password hashing like turning orange juice into a smoothie. You can always make the same smoothie from the same juice, but you can never turn a smoothie back into plain juice! 🧃 → 🥤

---

## What is JWT? (Simple Explanation)

### The Simple Idea

**JWT (JSON Web Token)** is like a **digital passport**.

Think of it like this:
```
You go to an airport ✈️
→ Show your ID at check-in
→ They give you a boarding pass
→ You use that boarding pass to get on the plane
→ The boarding pass has all your info on it
```

JWT works the same way:
```
You login to a website 💻
→ Send username + password
→ Server gives you a JWT token
→ You send that token with every request
→ The token has your info inside it
```

### What Does a JWT Look Like?

It's a long string of letters and numbers:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Looks confusing?** Don't worry! You don't read it - computers do.

### Inside the JWT

If we decode it, we see:

```json
{
  "user_id": "12345",
  "name": "John Doe",
  "email": "john@example.com",
  "expires": "2025-01-20 15:00:00"
}
```

### Key Points About JWT

✅ **Self-contained**: All info is IN the token
✅ **Stateless**: Server doesn't store anything
✅ **Portable**: Works everywhere (mobile apps, websites, APIs)
❌ **Can't be cancelled**: Once issued, it's valid until it expires
❌ **Bigger size**: Takes more space than session IDs

### Real-World Analogy

**JWT is like a movie ticket:**
- You buy it once
- It has your seat number and movie time printed on it
- You don't need to go back to the box office
- But you can't cancel it once printed
- It expires after the movie

---

## What are Sessions? (Simple Explanation)

### The Simple Idea

**Sessions** are like having a **locker at the gym**.

Think of it like this:
```
You go to the gym 🏋️
→ They give you a locker key (#247)
→ Your stuff is in locker #247
→ You show your key to access your locker
→ The gym keeps all your belongings
```

Sessions work the same way:
```
You login to a website 💻
→ Server creates a session and stores your info
→ Server gives you a session ID (like a key)
→ You send that ID with every request
→ Server looks up your info using that ID
```

### What Does a Session ID Look Like?

It's a random string:

```
abc123xyz456def789
```

### Where is the Data?

**Important difference from JWT:**

**JWT:** Data is IN the token (client has it)
```
Token = {user_id: 123, name: "John", email: "john@example.com"}
```

**Session:** Data is ON the server (client only has ID)
```
Client has: session_id = "abc123"

Server has:
  session_id: "abc123"
  data:
    user_id: 123
    name: "John"
    email: "john@example.com"
```

### Key Points About Sessions

✅ **Revocable**: Can be deleted immediately (logout works instantly)
✅ **Small cookie**: Only session ID sent to client
✅ **Secure**: Sensitive data stays on server
✅ **Flexible**: Can change session data anytime
❌ **Needs storage**: Requires database or Redis
❌ **Less scalable**: All servers need access to session store

### Real-World Analogy

**Session is like a coat check:**
- You give them your coat
- They give you a numbered ticket
- Your coat stays with them
- You can get it back anytime with the ticket
- They can refuse to give it back (ban you)

---

## JWT vs Sessions: Which One Should I Use?

### Quick Decision Guide

Ask yourself these questions:

#### Question 1: Are you building a mobile app?
- **Yes** → Use JWT ✅
- **No** → Keep reading

#### Question 2: Do you need to logout users immediately?
- **Yes** → Use Sessions ✅
- **No** → JWT is fine

#### Question 3: Will you have millions of users?
- **Yes** → Use JWT (more scalable) ✅
- **No** → Either is fine

#### Question 4: Is it a banking/healthcare app?
- **Yes** → Use Sessions (more secure) ✅
- **No** → Either is fine

### Simple Comparison

| What do you care about? | Use JWT | Use Sessions |
|------------------------|---------|--------------|
| Mobile app | ✅ | ❌ |
| Simple to build | ❌ | ✅ |
| Can logout instantly | ❌ | ✅ |
| Works across different servers easily | ✅ | ❌ |
| Most secure | ❌ | ✅ |
| Fastest | ✅ | ❌ |
| Easiest to understand | ❌ | ✅ |

### My Recommendation

**For beginners:** Start with **Sessions** (simpler!)

**For mobile apps:** Use **JWT** (mobile apps need it)

**For serious apps:** Use **JWT for access** + **Sessions for refresh** (best of both worlds)

---

## Implementing JWT (Step by Step)

### Step 1: Install What You Need

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

**What are these?**
- `python-jose`: Creates and reads JWT tokens
- `passlib`: Hashes passwords securely

### Step 2: Create a Secret Key

This is like a password that signs your tokens.

```python
# In your .env file
SECRET_KEY=your-super-secret-key-here-change-this-in-production

# Or generate one in Python
import secrets
print(secrets.token_urlsafe(32))
# Output: dkf89sdkjf8sdf89sdfsdf8sdfsdf8sdf
```

⚠️ **IMPORTANT**: Never share your secret key! It's like your bank PIN.

### Step 3: Create Token Functions

**Simple version with comments:**

```python
# app/core/jwt.py

from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = "your-secret-key-here"  # Get from .env in real app
ALGORITHM = "HS256"  # Type of encryption

def create_token(user_id: str) -> str:
    """
    Create a JWT token for a user.

    Think of this as: "Give the user a boarding pass"
    """
    # What goes inside the token
    data = {
        "sub": user_id,  # "sub" means "subject" (who this token is for)
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)  # Expires in 30 min
    }

    # Create the token
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return token


def verify_token(token: str) -> dict:
    """
    Check if a token is valid.

    Think of this as: "Check if the boarding pass is real"
    """
    try:
        # Decode the token
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data
    except:
        # Token is invalid or expired
        return None
```

### Step 4: Hash Passwords

**Never save passwords as plain text!**

❌ **BAD**: `password: "mypassword123"` (anyone who sees database knows it)
✅ **GOOD**: `password: "$2b$12$asdkfjlk..."` (gibberish that only computer understands)

```python
# app/core/security.py

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    """
    Turn a password into gibberish (hash it).

    Example:
      Input:  "mypassword123"
      Output: "$2b$12$KIXz7e8Qr..."
    """
    return pwd_context.hash(password)


def check_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if password matches the hash.

    Example:
      plain_password = "mypassword123"
      hashed_password = "$2b$12$KIXz7e8Qr..."
      Returns: True (they match!)
    """
    return pwd_context.verify(plain_password, hashed_password)
```

### Step 5: Create Registration Endpoint

```python
# app/api/v1/routes/auth.py

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/register")
async def register(email: str, password: str, name: str):
    """
    Register a new user.

    Steps:
    1. Check if email already exists
    2. Hash the password
    3. Save user to database
    4. Give them a token
    """
    # 1. Check if user exists
    existing_user = get_user_by_email(email)  # You create this function
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    # 2. Hash password
    hashed_password = hash_password(password)

    # 3. Save to database
    new_user = create_user_in_database(
        email=email,
        name=name,
        password=hashed_password
    )

    # 4. Create token
    token = create_token(str(new_user.id))

    # 5. Return token to user
    return {
        "access_token": token,
        "token_type": "bearer",  # Standard way to send tokens
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name
        }
    }
```

### Step 6: Create Login Endpoint

```python
@router.post("/login")
async def login(email: str, password: str):
    """
    Login existing user.

    Steps:
    1. Find user by email
    2. Check if password is correct
    3. Give them a token
    """
    # 1. Find user
    user = get_user_by_email(email)

    # 2. Check password
    if not user or not check_password(password, user.password):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    # 3. Create token
    token = create_token(str(user.id))

    # 4. Return token
    return {
        "access_token": token,
        "token_type": "bearer"
    }
```

### Step 7: Protect Your Endpoints

```python
from fastapi import Depends, Header, HTTPException

async def get_current_user(authorization: str = Header(None)):
    """
    Get the logged-in user from the token.

    This is used in protected endpoints.
    """
    # 1. Check if token was sent
    if not authorization:
        raise HTTPException(status_code=401, detail="Not logged in")

    # 2. Extract token (format is "Bearer <token>")
    try:
        token = authorization.split(" ")[1]
    except:
        raise HTTPException(status_code=401, detail="Invalid token format")

    # 3. Verify token
    data = verify_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 4. Get user from database
    user_id = data.get("sub")
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# Now use it in protected endpoints
@router.get("/profile")
async def get_profile(current_user = Depends(get_current_user)):
    """
    Get current user's profile.

    This endpoint requires login (token).
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name
    }
```

### Step 8: Using JWT from Frontend

**JavaScript example:**

```javascript
// Register
async function register(email, password, name) {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name })
  });

  const data = await response.json();

  // Save token
  localStorage.setItem('token', data.access_token);

  return data.user;
}

// Login
async function login(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();

  // Save token
  localStorage.setItem('token', data.access_token);
}

// Make authenticated requests
async function getProfile() {
  const token = localStorage.getItem('token');

  const response = await fetch('/api/v1/profile', {
    headers: {
      'Authorization': `Bearer ${token}`  // Send token here
    }
  });

  return await response.json();
}

// Logout (just delete the token)
function logout() {
  localStorage.removeItem('token');
}
```

---

## Implementing Sessions (Step by Step)

### Step 1: Install Redis

**What is Redis?** Think of it as a super-fast database that stores temporary data.

```bash
# Install Redis
pip install redis

# Run Redis (on Windows, download from Redis website)
# On Mac: brew install redis && redis-server
# On Linux: sudo apt install redis && redis-server
```

### Step 2: Create Session Manager

```python
# app/core/session.py

import redis
import secrets
import json
from datetime import datetime, timedelta

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class SessionManager:
    """
    Manages user sessions.

    Think of this as: "Manages the gym lockers"
    """

    def create_session(self, user_id: str, user_data: dict) -> str:
        """
        Create a new session.

        Steps:
        1. Generate random session ID
        2. Store user data in Redis
        3. Return session ID
        """
        # 1. Generate random ID (like giving someone locker #247)
        session_id = secrets.token_urlsafe(32)

        # 2. Store in Redis
        data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            **user_data  # Extra info like name, email
        }

        # Save for 12 hours (43200 seconds)
        redis_client.setex(
            f"session:{session_id}",  # Key
            43200,                     # Expire in 12 hours
            json.dumps(data)           # Value
        )

        return session_id


    def get_session(self, session_id: str) -> dict:
        """
        Get session data.

        Think: "Get what's in locker #247"
        """
        data = redis_client.get(f"session:{session_id}")

        if data:
            return json.loads(data)
        return None


    def delete_session(self, session_id: str):
        """
        Delete a session (logout).

        Think: "Empty the locker and take away the key"
        """
        redis_client.delete(f"session:{session_id}")


session_manager = SessionManager()
```

### Step 3: Create Registration Endpoint

```python
from fastapi import Response

@router.post("/register")
async def register(email: str, password: str, name: str, response: Response):
    """
    Register with sessions.
    """
    # 1-3. Same as JWT (check user, hash password, save to database)
    existing_user = get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = hash_password(password)
    new_user = create_user_in_database(email, name, hashed_password)

    # 4. Create session (different from JWT!)
    session_id = session_manager.create_session(
        str(new_user.id),
        {"email": email, "name": name}
    )

    # 5. Set cookie (browser will send this automatically)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,    # JavaScript can't access it (security!)
        max_age=43200     # 12 hours
    )

    return {
        "message": "Registration successful",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name
        }
    }
```

### Step 4: Create Login Endpoint

```python
@router.post("/login")
async def login(email: str, password: str, response: Response):
    """
    Login with sessions.
    """
    # 1. Find user
    user = get_user_by_email(email)

    # 2. Check password
    if not user or not check_password(password, user.password):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    # 3. Create session
    session_id = session_manager.create_session(
        str(user.id),
        {"email": user.email, "name": user.name}
    )

    # 4. Set cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=43200
    )

    return {"message": "Login successful"}
```

### Step 5: Protect Your Endpoints

```python
from fastapi import Cookie

async def get_current_user_session(session_id: str = Cookie(None)):
    """
    Get logged-in user from session.
    """
    # 1. Check if session ID was sent
    if not session_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    # 2. Get session data from Redis
    session_data = session_manager.get_session(session_id)

    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    # 3. Get user from database
    user_id = session_data.get("user_id")
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/profile")
async def get_profile(current_user = Depends(get_current_user_session)):
    """
    Protected endpoint using sessions.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name
    }
```

### Step 6: Logout Endpoint

```python
@router.post("/logout")
async def logout(response: Response, session_id: str = Cookie(None)):
    """
    Logout user.

    With sessions, we can actually delete the session!
    (With JWT, we can't - token stays valid until it expires)
    """
    # Delete session from Redis
    if session_id:
        session_manager.delete_session(session_id)

    # Clear cookie
    response.delete_cookie(key="session_id")

    return {"message": "Logged out successfully"}
```

### Step 7: Using Sessions from Frontend

**JavaScript example:**

```javascript
// Register (much simpler!)
async function register(email, password, name) {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',  // IMPORTANT: Send cookies
    body: JSON.stringify({ email, password, name })
  });

  return await response.json();
  // Cookie is saved automatically by browser!
}

// Login
async function login(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',  // Send cookies
    body: JSON.stringify({ email, password })
  });

  return await response.json();
}

// Get profile (no need to send token manually!)
async function getProfile() {
  const response = await fetch('/api/v1/profile', {
    credentials: 'include'  // Browser sends cookie automatically
  });

  return await response.json();
}

// Logout
async function logout() {
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include'
  });
  // Cookie is deleted by server
}
```

**Notice:** With sessions, frontend code is simpler! No need to manually manage tokens.

---

## What is OAuth? (Login with Google/GitHub)

### The Simple Idea

**OAuth** lets users login using their Google/Facebook/GitHub account instead of creating a new password.

### Why is This Good?

**For users:**
- ✅ No new password to remember
- ✅ Faster registration (no email confirmation)
- ✅ More secure (Google security > your security)

**For you (developer):**
- ✅ Less work (no email verification, password reset, etc.)
- ✅ More sign-ups (people trust Google)
- ✅ Get user's profile picture for free

### Real-Life Analogy

**OAuth is like using your passport to travel:**

```
Instead of getting a visa for every country...
→ You show your passport (Google account)
→ Countries trust your passport
→ You get in without extra paperwork
```

### How OAuth Works (Simple Steps)

```
1. User clicks "Login with Google" on your website

2. Your website redirects to Google
   "Hey Google, this person wants to login to my website"

3. User logs into Google (if not already)
   Google asks: "Allow MyWebsite to see your email and name?"
   User clicks "Yes"

4. Google redirects back to your website
   "Here's a special code for this user"

5. Your website sends that code to Google
   "Can I get this user's info?"

6. Google sends back user's info
   {
     "email": "john@gmail.com",
     "name": "John Doe",
     "picture": "https://..."
   }

7. Your website creates account or logs in existing user
```

### Implementing OAuth with Google

#### Step 1: Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Google+ API"
4. Create "OAuth 2.0 credentials"
5. You'll get:
   - **Client ID**: `123456789.apps.googleusercontent.com`
   - **Client Secret**: `abc123xyz456`

#### Step 2: Install Library

```bash
pip install authlib httpx
```

#### Step 3: Configure in Your App

```python
# .env file
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-secret-here
```

#### Step 4: Create OAuth Endpoints

```python
from authlib.integrations.starlette_client import OAuth

# Setup OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id='your-google-client-id',
    client_secret='your-google-secret',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


@router.get("/auth/google/login")
async def google_login(request):
    """
    Step 1: Redirect user to Google.

    When user clicks "Login with Google", send them here.
    """
    # This will redirect to Google's login page
    return await oauth.google.authorize_redirect(
        request,
        'http://localhost:8000/api/v1/auth/google/callback'  # Where Google sends user back
    )


@router.get("/auth/google/callback")
async def google_callback(request):
    """
    Step 2: Google sends user back here with their info.
    """
    # Get user's info from Google
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')

    # user_info looks like:
    # {
    #   "email": "john@gmail.com",
    #   "name": "John Doe",
    #   "picture": "https://lh3.googleusercontent.com/...",
    #   "sub": "123456789"  # Google's ID for this user
    # }

    # Check if user exists
    user = get_user_by_email(user_info['email'])

    if not user:
        # Create new user
        user = create_user_in_database(
            email=user_info['email'],
            name=user_info['name'],
            google_id=user_info['sub'],  # Save Google ID
            avatar=user_info['picture'],
            password=hash_password(secrets.token_urlsafe(32))  # Random password (they won't use it)
        )

    # Create session or JWT (your choice)
    token = create_token(str(user.id))

    # Redirect to frontend with token
    return RedirectResponse(
        url=f'http://localhost:3000/auth/success?token={token}'
    )
```

#### Step 5: Frontend Button

```html
<!-- Simple HTML button -->
<button onclick="window.location.href='/api/v1/auth/google/login'">
  Login with Google
</button>
```

```javascript
// Or in React/Vue
function LoginPage() {
  const loginWithGoogle = () => {
    window.location.href = '/api/v1/auth/google/login';
  };

  return (
    <button onClick={loginWithGoogle}>
      Login with Google
    </button>
  );
}
```

**That's it!** OAuth is actually quite simple once you understand the flow.

---

## Security Tips (Keep Your App Safe)

### 1. Always Use HTTPS in Production

❌ **Bad:** `http://mywebsite.com` (data sent as plain text)
✅ **Good:** `https://mywebsite.com` (data is encrypted)

**Why?** Without HTTPS, hackers can see passwords and tokens.

### 2. Never Store Passwords as Plain Text

❌ **Bad:**
```python
user.password = "mypassword123"  # NEVER DO THIS
```

✅ **Good:**
```python
user.password = hash_password("mypassword123")  # Always hash
```

### 3. Use HttpOnly Cookies

❌ **Bad:**
```python
response.set_cookie("session_id", session_id)  # JavaScript can steal this
```

✅ **Good:**
```python
response.set_cookie("session_id", session_id, httponly=True)  # JavaScript can't access
```

**Why?** Protects against XSS attacks (malicious JavaScript).

### 4. Don't Store JWT in localStorage

❌ **Bad:**
```javascript
localStorage.setItem('token', jwt);  // Can be stolen by XSS
```

✅ **Good:**
```javascript
// Option 1: Store in memory (lost on page refresh, but safer)
let token = null;

// Option 2: Use HttpOnly cookie (set by server)
// No JavaScript access needed!
```

### 5. Make Tokens Expire

❌ **Bad:**
```python
# Token never expires - if stolen, works forever
token = create_token(user_id)
```

✅ **Good:**
```python
# Token expires in 15 minutes
token = create_token(user_id, expires_in_minutes=15)
```

### 6. Require Strong Passwords

❌ **Bad:** Allow `password = "123"`

✅ **Good:**
```python
# Check password strength
def validate_password(password):
    if len(password) < 8:
        raise Error("Password must be at least 8 characters")

    if not any(char.isupper() for char in password):
        raise Error("Password must have uppercase letter")

    if not any(char.isdigit() for char in password):
        raise Error("Password must have a number")
```

### 7. Rate Limit Login Attempts

**Why?** Hackers try thousands of passwords per second.

```python
# Allow only 5 login attempts per minute
from slowapi import Limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(email, password):
    # ... login code ...
```

### 8. Never Put Sensitive Data in JWT

❌ **Bad:**
```python
token = create_token({
    "user_id": user.id,
    "credit_card": user.credit_card,  # NEVER!
    "ssn": user.ssn                   # NEVER!
})
```

✅ **Good:**
```python
token = create_token({
    "user_id": user.id,
    "email": user.email,
    "role": user.role
})
# Keep sensitive data in database only
```

### 9. Log Security Events

```python
# Log all login attempts
logger.info(f"Login attempt: {email} from {ip_address}")

# Log failed attempts
logger.warning(f"Failed login: {email} from {ip_address}")

# Log suspicious activity
if failed_attempts > 10:
    logger.error(f"Possible attack: {email} from {ip_address}")
```

---

## Common Mistakes and How to Avoid Them

### Mistake 1: Not Checking if Email Already Exists

❌ **Problem:**
```python
@router.post("/register")
async def register(email, password, name):
    # No check - creates duplicate users!
    user = create_user(email, password, name)
```

✅ **Solution:**
```python
@router.post("/register")
async def register(email, password, name):
    # Check first
    if get_user_by_email(email):
        raise HTTPException(409, "Email already registered")

    user = create_user(email, password, name)
```

### Mistake 2: Returning Too Much User Data

❌ **Problem:**
```python
@router.get("/profile")
async def get_profile(user):
    # Returns everything including hashed password!
    return user
```

✅ **Solution:**
```python
@router.get("/profile")
async def get_profile(user):
    # Only return what's needed
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name
        # DON'T include: password, internal IDs, etc.
    }
```

### Mistake 3: Not Handling Expired Tokens

❌ **Problem:**
```python
# Decode without checking expiration
data = jwt.decode(token, verify=False)  # DANGEROUS!
```

✅ **Solution:**
```python
# Always verify everything
try:
    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
except jwt.ExpiredSignatureError:
    raise HTTPException(401, "Token expired - please login again")
except jwt.JWTError:
    raise HTTPException(401, "Invalid token")
```

### Mistake 4: Allowing Weak Passwords

❌ **Problem:**
```python
# Accepts "123" as password
user.password = hash_password(password)
```

✅ **Solution:**
```python
def validate_password(password):
    if len(password) < 8:
        raise HTTPException(400, "Password too short (minimum 8 characters)")

    # Add more checks as needed
    return True

# Use it
validate_password(password)
user.password = hash_password(password)
```

### Mistake 5: Not Logging Out Properly

❌ **Problem (with JWT):**
```javascript
// Just delete token from client - but token is still valid!
localStorage.removeItem('token');
```

✅ **Solution:**
```javascript
// Need to blacklist token on server
await fetch('/api/v1/auth/logout', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
});

// Server adds token to blacklist
localStorage.removeItem('token');
```

✅ **Better: Use refresh tokens:**
```python
# Short-lived access token (15 min)
access_token = create_token(user_id, expires_in_minutes=15)

# Long-lived refresh token (7 days)
refresh_token = create_token(user_id, expires_in_days=7)

# Store refresh token in database - can be revoked anytime
```

### Mistake 6: Forgetting CORS Configuration

❌ **Problem:**
```python
# No CORS setup - frontend can't access API
app = FastAPI()
```

✅ **Solution:**
```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Summary: Quick Reference

### When to Use What

| Scenario | Use This |
|----------|----------|
| Building a mobile app | JWT ✅ |
| Simple website | Sessions ✅ |
| Need to logout users instantly | Sessions ✅ |
| Want social login (Google, etc.) | OAuth ✅ |
| Banking/healthcare app | Sessions + 2FA ✅ |
| Microservices | JWT ✅ |
| Just learning | Sessions (simpler!) ✅ |

### Key Takeaways

1. **JWT**: Like a boarding pass - has all your info, works anywhere, can't be cancelled
2. **Sessions**: Like a gym locker - server keeps your info, you get a key, can be locked anytime
3. **OAuth**: Like using your passport - login with Google instead of creating new account

4. **Security**:
   - Always hash passwords (use bcrypt)
   - Always use HTTPS in production
   - Make tokens expire
   - Use HttpOnly cookies when possible

5. **Best Practice**:
   - Start simple (sessions)
   - Add JWT when you need it (mobile app)
   - Add OAuth for convenience (Google login)

---

## Need Help?

If you're still confused about any topic:

1. **JWT**: Think of it as a movie ticket with your info printed on it
2. **Sessions**: Think of it as a coat check ticket - they keep your coat, you get a number
3. **OAuth**: Think of it as using your passport instead of getting a new visa for each country

**Remember:** Security is like locking your house:
- Good enough is better than nothing
- Don't leave obvious vulnerabilities (weak passwords, no HTTPS)
- Keep improving as you learn

Good luck! 🚀
