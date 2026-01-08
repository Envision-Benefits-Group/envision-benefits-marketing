param (
    [string]$POSTGRES_USER,
    [string]$POSTGRES_DB
)

Write-Host "Waiting for database to be ready..."
$ready = $false
while ($ready -eq $false) {
    try {
        $dbContainer = (docker compose ps -q db | Select-Object -First 1)
        if (-not $dbContainer) { $dbContainer = 'postgres_db' }
        $output = docker exec $dbContainer pg_isready -U $POSTGRES_USER -d $POSTGRES_DB 2>&1
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
        } else {
            Write-Host "Database is unavailable - sleeping"
            Start-Sleep -s 2
        }
    } catch {
        Write-Host "Database is unavailable - sleeping"
        Start-Sleep -s 2
    }
}
Write-Host "Database is up and running!"

Write-Host "Waiting for FastAPI backend to be ready..."
$backendReady = $false
while ($backendReady -eq $false) {
    try {
        $backendContainer = (docker compose ps -q backend | Select-Object -First 1)
        if (-not $backendContainer) { $backendContainer = 'fastapi_backend' }
        $healthCheck = docker exec $backendContainer curl -f http://localhost:8000/health 2>$null
        if ($LASTEXITCODE -eq 0) {
            $backendReady = $true
        } else {
            Write-Host "FastAPI backend is unavailable - sleeping"
            Start-Sleep -s 2
        }
    } catch {
        Write-Host "FastAPI backend is unavailable - sleeping"
        Start-Sleep -s 2
    }
}
Write-Host "FastAPI backend is up and running!"
Write-Host "All services are ready!" 