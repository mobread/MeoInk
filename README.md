# MeoInk

Barebones e-ink display controller for Inky Impression 800×480 on rpzero01.

## Services

- **pve01** — `meoink-server.service` (FastAPI, port 8183)
- **rpzero01** — `meoink-client.service` (Flask, port 5000)

## Server dev

```bash
cd server
venv/bin/uvicorn main:app --reload --port 8183
```

## Run tests

```bash
cd server
venv/bin/pytest tests/ -v
```
