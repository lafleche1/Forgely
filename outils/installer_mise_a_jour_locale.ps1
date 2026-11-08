$ErrorActionPreference = 'Stop'
try {
    $package = Split-Path $PSScriptRoot -Parent
    $payload = Join-Path $package 'mise_a_jour_video'
    if (-not (Test-Path (Join-Path $payload 'manifest.json'))) { throw 'Paquet incomplet : extrais toute l archive ZIP avant de lancer cet installateur.' }
    $candidates = @($package, (Split-Path $package -Parent))
    foreach ($base in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('MyDocuments'), (Join-Path $env:USERPROFILE 'Downloads'))) {
        if ($base) { $candidates += (Join-Path $base 'Forgely') }
    }
    $matches = @($candidates | Select-Object -Unique | Where-Object { Test-Path (Join-Path $_ 'Application\forgely.py') })
    $root = $null
    if ($matches.Count -eq 1) { $root = $matches[0] }
    if (-not $root) {
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = 'Selectionne ton dossier Forgely, celui qui contient Application.'
        $dialog.ShowNewFolderButton = $false
        if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'Installation annulee ; aucun fichier remplace.' }
        $root = $dialog.SelectedPath
        $dialog.Dispose()
    }
    if (-not (Test-Path (Join-Path $root 'Application\forgely.py'))) { throw 'Ce dossier ne contient pas les sources de Forgely (Application\forgely.py).' }
    if (Get-Process -Name Forgely -ErrorAction SilentlyContinue) { throw 'Ferme Forgely puis relance cet installateur.' }
    $python = $null
    foreach ($candidate in @((Join-Path $root 'Application\.venv\Scripts\python.exe'), (Join-Path $root '.venv\Scripts\python.exe'))) {
        if (Test-Path $candidate) { $python = $candidate; break }
    }
    $prefix = @()
    if (-not $python) {
        $command = Get-Command py -ErrorAction SilentlyContinue
        if ($command) { $python = $command.Source; $prefix = @('-3') }
        else {
            $command = Get-Command python -ErrorAction SilentlyContinue
            if ($command) { $python = $command.Source }
        }
    }
    if (-not $python) { throw 'Python introuvable. Cette mise a jour necessite la version source de Forgely et son environnement Python.' }
    Write-Host "Installation cible : $root"
    Write-Host 'Les fichiers remplaces seront sauvegardes. Les versions inconnues seront refusees.'
    & $python @prefix (Join-Path $PSScriptRoot 'mettre_a_jour_prix_tylezia.py') --root $root --payload $payload
    if ($LASTEXITCODE -ne 0) { throw 'La mise a jour a ete refusee ou a echoue. Lis le diagnostic ci-dessus.' }
    Write-Host ''
    Write-Host 'Mise a jour appliquee. Relance Forgely avec LANCER_FORGELY_MIS_A_JOUR.bat dans ton dossier Forgely.'
    Write-Host 'Ce lanceur utilise les sources actualisees, meme si un ancien EXE est encore present.'
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
