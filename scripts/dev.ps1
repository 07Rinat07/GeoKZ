$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Создан .env из .env.example. Перед эксплуатацией смените пароль БД." -ForegroundColor Yellow
}

docker compose up --build
