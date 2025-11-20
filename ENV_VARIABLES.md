# Environment Variables для DevOps

## Обов'язкові змінні

### API Keys (завжди потрібні)
```env
AHREFS_API_TOKEN=your_token
SIMILAR_WEB_KEY=your_key
```

### PostgreSQL Database (для production)
```env
DB_TYPE=postgresql
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

## Приклад Docker Run

```bash
docker run -d \
  --name seo-backend \
  -p 8000:8000 \
  -e AHREFS_API_TOKEN=xxx \
  -e SIMILAR_WEB_KEY=xxx \
  -e DB_TYPE=postgresql \
  -e POSTGRES_HOST=postgres_host \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=seo_checker \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  seo-backend:latest
```

## Приклад Docker Compose

```yaml
services:
  seo-backend:
    image: seo-backend:latest
    ports:
      - "8000:8000"
    environment:
      - AHREFS_API_TOKEN=xxx
      - SIMILAR_WEB_KEY=xxx
      - DB_TYPE=postgresql
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=seo_checker
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
```

## Альтернативні назви змінних

Код також підтримує альтернативні назви (для зворотної сумісності):

```env
DB_HOST=localhost      # або POSTGRES_HOST
DB_PORT=5432          # або POSTGRES_PORT
DB_NAME=seo_checker   # або POSTGRES_DB
DB_USER=postgres      # або POSTGRES_USER
DB_PASSWORD=password  # або POSTGRES_PASSWORD
```

**Примітка:** Якщо вказані обидві версії, пріоритет має `POSTGRES_*`

## Для SQLite (локальна розробка)

```env
DB_TYPE=sqlite
SQLITE_DB_PATH=/app/ahrefs_data.db
```

## Таблиця всіх змінних

| Змінна | Обов'язкова? | За замовчуванням | Опис |
|--------|--------------|------------------|------|
| `AHREFS_API_TOKEN` | **Так** | - | Ahrefs API токен |
| `SIMILAR_WEB_KEY` | **Так** | - | SimilarWeb API ключ |
| `DB_TYPE` | Ні | `sqlite` | Тип БД: `sqlite` або `postgresql` |
| `POSTGRES_HOST` | Так (PostgreSQL) | `localhost` | Хост PostgreSQL |
| `POSTGRES_PORT` | Так (PostgreSQL) | `5432` | Порт PostgreSQL |
| `POSTGRES_DB` | Так (PostgreSQL) | `seo_checker` | Назва бази даних |
| `POSTGRES_USER` | Так (PostgreSQL) | `postgres` | Користувач БД |
| `POSTGRES_PASSWORD` | Так (PostgreSQL) | - | Пароль БД |

## Перевірка

Після запуску контейнера перевір:

```bash
# Перевір логи
docker logs seo-backend

# Перевір health endpoint
curl http://localhost:8000/health

# Має повернути: {"status":"healthy"}
```

## База даних

База даних автоматично ініціалізується при першому запуску. Таблиці створюються автоматично.

Якщо потрібно створити базу вручну:

```sql
CREATE DATABASE seo_checker;
```

