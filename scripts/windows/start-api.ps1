[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"
$DefaultOrigins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"

Set-Location $Root
if (-not $env:SOTUHIRE_API_ALLOWED_ORIGINS) {
    $env:SOTUHIRE_API_ALLOWED_ORIGINS = $DefaultOrigins
}

python scripts/run_api.py
