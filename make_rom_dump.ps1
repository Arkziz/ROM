#requires -Version 5.1

$ErrorActionPreference = "Stop"

# Use the folder where this script is located.
# This avoids encoding problems in paths with non-ASCII characters.
$ProjectRoot = $PSScriptRoot
$OutputFile = Join-Path $ProjectRoot "ROM_FULL_DUMP.txt"

$MaxFileSizeMB = 2
$MaxFileSizeBytes = $MaxFileSizeMB * 1MB

$ExcludeDirectoryNames = @(
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "node_modules",
    "dist",
    "build",
    "logs",
    "log",
    "tmp",
    "temp",
    "patch",
    "backup"
	"MD"
	"simulation_reports"
)

$ExcludeExactFileNames = @(
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "game.db",
    "game.db-shm",
    "game.db-wal",
    "changes.diff"
)

$ExcludeFilePatterns = @(
    "ROM_FULL_DUMP*.txt",
    "*.db",
    "*.db-shm",
    "*.db-wal",
    "*.sqlite",
    "*.sqlite3",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.dll",
    "*.exe",
    "*.msi",
    "*.bin",
    "*.dat",
    "*.zip",
    "*.7z",
    "*.rar",
    "*.tar",
    "*.gz",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.webp",
    "*.ico",
    "*.bmp",
    "*.pdf",
    "*.doc",
    "*.docx",
    "*.xls",
    "*.xlsx",
    "*.ppt",
    "*.pptx",
    "*.log",
    "*.tmp",
    "*.bak"
)

$AllowedExtensions = @(
    ".py",
    ".pyi",
    ".pyw",
    ".md",
    ".txt",
    ".json",
    ".jsonc",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".csv",
    ".sql",
    ".ps1",
    ".psm1",
    ".psd1",
    ".bat",
    ".cmd",
    ".sh"
)

$AllowedExactFileNames = @(
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    "requirements.txt",
    "README",
    "LICENSE"
)

function Get-RelativePathSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BasePath,

        [Parameter(Mandatory = $true)]
        [string]$FullPath
    )

    $NormalizedBase = $BasePath.TrimEnd("\", "/")

    if ($FullPath.StartsWith($NormalizedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $FullPath.Substring($NormalizedBase.Length).TrimStart("\", "/")
    }

    return $FullPath
}

function Test-IsExcludedDirectory {
    param(
        [AllowEmptyString()]
        [string]$RelativeDirectory
    )

    if ([string]::IsNullOrWhiteSpace($RelativeDirectory)) {
        return $false
    }

    $Parts = $RelativeDirectory -split "[\\/]+"

    foreach ($Part in $Parts) {
        foreach ($ExcludedName in $ExcludeDirectoryNames) {
            if ($Part -ieq $ExcludedName) {
                return $true
            }
        }
    }

    return $false
}

function Test-IsExcludedFileName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FileName
    )

    foreach ($ExcludedName in $ExcludeExactFileNames) {
        if ($FileName -ieq $ExcludedName) {
            return $true
        }
    }

    foreach ($Pattern in $ExcludeFilePatterns) {
        if ($FileName -like $Pattern) {
            return $true
        }
    }

    return $false
}

function Test-IsAllowedTextFile {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File
    )

    foreach ($AllowedName in $AllowedExactFileNames) {
        if ($File.Name -ieq $AllowedName) {
            return $true
        }
    }

    return ($AllowedExtensions -contains $File.Extension.ToLowerInvariant())
}

function Test-ShouldIncludeFile {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File
    )

    $RelativePath = Get-RelativePathSafe -BasePath $ProjectRoot -FullPath $File.FullName
    $RelativeDirectory = Split-Path $RelativePath -Parent

    if (Test-IsExcludedDirectory -RelativeDirectory $RelativeDirectory) {
        return $false
    }

    if (Test-IsExcludedFileName -FileName $File.Name) {
        return $false
    }

    if (-not (Test-IsAllowedTextFile -File $File)) {
        return $false
    }

    if ($File.Length -gt $MaxFileSizeBytes) {
        return $false
    }

    return $true
}

function Add-DumpLine {
    param(
        [AllowEmptyString()]
        [string]$Text = ""
    )

    Add-Content -LiteralPath $OutputFile -Value $Text -Encoding UTF8
}

