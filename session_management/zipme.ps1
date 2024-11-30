# Define the name of the zip file
$ZIP_FILE = "session_management.zip"

Write-Host "Starting zipping process..."

# Exclude patterns
$excludeDirs = @('__pycache__')
$excludeFiles = @('zipme.ps1', $ZIP_FILE, 'scanner.py')
$excludePatterns = @('*.lock')

Write-Host "Excluding directories: $($excludeDirs -join ', ')"
Write-Host "Excluding files: $($excludeFiles -join ', ')"
Write-Host "Excluding patterns: $($excludePatterns -join ', ')"

$zipPath = Join-Path $PWD $ZIP_FILE

# Ensure any existing zip file is deleted
if (Test-Path $zipPath) {
    try {
        Remove-Item $zipPath -Force
        Write-Host "Removed existing zip file $ZIP_FILE"
    } catch {
        Write-Host "Could not remove existing zip file $ZIP_FILE. It may be in use."
        exit 1
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$rootDir = Get-Item -Path $PWD

$filesAdded = 0

try {
    $zipArchive = [System.IO.Compression.ZipFile]::Open($zipPath, [System.IO.Compression.ZipArchiveMode]::Create)

    $allFiles = Get-ChildItem -Path $rootDir -Recurse -File

    foreach ($file in $allFiles) {
        $relativePath = $file.FullName.Substring($rootDir.FullName.Length + 1)

        # Debugging
        Write-Host "Processing file: $relativePath"

        # Check if the file is the zip file itself
        if ($file.FullName -eq $zipPath) {
            Write-Host "Skipping zip file itself: $relativePath"
            continue
        }

        # Check if the file is in an excluded directory
        $inExcludedDir = $false
        foreach ($dir in $excludeDirs) {
            if ($file.FullName -like "*\$dir\*") {
                Write-Host "Skipping file in excluded directory: $relativePath"
                $inExcludedDir = $true
                break
            }
        }

        if ($inExcludedDir) {
            continue
        }

        # Check if the file name is in the excluded files list
        if ($excludeFiles -contains $file.Name) {
            Write-Host "Skipping excluded file: $relativePath"
            continue
        }

        # Check if the file matches any of the excluded patterns
        $matchesExcludedPattern = $false
        foreach ($pattern in $excludePatterns) {
            if ($file.Name -like $pattern) {
                Write-Host "Skipping file matching excluded pattern '$pattern': $relativePath"
                $matchesExcludedPattern = $true
                break
            }
        }

        if ($matchesExcludedPattern) {
            continue
        }

        # Add the file to the zip archive using the correct method
        Write-Host "Adding file: $relativePath"
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zipArchive, $file.FullName, $relativePath)

        $filesAdded++
    }
}
finally {
    if ($zipArchive) {
        $zipArchive.Dispose()
        Write-Host "Zip archive closed."
    }
}

Write-Host "Zipped $filesAdded files into $ZIP_FILE"
