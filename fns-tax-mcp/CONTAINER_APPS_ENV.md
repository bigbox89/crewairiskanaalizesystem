# Переменные окружения для деплоя в Container Apps

## Обязательные переменные (Required)

### FNS_MODE
- **Тип:** `rawEnv` (обычная переменная)
- **Обязательность:** ✅ Обязательна
- **Значение по умолчанию:** `test`
- **Описание:** Режим работы сервера
- **Возможные значения:**
  - `test` - тестовый режим (используются заглушки из mocks.py)
  - `prod` - продакшн режим (используется реальный API-ФНС)
- **Пример:** `FNS_MODE=prod`

### FNS_API_TOKEN
- **Тип:** `secretEnv` (секретная переменная)
- **Обязательность:** ✅ Обязательна
- **Описание:** Токен от api-fns.ru для работы с API-ФНС
- **Как получить:** Регистрация на https://api-fns.ru (за 1 минуту)
- **Пример:** `FNS_API_TOKEN=your_api_token_here`

### PORT
- **Тип:** `rawEnv` (обычная переменная)
- **Обязательность:** ⚠️ Рекомендуется (если не указан, используется 8080)
- **Значение по умолчанию:** `8080`
- **Описание:** Порт, на котором будет работать сервер
- **Пример:** `PORT=8080`

### HOST
- **Тип:** `rawEnv` (обычная переменная)
- **Обязательность:** ⚠️ Рекомендуется (если не указан, используется 0.0.0.0)
- **Значение по умолчанию:** `0.0.0.0`
- **Описание:** Хост для привязки сервера
- **Пример:** `HOST=0.0.0.0`

---

## Опциональные переменные (Optional)

### FNS_PROD_TOKEN
- **Тип:** `secretEnv` (секретная переменная)
- **Обязательность:** ❌ Опциональна
- **Описание:** Токен от nalog.gov.ru для реальной отправки деклараций
- **Когда нужна:** Только если планируется реальная отправка деклараций в ФНС
- **Пример:** `FNS_PROD_TOKEN=your_prod_token_here`

### FNS_CERT_PATH
- **Тип:** `secretEnv` (секретная переменная)
- **Обязательность:** ❌ Опциональна
- **Значение по умолчанию:** `/certs/cert.p12`
- **Описание:** Путь к файлу КЭП (квалифицированной электронной подписи) .p12 внутри контейнера
- **Когда нужна:** Только если планируется подписание деклараций КЭП
- **Пример:** `FNS_CERT_PATH=/certs/cert.p12`

### FNS_CERT_PASSWORD
- **Тип:** `secretEnv` (секретная переменная)
- **Обязательность:** ❌ Опциональна (требуется только если указан FNS_CERT_PATH)
- **Описание:** Пароль от файла КЭП
- **Когда нужна:** Только если указан FNS_CERT_PATH
- **Пример:** `FNS_CERT_PASSWORD=your_cert_password`

---

## Конфигурация для Container Apps

### Минимальная конфигурация (для тестирования)

```yaml
environmentVariables:
  - name: FNS_MODE
    value: "test"
  - name: PORT
    value: "8080"
  - name: HOST
    value: "0.0.0.0"

secrets:
  - name: FNS_API_TOKEN
    value: "your_api_token_here"
```

### Полная конфигурация (для продакшна)

```yaml
environmentVariables:
  - name: FNS_MODE
    value: "prod"
  - name: PORT
    value: "8080"
  - name: HOST
    value: "0.0.0.0"

secrets:
  - name: FNS_API_TOKEN
    value: "your_api_token_here"
  - name: FNS_PROD_TOKEN
    value: "your_prod_token_here"  # Опционально
  - name: FNS_CERT_PATH
    value: "/certs/cert.p12"  # Опционально
  - name: FNS_CERT_PASSWORD
    value: "your_cert_password"  # Опционально
```

---

## JSON формат для Cloud.ru Container Apps

### Минимальная конфигурация

```json
{
  "environmentVariables": {
    "FNS_MODE": "test",
    "PORT": "8080",
    "HOST": "0.0.0.0"
  },
  "secrets": {
    "FNS_API_TOKEN": "your_api_token_here"
  }
}
```

### Полная конфигурация

```json
{
  "environmentVariables": {
    "FNS_MODE": "prod",
    "PORT": "8080",
    "HOST": "0.0.0.0"
  },
  "secrets": {
    "FNS_API_TOKEN": "your_api_token_here",
    "FNS_PROD_TOKEN": "your_prod_token_here",
    "FNS_CERT_PATH": "/certs/cert.p12",
    "FNS_CERT_PASSWORD": "your_cert_password"
  }
}
```

---

## Примечания

1. **FNS_MODE**: 
   - В тестовом режиме (`test`) все tools возвращают заглушки из `mocks.py`
   - В продакшн режиме (`prod`) используются реальные запросы к API-ФНС

2. **FNS_API_TOKEN**: 
   - Обязателен для работы в режиме `prod`
   - Можно получить бесплатно на https://api-fns.ru
   - В режиме `test` не используется, но переменная все равно должна быть задана

3. **PORT и HOST**: 
   - Обычно не требуют изменения
   - Container Apps автоматически управляет портами
   - HOST должен быть `0.0.0.0` для работы в контейнере

4. **КЭП (FNS_CERT_PATH, FNS_CERT_PASSWORD)**: 
   - Нужны только для реальной отправки деклараций
   - Файл сертификата должен быть смонтирован в контейнер как volume
   - В Container Apps используйте секреты для хранения пароля

---

## Проверка конфигурации

После деплоя проверьте работу сервера:

1. **Health check:**
   ```bash
   curl https://your-app-url/health
   ```

2. **Список tools:**
   ```bash
   curl https://your-app-url/
   ```

3. **MCP endpoint:**
   ```bash
   curl -X POST https://your-app-url/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
   ```


