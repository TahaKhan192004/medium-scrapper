param(
  [Parameter(Mandatory = $false)]
  [string]$InstallDir = "$HOME\\medium-scraper-mcp",

  [Parameter(Mandatory = $false)]
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "WARNING: $msg" -ForegroundColor Yellow }
function Assert-Ok($what) {
  if ($LASTEXITCODE -ne 0) { throw "$what failed (exit code $LASTEXITCODE)." }
}

Write-Step "Installing Medium Scraper MCP server"
Write-Host "Install dir: $InstallDir"
Write-Host "Python:      $PythonExe"

if (-not (Test-Path $InstallDir)) {
  Write-Step "Creating install directory"
  New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

Write-Step "Copying project files"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path (Join-Path $repoRoot "requirements.txt"))) {
  throw "requirements.txt not found next to install.ps1. Place install.ps1 in the project root and run it again."
}

Get-ChildItem -Path $repoRoot -Force | ForEach-Object {
  if ($_.Name -in @(".venv", "__pycache__", ".git")) { return }
  Copy-Item -Recurse -Force -Path $_.FullName -Destination (Join-Path $InstallDir $_.Name)
}

Push-Location $InstallDir
try {
  Write-Step "Creating virtual environment (.venv)"
  & $PythonExe -m venv .venv
  Assert-Ok "python -m venv"

  $venvPy = Join-Path $InstallDir ".venv\\Scripts\\python.exe"
  if (-not (Test-Path $venvPy)) {
    throw "venv python not found at $venvPy"
  }

  Write-Step "Installing dependencies"
  & $venvPy -m pip install -r requirements.txt
  Assert-Ok "pip install"

  Write-Step "Done"
  Write-Host ""
  Write-Host "Next:" -ForegroundColor Green
  Write-Host "1) Configure Claude Desktop to use:"
  Write-Host "   command: $venvPy"
  Write-Host "   args:    $InstallDir\\mcp_server.py"
  Write-Host "2) Restart Claude Desktop."
  Write-Host ""
  Write-Host "Optional quick test:"
  Write-Host "  $venvPy $InstallDir\\mcp_server.py"
} finally {
  Pop-Location
}
