FROM python:3.9-slim as base
WORKDIR /app

COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copy all application code into the container
COPY api /app
EXPOSE 80

FROM base as dev
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
