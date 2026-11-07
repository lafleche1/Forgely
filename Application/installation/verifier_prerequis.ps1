# Verification idempotente des prerequis OCR pour Forgely.
# Le programme Python est deja embarque par PyInstaller : ne pas installer Python.
$ErrorActionPreference = 'Stop'
$log = Join-Path $env:LOCALAPPDATA 'Forgely\installation-ocr.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
function Log([string]$message) { "$(Get-Date -Format s) $message" | Out-File -FilePath $log -Append -Encoding utf8 }
function Find-Tesseract {
    $candidates = @(
      (Join-Path $env:ProgramFiles 'Tesseract-OCR\tesseract.exe'),
      (Join-Path ${env:ProgramFiles(x86)} 'Tesseract-OCR\tesseract.exe'),
      (Join-Path $env:LOCALAPPDATA 'Programs\Tesseract-OCR\tesseract.exe')
    )
    $cmd = Get-Command tesseract.exe -ErrorAction SilentlyContinue
    if ($cmd) { $candidates += $cmd.Source }
    foreach ($p in $candidates) { if ($p -and (Test-Path $p)) { return $p } }
    return $null
}
function Has-French([string]$exe) {
    if (-not $exe) { return $false }
    try { $langs = & $exe --list-langs 2>&1; return [bool]($langs | Where-Object { $_ -match '^fra\s*$' }) }
    catch { return $false }
}
Log 'Debut verification OCR'
$exe = Find-Tesseract
if (-not $exe) {
    Log 'Tesseract absent : tentative installation via winget'
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { Log 'winget indisponible'; exit 10 }
    & $winget.Source install --id UB-Mannheim.TesseractOCR --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
    $result = $LASTEXITCODE
    $exe = Find-Tesseract
    if (-not $exe) { Log "Installation Tesseract non confirmee (code $result)"; exit 11 }
}
Log "Tesseract detecte : $exe"
if (Has-French $exe) { Log 'Langue fra presente : aucune reinstallation'; exit 0 }
Log 'Langue fra manquante : installation du seul fichier linguistique'
# La langue est telechargee dans le dossier utilisateur, sans modifier Tesseract existant.
$target = Join-Path $env:LOCALAPPDATA 'Forgely\tessdata'
New-Item -ItemType Directory -Force -Path $target | Out-Null
$file = Join-Path $target 'fra.traineddata'
if (-not (Test-Path $file)) {
    try { Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata_fast/raw/refs/heads/main/fra.traineddata' -OutFile $file -MaximumRedirection 5 }
    catch { Log "Telechargement fra echoue : $_"; exit 12 }
}
# Copier la langue anglaise existante pour garantir fra+eng dans ce dossier.
$eng = Join-Path (Split-Path $exe) 'tessdata\eng.traineddata'
if (Test-Path $eng) { Copy-Item $eng (Join-Path $target 'eng.traineddata') -Force }
[Environment]::SetEnvironmentVariable('FORGELY_TESSDATA_DIR', $target, 'User')
Log "Langue fra installee dans $target"
exit 0
