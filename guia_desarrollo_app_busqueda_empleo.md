# Guía de Desarrollo: Aplicación Web para Búsqueda de Empleo con Scraping y Matching

Esta guía proporciona un plan detallado y secuencial para desarrollar una aplicación web full-stack que realiza scraping ético de portales de empleo, matching de ofertas basadas en el perfil del aspirante y generación de listados relevantes. La aplicación respeta términos de servicio, prioriza la privacidad y usa prácticas éticas en el scraping (por ejemplo, no sobrecargar servidores, usar delays y headers). 

**Consideraciones Generales:**
- **Legalidad y Ética:** Siempre verifica los términos de servicio de los portales (LinkedIn prohíbe scraping automatizado sin API; usa APIs oficiales si disponible, como LinkedIn API o Indeed API. Para este ejemplo, usaremos Scrapy con configuración ética para sitios permisivos como Indeed o InfoJobs). Implementa rate limiting, user-agents rotativos y proxies si es necesario. No almacenes datos sensibles sin consentimiento. Cumple con GDPR/CCPA para privacidad.
- **Estructura del Proyecto:** Crea un directorio raíz `job-search-app` con subdirectorios: `backend/` (Flask), `frontend/` (Astro), `database/` (scripts SQL), `tests/`, `docs/`. Usa Git para versionado.
- **Entorno:** Python 3.10+, Node.js 18+. Manejo de entornos con `.env` y `python-dotenv`.
- **Mejores Prácticas:** Código modular, logging con `logging` module, manejo de errores con try-except, pruebas unitarias.

## 1. Preparación del Entorno

**Objetivo:** Configurar el entorno de desarrollo, instalar dependencias y preparar la estructura base del proyecto.

**Tareas Específicas:**
- Crear el directorio del proyecto y clonar/inicializar Git.
- Instalar Python y Node.js si no están disponibles.
- Configurar virtual environment para Python y manejar paquetes con pip/requirements.txt.
- Instalar PostgreSQL local (usa Docker para simplicidad).
- Configurar variables de entorno (.env) para claves API, DB credentials, etc.

**Requisitos Previos:**
- Python 3.10+, Node.js 18+, PostgreSQL 14+, Git.
- Dependencias globales: `pip install virtualenv`, `npm install -g yarn` (opcional para Astro).

**Comandos y Snippets:**
```bash
# Crear proyecto
mkdir job-search-app
cd job-search-app
git init

# Backend: Virtual env
python -m venv backend/venv
source backend/venv/bin/activate  # En Linux/Mac
pip install flask sqlalchemy psycopg2-binary flask-jwt-extended scrapy beautifulsoup4 requests lxml python-dotenv fuzzywuzzy python-levenshtein nltk spacy pytest
pip freeze > backend/requirements.txt

# Frontend: Astro
cd frontend
npm create astro@latest . -- --template minimal
npm install tailwindcss @astrojs/tailwind
npm run dev  # Para desarrollo

# Base de datos: Docker para Postgres
docker run --name postgres-db -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=jobdb -p 5432:5432 -d postgres:14

# .env en raíz
echo "DB_URL=postgresql://postgres:secret@localhost:5432/jobdb
SECRET_KEY=tu_clave_secreta
LINKEDIN_API_KEY=opcional" > .env
```

- [ ] Entorno Python configurado y dependencias instaladas.
- [ ] Proyecto Astro inicializado con Tailwind.
- [ ] PostgreSQL corriendo localmente via Docker.
- [ ] Archivo .env creado con variables seguras.

## 2. Configuración del Backend (Flask)

**Objetivo:** Desarrollar el servidor Flask con API RESTful, blueprints modulares, autenticación JWT y conexión a DB.

**Tareas Específicas:**
- Estructura: `backend/app.py` (main), `backend/models.py` (SQLAlchemy), `backend/routes/` (blueprints para auth, profiles, scraping), `backend/scrapers/` (Scrapy spiders), `backend/utils/` (matching logic).
- Configurar SQLAlchemy para PostgreSQL.
- Implementar autenticación básica con JWT.
- Rutas clave: `/auth/register`, `/auth/login`, `/profile/upload` (POST JSON con habilidades, experiencia, ubicación), `/jobs/search` (GET con params para matching).

**Requisitos Previos:**
- Dependencias de backend instaladas.
- .env cargado.

**Comandos y Snippets:**
```python
# backend/app.py
from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from models import db
import os

load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL')
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
jwt = JWTManager(app)

# Blueprints
from routes.auth import auth_bp
from routes.jobs import jobs_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(jobs_bp, url_prefix='/jobs')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
```

