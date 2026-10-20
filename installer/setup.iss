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
Source: "vendor\IBScanDriver Setup.msi"; DestDir: "{app}\drivers"; Flags: ignoreversion

[Icons]
Name: "{group}\Randaframes Attendance"; Filename: "{app}\RandaframesAttendance.exe"
Name: "{group}\Install Scanner Driver"; Filename: "{sys}\msiexec.exe"; Parameters: "/i ""{app}\drivers\IBScanDriver Setup.msi"""
Name: "{autodesktop}\Randaframes Attendance"; Filename: "{app}\RandaframesAttendance.exe"

[Run]
Filename: "{app}\RandaframesAttendance.exe"; Description: "Open Randaframes Attendance"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
var
  RestartNeeded: Boolean;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  DriverPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    DriverPath := ExpandConstant('{app}\drivers\IBScanDriver Setup.msi');
    if FileExists(DriverPath) then
    begin
      if Exec(ExpandConstant('{sys}\msiexec.exe'),
        '/i "' + DriverPath + '" /passive /norestart',
        '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode) then
      begin
        if ResultCode = 3010 then
          RestartNeeded := True
        else if (ResultCode <> 0) and (ResultCode <> 1638) then
        begin
          MsgBox('Scanner driver setup returned status ' + IntToStr(ResultCode) + ' (the driver may already be installed).'#13#10 +
            'Randaframes Attendance has installed successfully.'#13#10#13#10 +
            'If your scanner is not detected, you can run the driver installer manually anytime from:'#13#10 +
            DriverPath, mbInformation, MB_OK);
        end;
      end;
    end;
  end;
end;

function NeedRestart(): Boolean;
begin
  Result := RestartNeeded;
end;
