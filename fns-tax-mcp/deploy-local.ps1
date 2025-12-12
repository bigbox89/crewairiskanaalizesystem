param(
    [string]$Registry = $env:CLOUD_RU_REGISTRY,
    [string]$ImageName = "fns-tax-mcp",
    [string]$ImageTag = "latest",
    [string]$Username = $env:CLOUD_RU_USERNAME,
    [string]$Password = $env:CLOUD_RU_PASSWORD
)

if (-not $Registry) {
    Write-Error "REGISTRY not specified. Set CLOUD_RU_REGISTRY environment variable or pass -Registry parameter"
    exit 1
}

if (-not $Username) {
    Write-Error "USERNAME not specified. Set CLOUD_RU_USERNAME environment variable or pass -Username parameter"
    exit 1
}

if (-not $Password) {
    Write-Error "PASSWORD not specified. Set CLOUD_RU_PASSWORD environment variable or pass -Password parameter"
    exit 1
}

$FullImageName = "${Registry}/${ImageName}:${ImageTag}"

Write-Host "Starting local build and publish of image..." -ForegroundColor Green
Write-Host "Registry: $Registry" -ForegroundColor Cyan
Write-Host "Image: $FullImageName" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop or Docker CLI"
    exit 1
}

Write-Host "Docker found" -ForegroundColor Green

Write-Host "Logging in to Cloud.ru registry..." -ForegroundColor Yellow
echo $Password | docker login $Registry -u $Username --password-stdin

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to login to registry"
    exit 1
}

Write-Host "Successfully logged in to registry" -ForegroundColor Green

Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t $FullImageName -f Dockerfile .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build image"
    exit 1
}

Write-Host "Image built successfully" -ForegroundColor Green

Write-Host "Pushing image to Cloud.ru registry..." -ForegroundColor Yellow
docker push $FullImageName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push image"
    exit 1
}

Write-Host "Image published successfully: $FullImageName" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Next step: run workflow to deploy to Container App" -ForegroundColor Cyan
