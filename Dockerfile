FROM docker.arvancloud.ir/python:3.11-slim 

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create user
RUN useradd -m -u 1000 appuser

# Install Python dependencies from PyPI
COPY --chown=appuser:appuser requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -i https://package-mirror.liara.ir/repository/pypi/simple

# Application code
COPY --chown=appuser:appuser ./app /app/app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]