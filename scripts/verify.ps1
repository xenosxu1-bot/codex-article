[CmdletBinding()]
param(
    [switch]$Deep
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

git diff --check

if ($Deep) {
    # Resolve the UTF-8 Chinese script names from the filesystem instead of embedding
    # them in a UTF-8-without-BOM PowerShell 5.1 script, which reads those literals as ANSI.
    $tools = Get-ChildItem -Directory | Where-Object { $_.Name -like '09-*' } | Select-Object -First 1
    if (-not $tools) { throw 'Verification failed: the 09-* tools directory was not found.' }

    $checks = @(
        @{ Marker = 'ARCHIVE_INLINE_DIR ='; Label = 'image asset check' },
        @{ Marker = 'OUTPUT_FILE = ROOT /'; Label = 'topic binding check' },
        @{ Marker = 'BAD_CHARS ='; Label = 'article quality scan' },
        @{ Marker = 'REQUIRED_ARTICLE_STATES ='; Label = 'source evidence check' }
    )
    foreach ($check in $checks) {
        $script = Get-ChildItem -LiteralPath $tools.FullName -File -Filter '*.py' |
            Where-Object { (Get-Content -LiteralPath $_.FullName -Raw -Encoding utf8) -like "*$($check.Marker)*" } |
            Select-Object -First 1
        if (-not $script) { throw "Verification failed: $($check.Label) script was not found." }
        Write-Host "[verify] python $($script.FullName)"
        python $script.FullName
        if ($LASTEXITCODE -ne 0) { throw "Verification failed: $($check.Label)" }
    }
}

Write-Host 'Verification passed.'
