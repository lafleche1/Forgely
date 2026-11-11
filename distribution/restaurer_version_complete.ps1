param([string]$DestinationRoot = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$project = Split-Path -Parent $PSScriptRoot
if ($DestinationRoot) { $project = [System.IO.Path]::GetFullPath($DestinationRoot) }
$stamp = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
$work = Join-Path $PSScriptRoot ('restauration-' + $stamp)
New-Item -ItemType Directory -Path $work | Out-Null
$archive = Join-Path $work 'Forgely-complet.zip'
$output = [System.IO.File]::Open($archive, [System.IO.FileMode]::CreateNew)
try {
    foreach ($part in $manifest.parts) {
        if ($part.name -notmatch '^part-[0-9]{3}\.bin$') { throw 'Nom de morceau invalide.' }
        $file = Join-Path (Join-Path $PSScriptRoot 'parts') $part.name
        $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $part.sha256) { throw ('Morceau incomplet ou modifié : ' + $part.name) }
        $partStream = [System.IO.File]::OpenRead($file)
        try { $partStream.CopyTo($output) } finally { $partStream.Dispose() }
    }
} finally { $output.Dispose() }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.sha256) {
    throw 'Empreinte de la version complète incorrecte.'
}
$target = [System.IO.Path]::GetFullPath((Join-Path $project ('Forgely-complet-' + $stamp)))
$prefix = $target + [System.IO.Path]::DirectorySeparatorChar
$zip = [System.IO.Compression.ZipFile]::OpenRead($archive)
try {
    foreach ($entry in $zip.Entries) {
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $target $entry.FullName))
        if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'Chemin interdit dans la version complète.'
        }
    }
} finally { $zip.Dispose() }
Expand-Archive -LiteralPath $archive -DestinationPath $target
Write-Host ''
Write-Host ('Version complète restaurée dans : ' + $target)
Write-Host 'Ouvrez OUVRIR FORGELY.bat pour le copilote, ou Entrainement_Forgely.exe pour l entrainement.'
