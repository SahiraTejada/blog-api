# Create ENV
    # For Linux / Mac OS
        python3 -m venv venv
    # Start ENV
        python  -m venv venv

# Start ENV
    # For Linux / Mac OS
        source venv/bin/activate
    # Start ENV
        venv\Scripts\Activate.ps1

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
    
# Run Migrations
    alembic revision --autogenerate -m "updates on database" &&
    alembic upgrade head


