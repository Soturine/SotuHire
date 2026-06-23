[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$SkipInstall,
    [switch]$ApiOnly,
    [switch]$WebOnly,
    [switch]$Production,
    [switch]$WithCompanion
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DefaultOrigins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
$ApiUrl = "http://127.0.0.1:8787"
$ApiHealthUrl = "$ApiUrl/api/v1/health"
$ApiDocsUrl = "$ApiUrl/docs"
$FrontendUrl = "http://localhost:5173"
$FrontendHealthUrl = "http://127.0.0.1:5173"
$CompanionUrl = "http://127.0.0.1:8765"
$CompanionHealthUrl = "$CompanionUrl/health"
$LogDir = Join-Path $Root ".sotuhire\logs"
$Processes = @()

function Assert-Command {
    param(
        [string]$Name,
        [string]$Label
    )
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Label nao encontrado no PATH."
    }
}

function Assert-RepoRoot {
    if (-not (Test-Path (Join-Path $Root "pyproject.toml")) -or
        -not (Test-Path (Join-Path $Root "scripts\run_api.py")) -or
        -not (Test-Path (Join-Path $Root "apps\web\package.json"))) {
        throw "Execute este launcher a partir da raiz do repositorio SotuHire."
    }
}

function Wait-Http {
    param(
        [string]$Url,
        [string]$Name,
        [int]$TimeoutSeconds = 90
    )
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500) {
                Write-Host "[SotuHire] $Name pronto: $Url"
                return
            }
        } catch {
            Start-Sleep -Milliseconds 700
        }
    }
    throw "Timeout aguardando $Name em $Url."
}

function Start-SotuCommand {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command
    )
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $PowerShellExe = (Get-Process -Id $PID).Path
    $StdOut = Join-Path $LogDir "$Name.out.log"
    $StdErr = Join-Path $LogDir "$Name.err.log"
    $ArgumentList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $Command)
    $Process = Start-Process `
        -FilePath $PowerShellExe `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdOut `
        -RedirectStandardError $StdErr
    Write-Host "[SotuHire] $Name iniciado (PID $($Process.Id)). Logs: $StdOut"
    return $Process
}

function Stop-SotuProcesses {
    foreach ($Process in $Processes) {
        if ($null -ne $Process -and -not $Process.HasExited) {
            Write-Host "[SotuHire] Encerrando PID $($Process.Id)..."
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

if ($ApiOnly -and $WebOnly) {
    throw "Use apenas uma flag: -ApiOnly ou -WebOnly."
}

Assert-RepoRoot
Assert-Command -Name "python" -Label "Python"
if (-not $ApiOnly) {
    Assert-Command -Name "node" -Label "Node.js"
    Assert-Command -Name "npm" -Label "npm"
}

$env:SOTUHIRE_API_ALLOWED_ORIGINS = if ($env:SOTUHIRE_API_ALLOWED_ORIGINS) {
    $env:SOTUHIRE_API_ALLOWED_ORIGINS
} else {
    $DefaultOrigins
}

Write-Host ""
Write-Host "SotuHire local"
Write-Host "API:          $ApiUrl"
Write-Host "API docs:     $ApiDocsUrl"
Write-Host "Frontend:    $FrontendUrl"
if ($WithCompanion) {
    Write-Host "Companion:   $CompanionUrl"
}
Write-Host "CORS:         $env:SOTUHIRE_API_ALLOWED_ORIGINS"
Write-Host ""

try {
    if (-not $WebOnly) {
        $Processes += Start-SotuCommand `
            -Name "api" `
            -WorkingDirectory $Root `
            -Command "python scripts/run_api.py"
        Wait-Http -Url $ApiHealthUrl -Name "API"
    }

    if ($WithCompanion) {
        $Processes += Start-SotuCommand `
            -Name "companion" `
            -WorkingDirectory $Root `
            -Command "python -m modules.local_api.server"
        Wait-Http -Url $CompanionHealthUrl -Name "Local Companion"
    }

    if (-not $ApiOnly) {
        $WebRoot = Join-Path $Root "apps\web"
        if (-not $SkipInstall -and -not (Test-Path (Join-Path $WebRoot "node_modules"))) {
            Write-Host "[SotuHire] Instalando dependencias do frontend..."
            Push-Location $WebRoot
            try {
                npm install
                if ($LASTEXITCODE -ne 0) {
                    throw "npm install falhou com codigo $LASTEXITCODE."
                }
            } finally {
                Pop-Location
            }
        }

        $WebCommand = if ($Production) {
            "npm run build; if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }; npm run preview -- --host 127.0.0.1 --port 5173"
        } else {
            "npm run dev -- --host 127.0.0.1 --port 5173"
        }
        $Processes += Start-SotuCommand -Name "web" -WorkingDirectory $WebRoot -Command $WebCommand
        Wait-Http -Url $FrontendHealthUrl -Name "Frontend" -TimeoutSeconds 180
        if (-not $NoBrowser) {
            Start-Process $FrontendUrl
        }
    }

    Write-Host ""
    Write-Host "[SotuHire] Pronto. Use Ctrl+C para parar os processos."
    while ($true) {
        Start-Sleep -Seconds 1
        foreach ($Process in $Processes) {
            if ($Process.HasExited) {
                throw "Processo PID $($Process.Id) encerrou com codigo $($Process.ExitCode). Veja os logs em $LogDir."
            }
        }
    }
} finally {
    Stop-SotuProcesses
}
