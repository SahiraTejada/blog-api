# Create ENV
    # For Linux / Mac OS
        python3 -m venv .venv
    # For Windows
        python -m venv .venv

# Activate ENV
    # For Linux / Mac OS
        source .venv/bin/activate
    # For Windows PowerShell
        .venv\Scripts\Activate.ps1
    # For Windows CMD
        .venv\Scripts\activate.bat

# Run Mypy
    mypy .
    sudo rm -rf .mypy_cache/ && mypy . --ignore-missing-imports && pytest tests/ -v

# Clear mypy cache
    sudo rm -rf .mypy_cache/

# Stop ENV
    deactivate

# Install Dependencies
    pip install -r requirements.txt

# Update Dependencies
    pip freeze > requirements.txt

# Start Server
    uvicorn app.main:app --reload

# Run Tests
    pytest tests/ -v # Add --log-cli-level=INFO if want to see print and logs

# Sort Imports (fix automatically)
    isort . --profile black --line-length 127

# Check Import Sorting (validate only, exit with error if not sorted)
    isort . --profile black --line-length 127 --check-only --diff

# Flake 8

## Run flake8 linter
    flake8 app/ --max-line-length 127

## Automatically fix all whitespace errors
autopep8 --in-place --recursive --select=W291,W292,W293 .  

# Auto-fix all flake8 issues (whitespace, indentation, etc.)
autopep8 --in-place --recursive --max-line-length 127 .
autopep8 --in-place --recursive --aggressive --aggressive .

## Or fix the entire project with all errors
autopep8 --in-place --recursive --aggressive --aggressive .

# Run Migrations
    alembic revision --autogenerate -m "updates on database" &&
    alembic upgrade head


