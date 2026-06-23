[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$SkipInstall,
    [switch]$ApiOnly,
    [switch]$WebOnly,
    [switch]$Production
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DefaultOrigins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
$ApiUrl = "http://127.0.0.1:8787"
$ApiHealthUrl = "$ApiUrl/api/v1/health"
$ApiDocsUrl = "$ApiUrl/docs"
$FrontendUrl = "http://localhost:5173"
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

function Start-SotuProcess {
    param(
        [string]$Name,
        [string]$Script,
        [string[]]$Arguments
    )
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $PowerShellExe = (Get-Process -Id $PID).Path
    $StdOut = Join-Path $LogDir "$Name.out.log"
    $StdErr = Join-Path $LogDir "$Name.err.log"
    $ArgumentList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $Script) + $Arguments
    $Process = Start-Process `
        -FilePath $PowerShellExe `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $Root `
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
Write-Host "API:       $ApiUrl"
Write-Host "API docs:  $ApiDocsUrl"
Write-Host "Frontend: $FrontendUrl"
Write-Host "CORS:      $env:SOTUHIRE_API_ALLOWED_ORIGINS"
Write-Host ""

try {
    if (-not $WebOnly) {
        $ApiScript = Join-Path $PSScriptRoot "start-api.ps1"
        $Processes += Start-SotuProcess -Name "api" -Script $ApiScript -Arguments @("-Root", $Root)
        Wait-Http -Url $ApiHealthUrl -Name "API"
    }

    if (-not $ApiOnly) {
        $WebScript = Join-Path $PSScriptRoot "start-web.ps1"
        $WebArgs = @("-Root", $Root)
        if ($SkipInstall) {
            $WebArgs += "-SkipInstall"
        }
        if ($Production) {
            $WebArgs += "-Production"
        }
        $Processes += Start-SotuProcess -Name "web" -Script $WebScript -Arguments $WebArgs
        Wait-Http -Url $FrontendUrl -Name "Frontend"
        if (-not $NoBrowser) {
            Start-Process $FrontendUrl
        }
    }

    Write-Host ""
    Write-Host "[SotuHire] Pronto. Use Ctrl+C para parar API e frontend."
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
