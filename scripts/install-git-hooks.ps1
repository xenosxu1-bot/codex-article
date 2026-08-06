[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

git config extensions.worktreeConfig true
git config core.hooksPath .githooks
Write-Host "Git hooks configured for $root"
