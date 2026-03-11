param(
    [Parameter(Mandatory = $true)]
    [string]$Ean,

    [Parameter(Mandatory = $true)]
    [string]$OutputFolder
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"

$LookupScript = Join-Path $ScriptDir "ean_lookup.py"
$RequirementsIn = Join-Path $ScriptDir "requirements.in"
$RequirementsTxt = Join-Path $ScriptDir "requirements.txt"

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"

if (-not (Test-Path $LookupScript)) {
    throw "Could not find ean_lookup.py in script folder: $ScriptDir"
}

if (-not (Test-Path $RequirementsIn)) {
    throw "Could not find requirements.in in script folder: $ScriptDir"
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv $VenvDir
}

Write-Host "Installing requirements..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install pip-tools
& $VenvPython -m piptools compile --strip-extras -o $RequirementsTxt $RequirementsIn
& $VenvPython -m piptools sync $RequirementsTxt

Write-Host "Running lookup..."
& $VenvPython $LookupScript $Ean -o $OutputFolder

Write-Host "Done."
