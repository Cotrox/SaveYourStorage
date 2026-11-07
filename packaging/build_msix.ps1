param(
    [string]$Version = "1.0.0",
    [string]$Publisher = "CN=SaveYourStorage",
    [string]$MakeAppx = "",
    [string]$SignTool = "",
    [string]$Certificate = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "dist\SaveYourStorage"
$staging = Join-Path $PSScriptRoot "staging"
$output = Join-Path $PSScriptRoot "output"

if (-not (Test-Path (Join-Path $source "SaveYourStorage.exe"))) {
    throw "Build non trovato. Esegui prima build_exe.bat."
}

if (-not $MakeAppx) {
    $MakeAppx = (Get-Command makeappx.exe -ErrorAction SilentlyContinue).Source
}
if (-not $MakeAppx) {
    throw "makeappx.exe non trovato. Installa Windows SDK o passa -MakeAppx."
}

Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue
New-Item $staging -ItemType Directory | Out-Null
New-Item (Join-Path $staging "Assets") -ItemType Directory | Out-Null
New-Item $output -ItemType Directory -Force | Out-Null
Copy-Item (Join-Path $source "*") $staging -Recurse

Copy-Item (Join-Path $root "assets\store-logo.png") (Join-Path $staging "Assets\StoreLogo.png")
Copy-Item (Join-Path $root "assets\square150x150-logo.png") (Join-Path $staging "Assets\Square150x150Logo.png")
Copy-Item (Join-Path $root "assets\square44x44-logo.png") (Join-Path $staging "Assets\Square44x44Logo.png")

$manifest = Get-Content (Join-Path $PSScriptRoot "AppxManifest.xml") -Raw
$manifest = $manifest -replace 'Publisher="[^"]+"', ('Publisher="' + $Publisher + '"')
$manifest = $manifest -replace 'Version="1\.0\.0\.0"', ('Version="' + ($Version -replace '^v', '') + '.0"')
Set-Content (Join-Path $staging "AppxManifest.xml") $manifest -Encoding utf8

$msix = Join-Path $output "SaveYourStorage.msix"
Remove-Item $msix -Force -ErrorAction SilentlyContinue
& $MakeAppx pack /d $staging /p $msix /o
if ($LASTEXITCODE -ne 0) { throw "Creazione MSIX fallita." }

if ($Certificate) {
    if (-not $SignTool) {
        $SignTool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source
    }
    if (-not $SignTool) { throw "signtool.exe non trovato." }
    & $SignTool sign /fd SHA256 /a /f $Certificate $msix
    if ($LASTEXITCODE -ne 0) { throw "Firma MSIX fallita." }
}

Write-Host "MSIX creato: $msix"
