# Player Service

Микросервис управляет учётными записями игроков, профилями Valorant,
статусами доступности и отзывами тиммейтов. Сервис предоставляет два
транспортных интерфейса:

- REST API для клиентских операций;
- gRPC API для взаимодействия с `matchmaking-service`.

Оба интерфейса запускаются в одном процессе, но слушают разные порты. По
умолчанию REST доступен на `8000`, а gRPC — на `50051`.

## Технологии

- Python 3.11+;
- FastAPI и Uvicorn;
- `grpcio` и Protocol Buffers;
- SQLAlchemy 2 в асинхронном режиме;
- asyncpg;
- PostgreSQL;
- Alembic;
- Pydantic Settings.

## Структура

```text
player-service/
├── app/
│   ├── api/                 # REST routers, DI и обработчики ошибок
│   ├── db/                  # Engine, sessions и SQLAlchemy-модели
│   ├── domain/              # Доменные сущности, enum и бизнес-правила
│   ├── grpc/                # gRPC servicer, server и protobuf-код
│   ├── repositories/        # Интерфейсы и SQLAlchemy-реализации
│   ├── schemas/             # REST request/response-схемы
│   ├── services/            # Прикладные сценарии
│   ├── config.py            # Конфигурация из окружения
│   └── main.py              # FastAPI-приложение и общий lifecycle
├── migrations/              # История миграций Alembic
├── scripts/                 # CLI-инструменты разработки
├── tests/                   # Автоматические тесты
├── .env.example
├── alembic.ini
└── pyproject.toml
```

Основное направление зависимостей:

```text
REST / gRPC
    ↓
Application services
    ↓
Repository interfaces
    ↓
SQLAlchemy repositories
    ↓
PostgreSQL
```

Транспортные слои не выполняют SQL-запросы напрямую. Благодаря интерфейсам
репозиториев прикладные сервисы можно использовать с fake-реализациями.

## Установка

Создать виртуальное окружение:

```powershell
python -m venv .venv
```

Установить сервис и runtime-зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Для разработки и повторной генерации protobuf-кода установить dev-зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Конфигурация

Для настройки конфигурации необходимо создать локальный `.env` на основе примера `.env.example`

Основные переменные:

| Переменная          | Назначение                      | Пример        |
|---------------------|---------------------------------|---------------|
| `APP_ENV`           | Окружение приложения            | `development` |
| `DEBUG`             | Режим отладки и Uvicorn reload  | `false`       |
| `LOG_LEVEL`         | Уровень логирования             | `INFO`        |
| `HTTP_HOST`         | Интерфейс REST-сервера          | `0.0.0.0`     |
| `HTTP_PORT`         | Порт REST-сервера               | `8000`        |
| `GRPC_HOST`         | Интерфейс gRPC-сервера          | `0.0.0.0`     |
| `GRPC_PORT`         | Порт gRPC-сервера               | `50051`       |
| `POSTGRES_USER`     | Пользователь PostgreSQL         | `player`      |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL               | `change-me`   |
| `POSTGRES_HOST`     | Адрес PostgreSQL                | `localhost`   |
| `POSTGRES_PORT`     | Порт PostgreSQL                 | `5432`        |
| `POSTGRES_DB`       | Имя базы данных                 | `player_db`   |
| `POSTGRES_SQL_ECHO` | Логирование SQLAlchemy-запросов | `false`       |

В Docker в `POSTGRES_HOST` обычно указывается имя сервиса PostgreSQL, а не
`localhost`.

## Миграции

PostgreSQL должен быть запущен и доступен по параметрам из `.env`.

Применить все миграции:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Проверить текущую ревизию:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

## Запуск REST и gRPC

Рекомендуемый запуск:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

Приложение запускается как Python-модуль. Не следует запускать
`app/main.py` напрямую: каталог `app/grpc` в таком режиме может перекрыть
установленную библиотеку `grpcio` при разрешении импортов.

Альтернативный запуск через Uvicorn:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI lifespan автоматически:

1. запускает gRPC-сервер на `GRPC_HOST:GRPC_PORT`;
2. передаёт управление Uvicorn и REST API;
3. при остановке завершает gRPC-сервер;
4. освобождает SQLAlchemy engine.

После запуска доступны:

- REST API: `http://localhost:8000`;
- Swagger UI: `http://localhost:8000/docs`;
- ReDoc: `http://localhost:8000/redoc`;
- gRPC: `localhost:50051`.

## REST API

| Метод   | Путь                                           | Назначение                        |
|---------|------------------------------------------------|-----------------------------------|
| `POST`  | `/api/v1/players`                              | Создать игрока и Valorant-профиль |
| `GET`   | `/api/v1/players/{player_id}`                  | Получить игрока и профиль         |
| `PATCH` | `/api/v1/players/{player_id}/valorant-profile` | Обновить профиль                  |
| `PATCH` | `/api/v1/players/{player_id}/status`           | Изменить статус                   |
| `POST`  | `/api/v1/players/{target_player_id}/reviews`   | Добавить отзыв                    |
| `GET`   | `/api/v1/players/{player_id}/reviews`          | Получить отзывы                   |
| `GET`   | `/health`                                      | Проверить HTTP-процесс            |

