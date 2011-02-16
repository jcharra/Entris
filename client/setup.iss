[Setup]
AppName=Entris
AppVersion=2.00
DefaultDirName={pf}\Entris
DefaultGroupName=Entris
UninstallDisplayIcon={app}\Entris.exe
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:Inno Setup Examples Output

[Files]
Source: "Entris.exe"; DestDir: "{app}"
Source: "jack_type.ttf"; DestDir: "{app}"
Source: "w9xpopen.exe"; DestDir: "{app}";
Source: "README.rtf"; DestDir: "{app}"; Flags: isreadme
Source: "sound\kraut.mid"; DestDir: "{app}\sound";
Source: "sound\quack.ogg"; DestDir: "{app}\sound";

[Icons]
Name: "{group}\Entris"; Filename: "{app}\Entris.exe"
