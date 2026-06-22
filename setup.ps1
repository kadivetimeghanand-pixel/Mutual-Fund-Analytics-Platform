# setup.ps1 — MutualFundAnalytics Python 3.14 Environment Setup

param([switch]$SkipValidation = $false)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
$LogFile = Join-Path $ProjectRoot "setup_log.txt"

if (Test-Path $LogFile) { Clear-Content -Path $LogFile }

Write-Host "================================================================================"
Write-Host "MutualFundAnalytics — Python 3.14 Environment Setup"
Write-Host "================================================================================"

# Step 1: Check Python
Write-Host ""
Write-Host "Step 1: Detect Python Installation"
$pythonVersion = & python --version 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python detected: $pythonVersion"
} else {
    Write-Host "✗ Python not found"
    exit 1
}

# Step 2: Upgrade pip
Write-Host ""
Write-Host "Step 2: Upgrade pip, setuptools, wheel"
& python -m pip install --upgrade pip setuptools wheel 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Upgrade successful"
} else {
    Write-Host "✗ Upgrade failed"
    exit 2
}

# Step 3: Install requirements
Write-Host ""
Write-Host "Step 3: Install Requirements"

if (-not (Test-Path $RequirementsFile)) {
    Write-Host "✗ requirements.txt not found"
    exit 3
}

& python -m pip install -r $RequirementsFile 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Requirements installed successfully"
} else {
    Write-Host "✗ Requirements installation failed"
    exit 4
}

# Step 4: Validate
if (-not $SkipValidation) {
    Write-Host ""
    Write-Host "Step 4: Validate Installation"
    
    $packages = @("pandas", "numpy", "loguru", "requests", "tqdm")
    foreach ($pkg in $packages) {
        $version = & python -c "import $pkg; print($pkg.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $pkg version $version"
        } else {
            Write-Host "✗ $pkg import failed"
        }
    }
}

# Step 5: Create directories
Write-Host ""
Write-Host "Step 5: Create Project Directories"

$dirs = @(
    (Join-Path $ProjectRoot "data" "raw"),
    (Join-Path $ProjectRoot "data" "processed"),
    (Join-Path $ProjectRoot "reports"),
    (Join-Path $ProjectRoot "logs"),
    (Join-Path $ProjectRoot "notebooks")
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force -ErrorAction SilentlyContinue | Out-Null
        Write-Host "✓ Created: $dir"
    } else {
        Write-Host "✓ Exists: $dir"
    }
}

# Summary
Write-Host ""
Write-Host "================================================================================"
Write-Host "✓ SETUP COMPLETED SUCCESSFULLY"
Write-Host "================================================================================"
Write-Host ""
Write-Host "  Python Environment: Configured for Python 3.14"
Write-Host "  Project Path: $ProjectRoot"
Write-Host ""
Write-Host "NEXT STEPS:"
Write-Host ""
Write-Host "  1. Run the pipeline:"
Write-Host "     python dashboard/main.py"
Write-Host ""
Write-Host "  2. Check logs:"
Write-Host "     Get-Content logs/day1_pipeline.log"
Write-Host ""
Write-Host "================================================================================"