```python
# backend/models.py (Ejemplo tabla perfiles)
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Usa bcrypt
    profile = db.relationship('Profile', backref='user', uselist=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skills = db.Column(db.Text)  # JSON string: ["Python", "Flask"]
    experience = db.Column(db.Text)
    location = db.Column(db.String(100))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    company = db.Column(db.String(100))
    description = db.Column(db.Text)
    url = db.Column(db.String(500))
    scraped_at = db.Column(db.DateTime)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))  # Asociado a matching
```

- [ ] Estructura de backend creada con blueprints.
- [ ] Modelos de DB definidos y migración inicial (db.create_all()).
- [ ] Autenticación JWT implementada en rutas auth.
- [ ] Logging configurado (usa logging.basicConfig(level=logging.INFO)).

## 3. Implementación del Scraping y Matching

**Objetivo:** Desarrollar el módulo de scraping ético y lógica de matching de keywords.

**Tareas Específicas:**
- Usar Scrapy para spiders asíncronos en Indeed/InfoJobs (ej: buscar por keywords como "desarrollador Python Bogotá").
- Headers: User-Agent rotativos, delays (time.sleep(2-5s)).
- Matching: Usa fuzzywuzzy para similitud de strings en skills/experience vs job description. Umbral >70%.
- Almacenar resultados en DB, con logs de errores (e.g., bloqueos por IP).
- Ruta `/jobs/search` ejecuta scraping si cache <24h, sino usa DB.

**Requisitos Previos:**
- Scrapy instalado.
- Conocimiento de selectores CSS para sitios objetivo (inspecciona con DevTools).

**Comandos y Snippets:**
```python
# backend/scrapers/indeed_spider.py (Scrapy project: scrapy startproject scrapers)
import scrapy
import time
from scrapy.crawler import CrawlerProcess

class IndeedSpider(scrapy.Spider):
    name = 'indeed'
    start_urls = ['https://www.indeed.com/jobs?q=python&l=Bogotá']  # Dinámico via params

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'DOWNLOAD_DELAY': 3,  # Delay ético
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
    }

    def parse(self, response):
        for job in response.css('div.job_seen_beacon'):
            yield {
                'title': job.css('h2.jobTitle::text').get(),
                'company': job.css('.companyName::text').get(),
                'description': job.css('.summary::text').get(),
                'url': response.urljoin(job.css('a::attr(href)').get()),
            }
            time.sleep(2)  # Delay adicional

# En ruta jobs: Ejecutar spider
process = CrawlerProcess()
process.crawl(IndeedSpider)
process.start()
```

```python
# backend/utils/matching.py
from fuzzywuzzy import fuzz
import nltk
nltk.download('punkt')  # Para tokenización básica

def match_profile_to_jobs(profile_skills, profile_exp, location, jobs):
    matches = []
    for job in jobs:
        score_skills = max(fuzz.ratio(skill.lower(), job['description'].lower()) for skill in profile_skills)
        score_exp = fuzz.partial_ratio(profile_exp.lower(), job['description'].lower())
        score_loc = 100 if location.lower() in job['description'].lower() else 0
        total_score = (score_skills + score_exp + score_loc) / 3
        if total_score > 70:
            matches.append({'job': job, 'score': total_score})
    return sorted(matches, key=lambda x: x['score'], reverse=True)
```

- [ ] Spider de Scrapy para al menos un portal (Indeed) implementado y probado.
- [ ] Lógica de matching con fuzzywuzzy integrada.
- [ ] Manejo de errores: Try-except para requests fallidas, logging de bloqueos.
- [ ] Cache en DB para evitar rescraping frecuente.

## 4. Integración con Base de Datos

**Objetivo:** Configurar y normalizar tablas para perfiles, jobs y logs.

**Tareas Específicas:**
- Tablas: Users, Profiles, Jobs (como en models.py), Logs (para scraping errors).
- Migraciones: Usa Flask-Migrate para cambios futuros.
- Insertar datos scraped en Jobs, asociar matches a Profiles.

**Requisitos Previos:**
- SQLAlchemy configurado.

**Comandos y Snippets:**
```python
# En app.py, agregar Flask-Migrate
from flask_migrate import Migrate
migrate = Migrate(app, db)

# Comando: flask db init, flask db migrate, flask db upgrade
```

```sql
-- Script inicial database/schema.sql (ejecutar con psql)
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10),
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- [ ] Tablas creadas y normalizadas (1NF+).
- [ ] Integración: Guardar perfiles y jobs post-matching.
- [ ] Logs de scraping/errors insertados automáticamente.

## 5. Desarrollo del Frontend (Astro)

**Objetivo:** Crear interfaz responsive con Astro, integrando API backend.

**Tareas Específicas:**
- Páginas: `/` (login/registro), `/profile` (formulario: skills, exp, location), `/dashboard` (listado jobs con scores, botones apply/export PDF via jsPDF).
- Usar fetch para API calls (e.g., POST /profile/upload).
- Responsive con Tailwind: Grid para jobs, forms styled.

**Requisitos Previos:**
- Astro con Tailwind instalado.

**Comandos y Snippets:**
```astro
--- src/pages/profile.astro ---
---
// Fetch o POST a backend
const response = await fetch('http://localhost:5000/profile/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ skills: ['Python'], experience: '5 años', location: 'Bogotá' })
});
const profile = await response.json();
---
<html lang="es">
<head>
  <title>Perfil</title>
