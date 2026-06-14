FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for caching benefits
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend project files into the /app/backend subdirectory
# This preserves the "backend.app" module namespace
COPY . /app/backend

# Set up environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:////app/backend/infrawatch.db

EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
