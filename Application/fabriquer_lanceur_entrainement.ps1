$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$compiler = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Compilateur Windows .NET Framework indisponible.' }
& $compiler /nologo /target:winexe /optimize+ /reference:System.Windows.Forms.dll "/win32icon:$PSScriptRoot\assets\forgely.ico" "/out:$projectDirectory\Entrainement_Forgely.exe" "$PSScriptRoot\lanceur_entrainement.cs"
if ($LASTEXITCODE -ne 0) { throw 'La compilation du lanceur a échoué.' }
