FROM python:3.11-slim

WORKDIR /app

# System deps for tree-sitter compilation + C++ analyzer
RUN apt-get update && apt-get install -y \
    gcc g++ git curl make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Compile the C++ analyzer if present, then start the API
CMD ["sh", "-c", "if [ -d /app/analyzer ] && [ -f /app/analyzer/Makefile ]; then make -C /app/analyzer && echo 'C++ analyzer compiled'; fi && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
