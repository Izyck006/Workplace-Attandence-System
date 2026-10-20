[Setup]
AppId=RandaframesAttendanceV2
AppName=Randaframes Attendance
AppVersion=2.0.0
AppPublisher=Zicron
AppPublisherURL=https://port-sage-delta.vercel.app/
AppSupportURL=https://port-sage-delta.vercel.app/
AppUpdatesURL=https://port-sage-delta.vercel.app/
VersionInfoCompany=Zicron
VersionInfoDescription=Randaframes Attendance Setup
VersionInfoCopyright=Copyright (C) 2026 Zicron
VersionInfoVersion=2.0.0.0
DefaultDirName={autopf}\Randaframes Attendance
DefaultGroupName=Randaframes Attendance
OutputDir=..\release
OutputBaseFilename=RandaframesAttendance-Setup-2.0.0
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\RandaframesAttendance.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "..\dist\RandaframesAttendance\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "vendor\IBScanDriver Setup.msi"; Flags: dontcopy

[Icons]
Name: "{group}\Randaframes Attendance"; Filename: "{app}\RandaframesAttendance.exe"
Name: "{autodesktop}\Randaframes Attendance"; Filename: "{app}\RandaframesAttendance.exe"

[Run]
Filename: "{app}\RandaframesAttendance.exe"; Description: "Open Randaframes Attendance"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  ExtractTemporaryFile('IBScanDriver Setup.msi');
  if not Exec(ExpandConstant('{sys}\msiexec.exe'),
    '/i "' + ExpandConstant('{tmp}\IBScanDriver Setup.msi') + '" /passive /norestart',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := 'Could not start the scanner driver installer. Check administrator rights and retry.'
  else if ResultCode = 3010 then
    NeedsRestart := True
  else if (ResultCode <> 0) and (ResultCode <> 1638) then
    Result := 'Scanner driver installation failed (code ' + IntToStr(ResultCode) + '). Resolve this before installing the attendance app.';
end;
