[Setup]
AppName=DAL ERP
AppVersion=7.8
AppPublisher=DAL ERP
DefaultDirName={autopf}\DAL ERP
DefaultGroupName=DAL ERP
OutputDir=Kurulum
OutputBaseFilename=DAL_ERP_v79_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Ek seçenekler:"

[Files]
Source: "dist\DAL ERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DAL ERP"; Filename: "{app}\DAL ERP.exe"
Name: "{commondesktop}\DAL ERP"; Filename: "{app}\DAL ERP.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DAL ERP.exe"; Description: "DAL ERP'yi çalıştır"; Flags: nowait postinstall skipifsilent
