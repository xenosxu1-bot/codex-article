[CmdletBinding(DefaultParameterSetName = 'Intent')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Intent')]
    [string]$IntentPath,
    [Parameter(Mandatory = $true, ParameterSetName = 'Result')]
    [string]$ResultPath,
    [string]$ProjectConfigPath = (Join-Path $PSScriptRoot '..\09-工具脚本\03-技能接入\article-skill-project.json'),
    [string]$SkillRoot = 'D:\projects_git\article-Skill',
    [switch]$Execute,
    [string]$ReceiptPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Read-JsonFile([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "File not found: $Path" }
    return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Invoke-Git([string[]]$Arguments) {
    $output = @(& git -C $ProjectRoot @Arguments 2>&1)
    if ($LASTEXITCODE -ne 0) { throw "git $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)" }
    return @($output | ForEach-Object { "$_" } | Where-Object { $_.Length -gt 0 })
}

function Invoke-CheckedCommand([scriptblock]$Command, [string]$Name) {
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE." }
}

function Test-SafeRelativePath([string]$Candidate) {
    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $false }
    $normalized = $Candidate.Replace('\', '/').Trim()
    if ($normalized.StartsWith('/') -or $normalized -match '^[A-Za-z]:/' -or $normalized -match '(^|/)..(/|$)' -or $normalized -match '(^|/).git(/|$)') { return $false }
    return $true
}

function Test-OwnedPath([string]$Candidate, [string[]]$OwnedPaths) {
    $normalized = $Candidate.Replace('\', '/').TrimEnd('/')
    foreach ($owned in $OwnedPaths) {
        if ($normalized -eq $owned -or $normalized.StartsWith("$owned/", [System.StringComparison]::Ordinal)) { return $true }
    }
    return $false
}

function Get-WorkingChanges {
    $unstaged = @(Invoke-Git @('diff', '--name-only'))
    $untracked = @(Invoke-Git @('ls-files', '--others', '--exclude-standard'))
    return @($unstaged + $untracked | Sort-Object -Unique)
}

function Write-Receipt([string]$Status, [string]$Message, [object]$Intent, [object]$Extra = $null) {
    $receipt = [ordered]@{
        schema_version = 'generated-article-sync-receipt.v1'
        status = $Status
        message = $Message
        executed_at = (Get-Date).ToUniversalTime().ToString('o')
        project_root = $ProjectRoot
        branch = $(try { (Invoke-Git @('branch', '--show-current') | Select-Object -First 1) } catch { $null })
        intent = $Intent
        extra = $Extra
    }
    $json = $receipt | ConvertTo-Json -Depth 16
    $json
    if ($ReceiptPath) {
        $directory = Split-Path -Parent $ReceiptPath
        if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
        [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath $directory).Path + [IO.Path]::DirectorySeparatorChar + (Split-Path -Leaf $ReceiptPath), $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($true)))
    }
}

$intent = $null
try {
    $config = Read-JsonFile $ProjectConfigPath
    $intent = if ($PSCmdlet.ParameterSetName -eq 'Result') {
        $result = Read-JsonFile $ResultPath
        $result.repository_sync_intent
    } else {
        Read-JsonFile $IntentPath
    }
    if ($null -eq $intent) { throw 'No repository_sync_intent is present; automatic repository delivery is not authorized.' }
    $adapter = $config.repository_sync
    if ($null -eq $adapter -or $adapter.enabled -ne $true) { throw 'Repository sync is disabled in the project adapter configuration.' }
    if ($intent.schema_version -ne $adapter.intent_schema) { throw "Unexpected intent schema: $($intent.schema_version)" }
    if ($intent.status -ne $adapter.trigger.required_intent_status) { throw "Intent status is not executable: $($intent.status)" }
    if ($intent.authorization.allow_repository_sync -ne $true) { throw 'The intent lacks explicit repository-sync authorization.' }
    if ($intent.execution_profile -ne $adapter.trigger.required_execution_profile) { throw "Intent execution profile must be $($adapter.trigger.required_execution_profile)." }
    if ($intent.target_id -ne $adapter.target.id) { throw "Intent target_id does not match this project: $($intent.target_id)" }
    if ($intent.branch -ne $adapter.target.branch) { throw "Intent branch does not match configured target branch: $($intent.branch)" }
    if ([string]::IsNullOrWhiteSpace([string]$intent.article_id) -or [string]::IsNullOrWhiteSpace([string]$intent.commit_message)) { throw 'Intent must contain article_id and commit_message.' }
    if ($null -eq $intent.final_article_package -or [string]::IsNullOrWhiteSpace([string]$intent.final_article_package.artifact_id) -or [string]::IsNullOrWhiteSpace([string]$intent.final_article_package.content_sha256)) { throw 'Intent final_article_package lineage is incomplete.' }

    $ownedPaths = @($intent.owned_paths | ForEach-Object { "$_".Replace('\', '/').TrimEnd('/') })
    if ($ownedPaths.Count -eq 0 -or @($ownedPaths | Select-Object -Unique).Count -ne $ownedPaths.Count) { throw 'Intent owned_paths must be a non-empty unique list.' }
    $allowedPrefixes = @($adapter.safety.allowed_owned_path_prefixes)
    foreach ($owned in $ownedPaths) {
        if (-not (Test-SafeRelativePath $owned)) { throw "Unsafe owned path: $owned" }
        $allowed = $false
        foreach ($prefix in $allowedPrefixes) {
            $prefixText = "$prefix".Replace('\', '/').TrimEnd('/')
            if ($owned -eq $prefixText -or $owned.StartsWith("$prefixText/", [System.StringComparison]::Ordinal)) { $allowed = $true; break }
        }
        if (-not $allowed) { throw "Owned path is outside configured article-delivery scope: $owned" }
    }
    $requiredChecks = @($intent.required_checks)
    $unsupportedChecks = @($requiredChecks | Where-Object { $_ -notin @($adapter.required_checks) })
    if ($unsupportedChecks.Count -gt 0) { throw "Intent requests unsupported checks: $($unsupportedChecks -join ', ')" }

    $branch = (Invoke-Git @('branch', '--show-current') | Select-Object -First 1)
    if ($branch -ne $adapter.target.branch) { throw "Current branch is $branch; expected $($adapter.target.branch)." }

    if (-not $Execute) {
        Write-Receipt 'planned' 'Intent is structurally valid. Dry run does not fetch, validate, stage, commit, or push.' $intent ([ordered]@{ working_changes = @(Get-WorkingChanges) })
        exit 0
    }

    $preexistingStaged = @(Invoke-Git @('diff', '--cached', '--name-only'))
    if ($adapter.safety.block_on_preexisting_staged_changes -eq $true -and $preexistingStaged.Count -gt 0) { throw "Pre-existing staged changes block automatic sync: $($preexistingStaged -join ', ')" }
    $initialChanges = @(Get-WorkingChanges)
    $initialOutside = @($initialChanges | Where-Object { -not (Test-OwnedPath $_ $ownedPaths) })
    if ($adapter.safety.block_on_unowned_changes -eq $true -and $initialOutside.Count -gt 0) { throw "Unowned working-tree changes block automatic sync: $($initialOutside -join ', ')" }
    if ($initialChanges.Count -eq 0) { throw 'No uncommitted target changes are available to synchronize.' }

    Invoke-Git @('fetch', 'origin') | Out-Null
    $aheadBehind = @(Invoke-Git @('rev-list', '--left-right', '--count', "HEAD...origin/$branch"))
    $counts = ($aheadBehind -join ' ').Trim().Split([char[]]' ' , [System.StringSplitOptions]::RemoveEmptyEntries)
    if ($adapter.safety.block_when_remote_not_equal -eq $true -and ($counts.Count -ne 2 -or $counts[0] -ne '0' -or $counts[1] -ne '0')) { throw "Local and origin/$branch differ (ahead=$($counts[0]), behind=$($counts[1])); automatic merge is disabled." }

    $toolsRoot = Get-ChildItem -LiteralPath $ProjectRoot -Directory | Where-Object { $_.Name -like '09-*' } | Select-Object -First 1
    if ($null -eq $toolsRoot) { throw 'Cannot locate project tool directory.' }
    $validationRoot = Get-ChildItem -LiteralPath $toolsRoot.FullName -Directory | Where-Object { $_.Name -like '01-*' } | Select-Object -First 1
    if ($null -eq $validationRoot) { throw 'Cannot locate project validation directory.' }
    $validationScripts = @(Get-ChildItem -LiteralPath $validationRoot.FullName -File -Filter '*.py')
    $unified = $validationScripts | Where-Object { (Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8) -match '--skill-root' } | Select-Object -First 1
    $oneClick = $validationScripts | Where-Object { $_.Name -match '一键发布检查' } | Select-Object -First 1
    if ($null -eq $unified -or $null -eq $oneClick) { throw 'Cannot locate the required article validation scripts.' }
    if ('article_unified_check' -in $requiredChecks) { Invoke-CheckedCommand { & python $unified.FullName --id $intent.article_id --strict --skill-root $SkillRoot } 'Article unified check' }
    if ('one_click_publish_check' -in $requiredChecks) { Invoke-CheckedCommand { & python $oneClick.FullName } 'One-click publish check' }
    if ('project_deep_verify' -in $requiredChecks) { Invoke-CheckedCommand { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot 'scripts\verify.ps1') -Deep } 'Project deep verification' }

    $postCheckChanges = @(Get-WorkingChanges)
    $postCheckOutside = @($postCheckChanges | Where-Object { -not (Test-OwnedPath $_ $ownedPaths) })
    if ($adapter.safety.block_on_unowned_changes -eq $true -and $postCheckOutside.Count -gt 0) { throw "Checks produced or retained unowned changes; automatic sync stopped: $($postCheckOutside -join ', ')" }
    if ($postCheckChanges.Count -eq 0) { throw 'Checks completed but no owned changes remain to commit.' }
    if ('git_diff_check' -in $requiredChecks) { Invoke-Git @('diff', '--check') | Out-Null }

    Invoke-Git (@('add', '--') + $ownedPaths) | Out-Null
    $cached = @(Invoke-Git @('diff', '--cached', '--name-only'))
    if ($cached.Count -eq 0) { throw 'Explicit staging produced no changes.' }
    $cachedOutside = @($cached | Where-Object { -not (Test-OwnedPath $_ $ownedPaths) })
    if ($cachedOutside.Count -gt 0) { throw "Staged changes escape the intent owned paths: $($cachedOutside -join ', ')" }
    if ('staged_secret_scan' -in $requiredChecks) { Invoke-Git @('diff', '--cached', '--check') | Out-Null }

    Invoke-Git @('commit', '-m', [string]$intent.commit_message) | Out-Null
    $commit = (Invoke-Git @('rev-parse', 'HEAD') | Select-Object -First 1)
    Invoke-Git @('push', 'origin', $branch) | Out-Null
    $remoteLine = (Invoke-Git @('ls-remote', 'origin', "refs/heads/$branch") | Select-Object -First 1)
    $remoteCommit = ($remoteLine -split '\s+')[0]
    if ($remoteCommit -ne $commit) { throw "Push did not verify on origin/$branch (local=$commit, remote=$remoteCommit)." }
    Write-Receipt 'pushed' 'Generated article changes were validated, explicitly staged, committed, pushed, and verified on origin.' $intent ([ordered]@{ commit = $commit; remote_commit = $remoteCommit; staged_paths = $cached })
}
catch {
    Write-Receipt 'blocked' $_.Exception.Message $intent $null
    exit 1
}