Подробные request/response-схемы доступны в Swagger UI.

## gRPC API

Общий контракт расположен в корне монорепозитория:

```text
proto/valorant_player_service.proto
```

Сервис реализует:

| RPC                              | Назначение                                    |
|----------------------------------|-----------------------------------------------|
| `GetValorantProfile`             | Получить объединённые данные игрока и профиля |
| `FindValorantPlayers`            | Найти игроков по matchmaking-фильтрам         |
| `CheckValorantPlayerEligibility` | Проверить одного игрока по фильтрам           |

Для поиска учитываются:

- исключаемый UUID игрока;
- диапазон рангов;
- статус доступности;
- минимальный рейтинг;
- регион;
- пересечение ролей;
- максимальное количество результатов.

Eligibility может возвращать следующие причины отказа:

```text
PLAYER_NOT_FOUND
RANK_OUT_OF_RANGE
STATUS_MISMATCH
RATING_BELOW_MINIMUM
REGION_MISMATCH
ROLE_MISMATCH
```

`player-service` уже предоставляет gRPC-сервер. Для полной межсервисной
связки `matchmaking-service` должен заменить `MockPlayerProvider` на настоящий
gRPC-клиент.

## CLI-инструменты

Все CLI-команды следует запускать из корня `player-service` через модульный
синтаксис `python -m`.

### Заполнение PostgreSQL тестовыми данными

Скрипт `scripts.seed_grpc_data` создаёт детерминированные данные для ручного
тестирования gRPC:

- игроков и Valorant-профили;
- реальные отзывы между созданными игроками;
- согласованные `teammate_rating` и `reviews_count`;
- разные регионы, ранги, роли и статусы;
- гарантированный пул игроков под стандартные фильтры клиента.

Перед запуском необходимо применить миграции.

Создать стандартный набор из 48 игроков:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_grpc_data
```

Создать 100 игроков:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_grpc_data --count 100
```

Минимально допустимое значение `--count` — `12`.

Скрипт идемпотентен относительно собственных данных: перед вставкой он удаляет
только игроков с Riot ID, начинающимся с `grpc-test-`. Остальные записи базы не
изменяются. UUID создаются детерминированно, поэтому повторный запуск формирует
тот же набор идентификаторов.

После завершения скрипт выводит UUID стандартного тестового игрока. Этот же UUID
уже используется клиентом по умолчанию.

### Имитация gRPC-клиента другого сервиса

Сначала запустить Player Service:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

Затем в другом терминале вызвать все три RPC:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client
```

Ответы выводятся как форматированный JSON.

Вызвать только получение профиля:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client --rpc get
```

Вызвать только поиск кандидатов:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client --rpc find
```

Вызвать только eligibility-проверку:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client --rpc check
```

Передать UUID конкретного игрока:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client `
  --rpc get `
  --player-id 00000000-0000-0000-0000-000000000000
```

Поиск с собственными фильтрами:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client `
  --rpc find `
  --min-rank GOLD_1 `
  --max-rank DIAMOND_3 `
  --status READY_TO_PLAY `
  --region EU `
  --min-rating 4.2 `
  --roles CONTROLLER SENTINEL `
  --limit 20
```

Проверка отрицательного eligibility-сценария:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client `
  --rpc check `
  --min-rank RADIANT `
  --max-rank RADIANT `
  --status IN_GAME `
  --region NA `
  --min-rating 5.0 `
  --roles DUELIST
```

Подключение к другому адресу gRPC-сервера:

```powershell
.\.venv\Scripts\python.exe -m scripts.grpc_client `
  --address player-service:50051
```

Основные параметры клиента:

| Параметр       | Значение по умолчанию |
|----------------|-----------------------|
| `--address`    | `localhost:50051`     |
| `--rpc`        | `all`                 |
| `--min-rank`   | `GOLD_1`              |
| `--max-rank`   | `PLATINUM_3`          |
| `--status`     | `READY_TO_PLAY`       |
| `--min-rating` | `4.0`                 |
| `--region`     | `EU`                  |
| `--roles`      | `CONTROLLER`          |
| `--limit`      | `10`                  |
| `--timeout`    | `5.0` секунд          |

### Повторная генерация protobuf-кода

Установить dev-зависимости и запустить генератор:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m scripts.generate_grpc
```

Генератор читает общий `.proto` и обновляет:

```text
app/grpc/generated/valorant_player_service_pb2.py
app/grpc/generated/valorant_player_service_pb2_grpc.py
```

Сгенерированные файлы не следует редактировать вручную.

## Тесты

Запустить весь набор тестов:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py"
```
