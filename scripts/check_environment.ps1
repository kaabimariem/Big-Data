# Verification de l'environnement Big Data
Write-Host "`n=== VERIFICATION ENVIRONNEMENT BIG DATA ===`n" -ForegroundColor Cyan

function Test-Tool {
    param($Name, $Command)
    Write-Host "[$Name] " -NoNewline
    try {
        $out = Invoke-Expression $Command 2>&1 | Select-Object -First 1
        Write-Host "OK" -ForegroundColor Green
        Write-Host "       $out"
        return $true
    } catch {
        Write-Host "MANQUANT" -ForegroundColor Red
        return $false
    }
}

$results = @{}
$results["Java"]   = Test-Tool "Java"   "java -version"
$results["Docker"] = Test-Tool "Docker" "docker --version"
$results["Compose"]= Test-Tool "Compose" "docker compose version"
$results["Maven"]  = Test-Tool "Maven"  "mvn -version"
$results["Python"] = Test-Tool "Python" "python --version"

Write-Host "`n=== FICHIERS PROJET ===" -ForegroundColor Cyan
$root = Split-Path -Parent $PSScriptRoot
@(
    "ecommerce_dataset_bigdata.csv",
    "mapreduce\pom.xml",
    "docker\hadoop\docker-compose.yml",
    "docker\spark\docker-compose.yml",
    "spark\batch_analysis.py",
    "spark\streaming_ecommerce.py"
) | ForEach-Object {
    $path = Join-Path $root $_
    if (Test-Path $path) { Write-Host "  OK  $_" -ForegroundColor Green }
    else { Write-Host "  --  $_ (manquant)" -ForegroundColor Yellow }
}

Write-Host "`n=== RECOMMANDATIONS ===" -ForegroundColor Cyan
if (-not $results["Maven"]) {
    Write-Host "  Maven : installer avec 'winget install Apache.Maven'"
    Write-Host "        ou utiliser Maven integre dans IntelliJ IDEA"
}
Write-Host "  Java  : le projet compile en Java 8 (SDK dans IntelliJ)"
Write-Host "  Docker: demarrer Docker Desktop avant les clusters`n"
