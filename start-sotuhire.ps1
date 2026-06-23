[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$SkipInstall,
    [switch]$ApiOnly,
    [switch]$WebOnly,
    [switch]$Production
)

$Launcher = Join-Path $PSScriptRoot "scripts\windows\start-sotuhire.ps1"
& $Launcher @PSBoundParameters
exit $LASTEXITCODE