</head>
<body class="bg-gray-100">
  <form class="max-w-md mx-auto p-4 bg-white">
    <input type="text" placeholder="Habilidades (JSON)" class="w-full p-2 border">
    <input type="text" placeholder="Experiencia" class="w-full p-2 border mt-2">
    <input type="text" placeholder="Ubicación" class="w-full p-2 border mt-2">
    <button type="submit" class="w-full bg-blue-500 text-white p-2 mt-4">Subir Perfil</button>
  </form>
</body>
</html>
```

```javascript
// src/components/JobList.astro - Export PDF
import jsPDF from 'jspdf';
const exportPDF = (jobs) => {
  const doc = new jsPDF();
  jobs.forEach(job => doc.text(`${job.title} - ${job.score}%`, 10, 10));
  doc.save('jobs.pdf');
};
```

- [ ] Páginas login, profile y dashboard implementadas.
- [ ] Integración API: Fetch con JWT auth.
- [ ] Estilos Tailwind responsive aplicados.
- [ ] Funcionalidad export (PDF/email via backend o client-side).

## 6. Pruebas

**Objetivo:** Implementar y ejecutar pruebas unitarias y e2e.

**Tareas Específicas:**
- Backend: Pytest para rutas, models, matching (mock scraping).
- Frontend: Pruebas e2e con Playwright (instala via npm).
- Pruebas de integración: Scraping ético, DB inserts.

**Requisitos Previos:**
- Pytest y Playwright instalados.

**Comandos y Snippets:**
```bash
# Backend tests
pytest backend/tests/ -v

# Ejemplo test
# backend/tests/test_matching.py
import pytest
from utils.matching import match_profile_to_jobs

def test_matching():
    jobs = [{'description': 'Python developer'}]
    matches = match_profile_to_jobs(['Python'], '', '', jobs)
    assert len(matches) == 1
    assert matches[0]['score'] > 70
```

```bash
# Frontend e2e
npx playwright test
```

- [ ] Pruebas unitarias backend (>80% coverage).
- [ ] Pruebas e2e frontend (navegación, forms).
- [ ] Pruebas de scraping: Mock responses para evitar calls reales.

## 7. Despliegue Local y Pruebas Finales

**Objetivo:** Correr la app localmente, probar end-to-end y documentar.

**Tareas Específicas:**
- Backend: `python backend/app.py` (puerto 5000).
- Frontend: `npm run dev` (puerto 4321), proxy a backend.
- Pruebas: Registro, upload perfil, search jobs, ver matches.
- Docker opcional: Dockerfile para Flask y compose para stack (app + postgres).

**Comandos y Snippets:**
```yaml
# docker-compose.yml
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: jobdb
  app:
    build: ./backend
    ports:
      - "5000:5000"
    depends_on:
      - db
```

- [ ] App corriendo local: Backend + Frontend integrados.
- [ ] Pruebas manuales: Scraping exitoso, matching preciso, UI responsive.
- [ ] Logs revisados para errores.

## Troubleshooting Común

- **Scraping bloqueado:** Aumenta delays, usa proxies (e.g., Scrapy middleware), rota user-agents. Verifica robots.txt.
- **DB conexión falla:** Chequea .env, Docker running (`docker ps`), puerto 5432 libre.
- **JWT errors:** Verifica SECRET_KEY, tokens expirados (configura expiry).
- **CORS en frontend:** Instala flask-cors y habilita origins.
- **Dependencias faltantes:** `pip install -r requirements.txt`, `npm install`.
- **Legal: Si API oficial disponible, migra a ella (e.g., Indeed Publisher API).**

## Próximos Pasos para Producción

- **Despliegue:** Backend en Heroku (con Postgres add-on), Frontend en Vercel/Netlify. Usa Gunicorn para Flask.
- **Seguridad:** HTTPS, rate limiting (Flask-Limiter), encripta passwords (bcrypt).
- **Escalabilidad:** Celery para scraping asíncrono, Redis cache.
- **Monitoreo:** Sentry para errors, CI/CD con GitHub Actions.
- **Mejoras:** Integrar NLP avanzado (spaCy models), emails con SendGrid, mobile app.

Esta guía es autónoma; sigue los pasos secuencialmente. Para dudas, consulta docs oficiales (Flask, Scrapy, Astro).