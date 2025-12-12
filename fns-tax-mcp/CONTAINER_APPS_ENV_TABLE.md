# Таблица переменных окружения для Container Apps

## Обязательные переменные

| Переменная | Тип | Обязательность | Значение по умолчанию | Описание |
|-----------|-----|----------------|----------------------|----------|
| `FNS_MODE` | rawEnv | ✅ Обязательна | `test` | Режим работы: `test` или `prod` |
| `FNS_API_TOKEN` | secretEnv | ✅ Обязательна | - | Токен от api-fns.ru |
| `PORT` | rawEnv | ⚠️ Рекомендуется | `8080` | Порт сервера |
| `HOST` | rawEnv | ⚠️ Рекомендуется | `0.0.0.0` | Хост для привязки |

## Опциональные переменные

| Переменная | Тип | Обязательность | Значение по умолчанию | Описание |
|-----------|-----|----------------|----------------------|----------|
| `FNS_PROD_TOKEN` | secretEnv | ❌ Опциональна | - | Токен от nalog.gov.ru для реальной отправки |
| `FNS_CERT_PATH` | secretEnv | ❌ Опциональна | `/certs/cert.p12` | Путь к файлу КЭП |
| `FNS_CERT_PASSWORD` | secretEnv | ❌ Опциональна | - | Пароль от КЭП |

## Быстрый старт

### Минимальная конфигурация (тест)

```bash
# rawEnvs
FNS_MODE=test
PORT=8080
HOST=0.0.0.0

# secretEnvs
FNS_API_TOKEN=your_token_here
```

### Полная конфигурация (продакшн)

```bash
# rawEnvs
FNS_MODE=prod
PORT=8080
HOST=0.0.0.0

# secretEnvs
FNS_API_TOKEN=your_api_token
FNS_PROD_TOKEN=your_prod_token  # опционально
FNS_CERT_PATH=/certs/cert.p12    # опционально
FNS_CERT_PASSWORD=your_password  # опционально
```


