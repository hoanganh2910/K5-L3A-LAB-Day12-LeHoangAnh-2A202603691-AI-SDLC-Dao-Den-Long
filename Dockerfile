FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Headless, soak, and pytest do not need a display.
# The windowed game and the benchmark need a desktop; run those on the host.
CMD ["python3", "-m", "pytest", "-q"]
