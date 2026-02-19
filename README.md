# Configurable TN Lot Intelligence Pipeline (MVP Scaffold)

Sistema Python para procesar un CSV de propiedades en TN, navegar fuentes públicas legalmente, estructurar datos por campo configurable y calcular `target_build_sqft`, `arv_estimate_usd` y `max_offer_usd` mediante estrategias enchufables.

> ⚠️ Estado actual del scaffold: `BrowsingAgent` está en modo stub (no hace scraping real todavía).
> Para evitar datos inventados, devuelve `UNKNOWN` + warning `BROWSING_AGENT_STUB_NO_LIVE_EXTRACTION`.

## Guardrails / Compliance

- No bypass de login/CAPTCHA/paywalls.
- No stealth o evasión anti-bot.
- Si una fuente se bloquea: warning + `UNKNOWN`.
- Trazabilidad por campo con fuente y evidencia.

## Input CSV

Columnas mínimas:
- `property_id` (recomendado)
- `address_line1` (requerido)
- `city` (requerido)
- `state` (default `TN`)
- `zip` (opcional)
- `county` (opcional)

## Configuración

- `config/fields.yaml`: columnas a producir, validadores, dependencias y hints de extracción.
- `config/calculations.yaml`: `target_cap_sqft`, estrategia ARV y MAO.
- `config/sources.yaml`: prioridad de fuentes por campo y overrides por jurisdicción.

## Plugins

### ARV
Agregar un módulo en `app/calculations/strategies/` y registrar:

```python
from app.registry import register_arv

@register_arv("my_arv")
def my_arv(*, property_data, findings, params):
    ...
```

### MAO

```python
from app.registry import register_mao

@register_mao("my_mao")
def my_mao(*, arv_value, property_data, params):
    ...
```

Luego cambiar `config/calculations.yaml` sin tocar `app/pipeline.py`.

## Ejecución

```bash
python -m app.pipeline \
  --input data/input_properties.csv \
  --output data/output_results.csv \
  --fields-config config/fields.yaml \
  --calc-config config/calculations.yaml \
  --sources-config config/sources.yaml \
  --cache-db data/cache.sqlite
```

### Logs (para debugging)

```bash
python -m app.pipeline ... --log-level DEBUG
```

### Forzar recálculo (sin cache)

```bash
python -m app.pipeline ... --no-cache
```

## Cache

La cache usa clave `(property_key, config_hash)` en SQLite (`data/cache.sqlite`).
Si corres dos veces la misma propiedad con igual config, reutiliza resultado anterior (cache hit).

## Tests

```bash
pytest -q
```

Incluye tests para:
- parse/validación de config,
- cap de `target_build_sqft` a 1600,
- fórmula MAO,
- registry de plugins.
