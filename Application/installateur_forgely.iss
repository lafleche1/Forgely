#define AppName "Forgely"
#define AppVersion "0.20.15"
[Setup]
AppId={{A7E3178F-04A1-4820-A68E-0B8A430C9741}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Projet Forgely
DefaultDirName={localappdata}\Programs\Forgely
DefaultGroupName=Forgely
OutputDir=installateur
OutputBaseFilename=Forgely-Setup-{#AppVersion}
SetupIconFile=assets\forgely.ico
UninstallDisplayIcon={app}\Forgely.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Files]
Source: "dist\Forgely\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: "installation\verifier_prerequis.ps1"; DestDir: "{app}\installation"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Forgely"; Filename: "{app}\Forgely.exe"; IconFilename: "{app}\Forgely.exe"
Name: "{autodesktop}\Forgely"; Filename: "{app}\Forgely.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: checkedonce

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\installation\verifier_prerequis.ps1"""; Description: "Verifier Tesseract OCR et installer uniquement les composants manquants"; Flags: runhidden waituntilterminated
Filename: "{app}\Forgely.exe"; Description: "Lancer Forgely"; Flags: nowait postinstall skipifsilent
