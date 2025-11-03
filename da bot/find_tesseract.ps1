# Script to find and add Tesseract to PATH
Write-Host "Searching for Tesseract installation..." -ForegroundColor Yellow

# Common installation locations
$searchPaths = @(
    "C:\Program Files\Tesseract-OCR",
    "C:\Program Files (x86)\Tesseract-OCR",
    "$env:LOCALAPPDATA\Tesseract-OCR",
    "$env:ProgramFiles\Tesseract-OCR",
    "$env:ProgramFiles(x86)\Tesseract-OCR"
)

$found = $null
foreach ($path in $searchPaths) {
    if (Test-Path "$path\tesseract.exe") {
        $found = $path
        Write-Host "Found Tesseract at: $found" -ForegroundColor Green
        break
    }
}

if (-not $found) {
    Write-Host "Tesseract not found in common locations." -ForegroundColor Red
    Write-Host "Please enter the full path to Tesseract-OCR folder (e.g., C:\Program Files\Tesseract-OCR):"
    $found = Read-Host
    if (-not (Test-Path "$found\tesseract.exe")) {
        Write-Host "Invalid path. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Check if already in PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -like "*$found*") {
    Write-Host "Tesseract is already in your User PATH!" -ForegroundColor Green
    exit 0
}

# Add to User PATH
Write-Host "Adding to User PATH..." -ForegroundColor Yellow
$newPath = $currentPath + ";$found"
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "Successfully added to PATH!" -ForegroundColor Green
Write-Host "Please close and reopen your terminal/application for changes to take effect." -ForegroundColor Yellow