function Get-SafeFileContent {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File
    )

    try {
        return Get-Content -LiteralPath $File.FullName -Raw -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        try {
            return Get-Content -LiteralPath $File.FullName -Raw -ErrorAction Stop
        }
        catch {
            return "[FILE READ ERROR: $($_.Exception.Message)]"
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    Write-Host "ERROR: PSScriptRoot is empty." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    Write-Host "ERROR: Project directory was not found:" -ForegroundColor Red
    Write-Host $ProjectRoot -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "db.py") -PathType Leaf)) {
    Write-Host "ERROR: db.py was not found in the project root:" -ForegroundColor Red
    Write-Host $ProjectRoot -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Scanning project files..." -ForegroundColor Cyan

$AllFiles = @(
    Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -Force -ErrorAction SilentlyContinue
)

$IncludedFiles = @(
    $AllFiles |
        Where-Object { Test-ShouldIncludeFile -File $_ } |
        Sort-Object FullName
)

$ExcludedFilesCount = $AllFiles.Count - $IncludedFiles.Count

if (Test-Path -LiteralPath $OutputFile) {
    Remove-Item -LiteralPath $OutputFile -Force
}

Set-Content -LiteralPath $OutputFile -Value "" -Encoding UTF8

$CreatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
$PowerShellVersion = $PSVersionTable.PSVersion.ToString()

Add-DumpLine "============================================================"
Add-DumpLine "ROM PROJECT SAFE FULL DUMP"
Add-DumpLine "============================================================"
Add-DumpLine ""
Add-DumpLine "Created: $CreatedAt"
Add-DumpLine "Project root: $ProjectRoot"
Add-DumpLine "PowerShell: $PowerShellVersion"
Add-DumpLine "Included files: $($IncludedFiles.Count)"
Add-DumpLine "Excluded files: $ExcludedFilesCount"
Add-DumpLine "Maximum file size: $MaxFileSizeMB MB"
Add-DumpLine ""
Add-DumpLine "SECURITY EXCLUSIONS:"
Add-DumpLine "- environment secrets"
Add-DumpLine "- SQLite databases and WAL/SHM files"
Add-DumpLine "- virtual environments"
Add-DumpLine "- IDE metadata"
Add-DumpLine "- Git internals"
Add-DumpLine "- patch and backup history"
Add-DumpLine "- caches and compiled files"
Add-DumpLine "- binary and archive files"
Add-DumpLine "- previous ROM_FULL_DUMP files"
Add-DumpLine ""
Add-DumpLine "==================== PROJECT TREE ===================="
Add-DumpLine ""
Add-DumpLine $ProjectRoot

if ($IncludedFiles.Count -eq 0) {
    Add-DumpLine "[NO FILES INCLUDED]"
}
else {
    foreach ($File in $IncludedFiles) {
        $RelativePath = Get-RelativePathSafe -BasePath $ProjectRoot -FullPath $File.FullName
        Add-DumpLine "- $RelativePath"
    }
}

Add-DumpLine ""
Add-DumpLine "==================== FILE CONTENTS ===================="
Add-DumpLine ""

$CurrentIndex = 0

foreach ($File in $IncludedFiles) {
    $CurrentIndex++
    $RelativePath = Get-RelativePathSafe -BasePath $ProjectRoot -FullPath $File.FullName

    $Percent = 0
    if ($IncludedFiles.Count -gt 0) {
        $Percent = [int](($CurrentIndex / $IncludedFiles.Count) * 100)
    }

    Write-Progress `
        -Activity "Creating ROM_FULL_DUMP.txt" `
        -Status "$CurrentIndex of $($IncludedFiles.Count): $RelativePath" `
        -PercentComplete $Percent

    Add-DumpLine "============================================================"
    Add-DumpLine "FILE: $RelativePath"
    Add-DumpLine "SIZE: $($File.Length) bytes"
    Add-DumpLine "LAST WRITE: $($File.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Add-DumpLine "============================================================"
    Add-DumpLine ""

    $Content = Get-SafeFileContent -File $File

    if ([string]::IsNullOrEmpty($Content)) {
        Add-DumpLine "[EMPTY FILE]"
    }
    else {
        Add-DumpLine $Content
    }

    Add-DumpLine ""
}

Write-Progress -Activity "Creating ROM_FULL_DUMP.txt" -Completed

$DumpItem = Get-Item -LiteralPath $OutputFile
$SizeMB = $DumpItem.Length / 1MB

Write-Host ""
Write-Host "DONE" -ForegroundColor Green
Write-Host "Dump created:" -ForegroundColor Green
Write-Host $OutputFile -ForegroundColor Cyan
Write-Host ""
Write-Host "Included files: $($IncludedFiles.Count)" -ForegroundColor Green
Write-Host "Excluded files: $ExcludedFilesCount" -ForegroundColor Green
Write-Host ("Dump size: {0:N2} MB" -f $SizeMB) -ForegroundColor Green
Write-Host ""
Write-Host "The dump excludes environment secrets, databases, patch, backup and virtual environments." -ForegroundColor Yellow
