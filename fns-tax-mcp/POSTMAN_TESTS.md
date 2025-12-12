# MCP Server - Postman Tests

## Базовый URL
```
https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru
```

## Endpoints

### 1. Health Check
**GET** `/health`

**Request:**
```
GET https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "fns-tax-mcp"
}
```

---

### 2. Root Endpoint (Info)
**GET** `/`

**Request:**
```
GET https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/
```

**Expected Response:**
```json
{
  "service": "fns-tax-mcp",
  "description": "MCP-сервер для генерации деклараций и работы с API-ФНС (24 tools)",
  "tools": [
    "generate_usn_declaration",
    "generate_osno_declaration",
    ...
  ]
}
```

---

### 3. MCP Protocol - List Tools
**POST** `/mcp`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

**Full URL:**
```
POST https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/mcp
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "generate_usn_declaration",
        "description": "Генерирует готовую к отправке декларацию по УСН...",
        "inputSchema": {...}
      },
      ...
    ]
  },
  "id": 1
}
```

---

### 4. MCP Protocol - Call Tool: generate_usn_declaration
**POST** `/mcp`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 2,
  "params": {
    "name": "generate_usn_declaration",
    "arguments": {
      "inn": "7707083893",
      "period": "Q1",
      "year": 2025,
      "income": 1000000.0,
      "expenses": 0.0,
      "tax_rate": 6
    }
  }
}
```

**Full URL:**
```
POST https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/mcp
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Декларация УСН 6% за Q1 2025\nИНН: 7707083893\n..."
      }
    ],
    "isError": false
  },
  "id": 2
}
```

---

### 5. MCP Protocol - Call Tool: generate_osno_declaration
**POST** `/mcp`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 3,
  "params": {
    "name": "generate_osno_declaration",
    "arguments": {
      "inn": "7707083893",
      "period": "Q1",
      "year": 2025,
      "income": 2000000.0,
      "expenses": 500000.0,
      "profit": 1500000.0,
      "loss": 0.0,
      "nds": 200000.0
    }
  }
}
```

---

### 6. MCP Protocol - Call Tool: generate_nds_declaration
**POST** `/mcp`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 4,
  "params": {
    "name": "generate_nds_declaration",
    "arguments": {
      "inn": "7707083893",
      "period": "Q1",
      "year": 2025,
      "turnover": 2000000.0,
      "nds_to_pay": 200000.0,
      "nds_to_refund": 0.0
    }
  }
}
```

---

### 7. MCP Protocol - Call Tool: generate_6ndfl_declaration
**POST** `/mcp`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 5,
  "params": {
    "name": "generate_6ndfl_declaration",
    "arguments": {
      "inn": "7707083893",
      "period": "Q1",
      "year": 2025,
      "total_income": 5000000.0,
      "total_ndfl": 650000.0,
      "withheld_ndfl": 650000.0
    }
  }
}
```

---

### 8. MCP Protocol - Call Tool: search_companies
**POST** `/mcp`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 6,
  "params": {
    "name": "search_companies",
    "arguments": {
      "q": "Яндекс"
    }
  }
}
```

**Note:** Этот tool требует `FNS_API_TOKEN` в переменных окружения сервера.

---

## Postman Collection JSON

```json
{
  "info": {
    "name": "FNS Tax MCP Server",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/health",
          "protocol": "https",
          "host": ["0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server", "ai-agent", "inference", "cloud", "ru"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Root Info",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/",
          "protocol": "https",
          "host": ["0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server", "ai-agent", "inference", "cloud", "ru"],
          "path": [""]
        }
      }
    },
    {
      "name": "MCP - List Tools",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"jsonrpc\": \"2.0\",\n  \"method\": \"tools/list\",\n  \"id\": 1\n}"
        },
        "url": {
          "raw": "https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/mcp",
          "protocol": "https",
          "host": ["0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server", "ai-agent", "inference", "cloud", "ru"],
          "path": ["mcp"]
        }
      }
    },
    {
      "name": "MCP - Generate USN Declaration",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"jsonrpc\": \"2.0\",\n  \"method\": \"tools/call\",\n  \"id\": 2,\n  \"params\": {\n    \"name\": \"generate_usn_declaration\",\n    \"arguments\": {\n      \"inn\": \"7707083893\",\n      \"period\": \"Q1\",\n      \"year\": 2025,\n      \"income\": 1000000.0,\n      \"expenses\": 0.0,\n      \"tax_rate\": 6\n    }\n  }\n}"
        },
        "url": {
          "raw": "https://0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server.ai-agent.inference.cloud.ru/mcp",
          "protocol": "https",
          "host": ["0129b13c-fcab-4f94-83c0-5b1622ff4297-mcp-server", "ai-agent", "inference", "cloud", "ru"],
          "path": ["mcp"]
        }
      }
    }
  ]
}
```

## Все доступные Tools (24)

1. `generate_usn_declaration` - Генерация декларации УСН
2. `generate_osno_declaration` - Генерация декларации ОСНО
3. `generate_nds_declaration` - Генерация декларации НДС
4. `generate_6ndfl_declaration` - Генерация формы 6-НДФЛ
5. `search_companies` - Поиск компаний
6. `autocomplete` - Автодополнение
7. `get_company_data` - Получение данных компании
8. `multinfo_companies` - Множественный запрос данных
9. `multcheck_companies` - Множественная проверка
10. `check_counterparty` - Проверка контрагента
11. `check_account_blocks` - Проверка блокировок счета
12. `check_account_blocks_file` - Проверка блокировок (файл)
13. `track_changes` - Отслеживание изменений
14. `monitor_companies` - Мониторинг компаний
15. `get_extract` - Получение выписки
16. `get_msp_extract` - Выписка МСП
17. `get_accounting_report` - Бухгалтерская отчетность
18. `get_accounting_report_file` - Бухгалтерская отчетность (файл)
19. `get_inn_by_passport` - ИНН по паспорту
20. `check_passport` - Проверка паспорта
21. `check_passport_info` - Информация о паспорте
22. `check_person_status` - Статус физического лица
23. `get_fsrar_licenses` - Лицензии ФСРАР
24. `get_api_statistics` - Статистика API

