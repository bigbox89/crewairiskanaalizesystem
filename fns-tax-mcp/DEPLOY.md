# Процесс деплоя fns-tax-mcp

## 📋 Обязательный порядок деплоя

### 1. Локальная сборка и публикация образа в Cloud.ru registry

**Windows PowerShell:**
```powershell
# Установите переменные окружения
$env:CLOUD_RU_REGISTRY = "tax-fns-agents-registry.cr.cloud.ru"
$env:CLOUD_RU_USERNAME = "ваш_username"
$env:CLOUD_RU_PASSWORD = "ваш_пароль"

# Запустите скрипт
.\deploy-local.ps1
```

**Linux/Mac:**
```bash
# Установите переменные окружения
export CLOUD_RU_REGISTRY="tax-fns-agents-registry.cr.cloud.ru"
export CLOUD_RU_USERNAME="ваш_username"
export CLOUD_RU_PASSWORD="ваш_пароль"

# Сделайте скрипт исполняемым (один раз)
chmod +x deploy-local.sh

# Запустите скрипт
./deploy-local.sh
```

Скрипт автоматически:
- ✅ Проверит наличие Docker
- ✅ Войдет в Cloud.ru registry
- ✅ Соберет образ из `Dockerfile`
- ✅ Запушит образ в registry: `{REGISTRY}/fns-tax-mcp:latest`

### 2. Коммит и пуш кода в Git репозиторий

```powershell
# Windows PowerShell
git add .
git commit -m "feat: описание изменений"
git push origin master
```

### 3. Запуск CI/CD workflow для деплоя в Container App

Workflow автоматически:
- ✅ Использует образ из registry (или соберет новый, если нужно)
- ✅ Деплоит в Cloud.ru Container App через `evo-container-app-action@v5`

**Запуск workflow:**
- Автоматически при push в `main` ветку
- Или вручную через GitVerse UI: Actions → Deploy to Cloud.ru Container App → Run workflow

## 🔧 Переменные окружения для деплоя

Убедитесь, что в GitVerse Secrets настроены:
- `CLOUD_RU_REGISTRY` - адрес registry (например: `tax-fns-agents-registry.cr.cloud.ru`)
- `CLOUD_RU_USERNAME` - username для входа в registry
- `CLOUD_RU_PASSWORD` - пароль для входа в registry
- `CLOUD_RU_PROJECT_ID` - ID проекта в Cloud.ru

## 📝 Примечания

- Образ **рекомендуется** собирать локально перед запуском workflow
- Workflow может собрать образ сам, если он еще не существует в registry
- Для тестирования используйте тег `latest`, для продакшена - версию или SHA коммита
- Все credentials хранятся в GitVerse Secrets, не хардкодите их в скриптах

