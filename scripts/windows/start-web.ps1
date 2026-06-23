[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$SkipInstall,
    [switch]$Production
)

$ErrorActionPreference = "Stop"
$WebRoot = Join-Path $Root "apps\web"

Set-Location $WebRoot

if (-not $SkipInstall -and -not (Test-Path (Join-Path $WebRoot "node_modules"))) {
    Write-Host "[SotuHire] Instalando dependencias do frontend..."
    npm install
}

if ($Production) {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    npm run preview -- --host 127.0.0.1 --port 5173
} else {
    npm run dev -- --host 127.0.0.1 --port 5173
}
