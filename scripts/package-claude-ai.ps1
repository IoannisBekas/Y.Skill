param(
    [string]$Output = "dist/project-health-pass.zip"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$SkillDir = Join-Path $Root "skills/project-health-pass"
$OutputPath = Join-Path $Root $Output
$OutputDir = Split-Path -Parent $OutputPath

New-Item -ItemType Directory -Force $OutputDir | Out-Null
if (Test-Path $OutputPath) {
    Remove-Item -Force $OutputPath
}

Compress-Archive -Path $SkillDir -DestinationPath $OutputPath
Write-Host "Wrote $OutputPath"
