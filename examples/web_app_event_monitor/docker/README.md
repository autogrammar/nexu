# 🐳 Skonteneryzowany Ekosystem Telemetrii Nexu + Markpact

Ten katalog zawiera kompletną konfigurację wielodockerową pozwalającą na uruchomienie rozproszonego ekosystemu monitoringu za pomocą **Docker Compose**.

---

## 1. Jak to działa?

1. **Jednolity Dockerfile (`Dockerfile`)**:
   Zaprojektowaliśmy sparametryzowany Dockerfile, który pobiera argument `SERVICE_NAME`. Buduje on obraz kontenera, instaluje runtime `markpact`, kopiuje specyfikację README mikroserwisu i w locie przygotowuje piaskownicę.
2. **Orkiestracja Compose (`docker-compose.yml`)**:
   Spina wszystkie 3 usługi w odizolowaną sieć wirtualną `monitor-network`, przekazuje zmienne środowiskowe oraz definiuje reguły sprawdzania zdrowia kontenerów (`healthcheck`).

---

## 2. Instrukcja Uruchomienia

Aby zbudować i uruchomić cały rozproszony ekosystem w kontenerach Docker, wykonaj w terminalu poniższe polecenia:

```bash
# Wejdź do katalogu konfiguracyjnego Docker
cd /home/tom/github/semcod/nexu/examples/web_app_event_monitor/docker/

# Zbuduj obrazy i uruchom kontenery w tle
docker compose up --build -d
```

### Sprawdzenie statusu kontenerów:
```bash
docker compose ps
```

---

## 3. Podgląd Działania Ekosystemu

Gdy kontenery Docker są uruchomione, porty są wystawione na Twoim lokalnym hoście (`localhost`):

* 🖥️ **Ecosystem Dashboard UI**: [http://localhost:9103/](http://localhost:9103/)
* 📊 **Telemetry Metrics Endpoint**: [http://localhost:9101/metrics](http://localhost:9101/metrics)
* 🚨 **System Rule Alerts History**: [http://localhost:9102/alerts](http://localhost:9102/alerts)

---

## 4. Wyłączenie Środowiska

Aby zatrzymać i wyczyścić kontenery oraz utworzone sieci wirtualne, uruchom:

```bash
docker compose down
```
