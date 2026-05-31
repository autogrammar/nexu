# Wieloetapowy (multi-stage) Dockerfile dla kapsuł Markpact w ekosystemie Nexu
FROM python:3.11-slim

WORKDIR /app

# Instalacja podstawowych narzędzi systemowych
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalacja runtime markpact
RUN pip install --no-cache-dir markpact

# Argument określający, który serwis budujemy (analytics, alerts, dashboard)
ARG SERVICE_NAME

# Kopiowanie specyfikacji README serwisu
COPY services/${SERVICE_NAME}/README.md ./README.md

# Markpact automatycznie analizuje specyfikację, tworzy piaskownicę plikową,
# instaluje wymagane zależności i przygotowuje aplikację do startu.
RUN markpact README.md --dry-run

# Uruchomienie mikroserwisu przez markpact
ENTRYPOINT ["markpact", "README.md"]
