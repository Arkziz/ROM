#requires -Version 5.1

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

# Use the folder where this script is located as the project root.
# This avoids encoding problems in paths with non-ASCII characters.
$ProjectRoot = $PSScriptRoot
$OutputFileName = "ROM_FULL_DUMP.txt"
$OutputFile = Join-Path $ProjectRoot $OutputFileName

# Directories excluded at any nesting level.
$ExcludeDirectoryNames = @(
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".vs",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".hypothesis",
    "htmlcov",
    "coverage",
    "node_modules",
    "dist",
    "build",
    "logs",
    "log",
    "tmp",
    "temp",
    "cache",
    "patch",
    "backup",
    "MD",
    "simulation_reports",
    "reports"
)

# Exact file names that must never be included.
$ExcludeExactFileNames = @(
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "secrets.json",
    "credentials.json",
    "service-account.json",
    "game.db",
    "game.db-shm",
    "game.db-wal",
    "changes.diff"
)

# File-name patterns excluded for security or because they are binary/generated.
$ExcludeFilePatterns = @(
    "ROM_FULL_DUMP*.txt",
    ".env.*",
    "*.pem",
    "*.key",
    "*.pfx",
    "*.p12",
    "*.jks",
    "*.keystore",
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

# Only known text-based formats are included.
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
    $BaseWithSeparator = $NormalizedBase + [System.IO.Path]::DirectorySeparatorChar

    if ($FullPath.StartsWith($BaseWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $FullPath.Substring($BaseWithSeparator.Length)
    }

    if ($FullPath.Equals($NormalizedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        return ""
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

function Get-FileDecision {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File
    )

    $RelativePath = Get-RelativePathSafe -BasePath $ProjectRoot -FullPath $File.FullName
    $RelativeDirectory = Split-Path -Path $RelativePath -Parent

    if (Test-IsExcludedDirectory -RelativeDirectory $RelativeDirectory) {
        return "ExcludedDirectory"
    }

    if (Test-IsExcludedFileName -FileName $File.Name) {
        return "ExcludedFileName"
    }

    if (-not (Test-IsAllowedTextFile -File $File)) {
        return "UnsupportedFileType"
    }

    return "Include"
}

function Get-SafeFileContent {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File
    )

    try {
        return [System.IO.File]::ReadAllText(
            $File.FullName,
            [System.Text.UTF8Encoding]::new($false, $true)
        )
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

$IncludedFilesList = New-Object System.Collections.Generic.List[System.IO.FileInfo]
$ExclusionStats = @{
    ExcludedDirectory  = 0
    ExcludedFileName   = 0
    UnsupportedFileType = 0
}

foreach ($File in $AllFiles) {
    $Decision = Get-FileDecision -File $File

    if ($Decision -eq "Include") {
        $IncludedFilesList.Add($File)
    }
    else {
        $ExclusionStats[$Decision]++
    }
}

$IncludedFiles = @($IncludedFilesList | Sort-Object FullName)
$ExcludedFilesCount = $AllFiles.Count - $IncludedFiles.Count

$IncludedSourceBytes = 0L
foreach ($File in $IncludedFiles) {
    $IncludedSourceBytes += $File.Length
}
$IncludedSourceMB = $IncludedSourceBytes / 1MB

$CreatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
$PowerShellVersion = $PSVersionTable.PSVersion.ToString()
$Writer = $null

try {
    # UTF-8 with BOM is used for reliable display in Windows PowerShell 5.1 and text editors.
    $Utf8WithBom = New-Object System.Text.UTF8Encoding($true)
    $Writer = New-Object System.IO.StreamWriter($OutputFile, $false, $Utf8WithBom)

    $Writer.WriteLine("============================================================")
    $Writer.WriteLine("ROM PROJECT SAFE FULL DUMP")
    $Writer.WriteLine("============================================================")
    $Writer.WriteLine("")
    $Writer.WriteLine("Created: $CreatedAt")
    $Writer.WriteLine("Project root: $ProjectRoot")
    $Writer.WriteLine("PowerShell: $PowerShellVersion")
    $Writer.WriteLine("Scanned files: $($AllFiles.Count)")
    $Writer.WriteLine("Included files: $($IncludedFiles.Count)")
    $Writer.WriteLine("Excluded files: $ExcludedFilesCount")
    $Writer.WriteLine(("Included source size: {0:N2} MB" -f $IncludedSourceMB))
    $Writer.WriteLine("Per-file size limit: none")
    $Writer.WriteLine("")
    $Writer.WriteLine("EXCLUSION STATISTICS:")
    $Writer.WriteLine("- excluded directory: $($ExclusionStats.ExcludedDirectory)")
    $Writer.WriteLine("- excluded file name or pattern: $($ExclusionStats.ExcludedFileName)")
    $Writer.WriteLine("- unsupported file type: $($ExclusionStats.UnsupportedFileType)")
    $Writer.WriteLine("")
    $Writer.WriteLine("SECURITY AND SIZE EXCLUSIONS:")
    $Writer.WriteLine("- environment secrets and common key-store files")
    $Writer.WriteLine("- SQLite databases and WAL/SHM files")
    $Writer.WriteLine("- virtual environments")
    $Writer.WriteLine("- IDE metadata")
    $Writer.WriteLine("- Git and GitHub metadata")
    $Writer.WriteLine("- patch and backup history")
    $Writer.WriteLine("- reports, simulations and full MD documentation")
    $Writer.WriteLine("- caches and compiled files")
    $Writer.WriteLine("- binary and archive files")
    $Writer.WriteLine("- previous ROM_FULL_DUMP files")
    $Writer.WriteLine("")
    $Writer.WriteLine("==================== PROJECT TREE ====================")
    $Writer.WriteLine("")
    $Writer.WriteLine($ProjectRoot)

    if ($IncludedFiles.Count -eq 0) {
        $Writer.WriteLine("[NO FILES INCLUDED]")
    }
    else {
        foreach ($File in $IncludedFiles) {
            $RelativePath = Get-RelativePathSafe -BasePath $ProjectRoot -FullPath $File.FullName
            $Writer.WriteLine("- $RelativePath")
        }
    }

    $Writer.WriteLine("")
    $Writer.WriteLine("==================== FILE CONTENTS ===================")
    $Writer.WriteLine("")

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

        $Writer.WriteLine("============================================================")
        $Writer.WriteLine("FILE: $RelativePath")
        $Writer.WriteLine("SIZE: $($File.Length) bytes")
        $Writer.WriteLine("LAST WRITE: $($File.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))")
        $Writer.WriteLine("============================================================")
        $Writer.WriteLine("")

        $Content = Get-SafeFileContent -File $File

        if ([string]::IsNullOrEmpty($Content)) {
            $Writer.WriteLine("[EMPTY FILE]")
        }
        else {
            $Writer.Write($Content)
            if (-not $Content.EndsWith("`n")) {
                $Writer.WriteLine("")
            }
        }

        $Writer.WriteLine("")
    }
}
catch {
    Write-Progress -Activity "Creating ROM_FULL_DUMP.txt" -Completed
    Write-Host ""
    Write-Host "ERROR: Failed to create the dump." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
finally {
    if ($null -ne $Writer) {
        $Writer.Flush()
        $Writer.Dispose()
    }
}

Write-Progress -Activity "Creating ROM_FULL_DUMP.txt" -Completed

if (-not (Test-Path -LiteralPath $OutputFile -PathType Leaf)) {
    Write-Host "ERROR: Dump file was not created." -ForegroundColor Red
    exit 1
}

$DumpItem = Get-Item -LiteralPath $OutputFile
$SizeMB = $DumpItem.Length / 1MB

Write-Host ""
Write-Host "DONE" -ForegroundColor Green
Write-Host "Dump created:" -ForegroundColor Green
Write-Host $OutputFile -ForegroundColor Cyan
Write-Host ""
Write-Host "Scanned files: $($AllFiles.Count)" -ForegroundColor Green
Write-Host "Included files: $($IncludedFiles.Count)" -ForegroundColor Green
Write-Host "Excluded files: $ExcludedFilesCount" -ForegroundColor Green
Write-Host ("Included source size: {0:N2} MB" -f $IncludedSourceMB) -ForegroundColor Green
Write-Host ("Dump size: {0:N2} MB" -f $SizeMB) -ForegroundColor Green
Write-Host ""
Write-Host "No per-file size limit is applied." -ForegroundColor Yellow
Write-Host "The dump excludes secrets, databases, patch, backup, reports, MD and virtual environments." -ForegroundColor Yellow
