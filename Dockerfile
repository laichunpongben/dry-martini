FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the martini package directory
COPY martini /app/martini

EXPOSE 6010

# Launch via the package path
CMD ["uvicorn", "martini.main:app", "--host", "0.0.0.0", "--port", "6010"]
