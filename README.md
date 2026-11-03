# Restaurant API

REST API для ресторана: гость смотрит меню, бронирует стол и делает заказ,
кухня и официант меняют статус заказа.

## Запуск

```bash
python3 -m uvicorn main:app --reload
```

Интерактивная документация: http://127.0.0.1:8000/docs

## Токен сотрудника

`POST /api/v1/menu` и `PATCH /api/v1/orders/{id}/status` требуют заголовок
`Authorization: Bearer <token>`. Токен задаётся переменной окружения
`STAFF_TOKEN` (по умолчанию `dev-staff-token` — только для разработки).

## Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/v1/menu?category=&available=` | Меню (`available=true` по умолчанию) |
| POST | `/api/v1/menu` | Создание пункта меню (нужен токен сотрудника) |
| GET | `/api/v1/tables` | Список столов |
| GET/POST | `/api/v1/reservations` | Список / создание брони |
| GET/DELETE | `/api/v1/reservations/{id}` | Бронь / отмена брони |
| GET/POST | `/api/v1/orders` | Список / создание заказа |
| GET | `/api/v1/orders/{id}` | Заказ |
| PATCH | `/api/v1/orders/{id}/status` | Статус заказа (нужен токен сотрудника) |

Статусы заказа: `new`, `preparing`, `ready`, `served`, `cancelled`.
Время — ISO 8601, длительность брони по умолчанию 2 часа.

## Ошибки

Единый формат:

```json
{"error": {"code": "...", "message": "..."}}
```

## Тесты

```bash
python3 -m pytest
```
