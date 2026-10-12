# Installe la tache de sauvegarde (tous les 5 jours a 15 h) pour l'utilisateur Windows courant.
# Lancer depuis PowerShell : .\register_backup_task.ps1

$ErrorActionPreference = "Stop"

$TaskName = "BackupDistantSpectacles"
$ProjectDir = $PSScriptRoot
$BatFile = Join-Path $ProjectDir "backup_distant.bat"
$PythonExe = Join-Path $env:LOCALAPPDATA "Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\Local\flask-spectacles-backup\Scripts\python.exe"

if (-not (Test-Path $BatFile)) {
    throw "Script de sauvegarde introuvable : $BatFile"
}
if (-not (Test-Path $PythonExe)) {
    throw "Environnement Python de sauvegarde introuvable : $PythonExe"
}

$NextRun = Get-Date -Hour 15 -Minute 0 -Second 0
if ($NextRun -le (Get-Date)) {
    $NextRun = $NextRun.AddDays(1)
}

$Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$Command = [System.Security.SecurityElement]::Escape($env:ComSpec)
$Arguments = [System.Security.SecurityElement]::Escape('/d /c ""{0}" --scheduled"' -f $BatFile)
$WorkingDirectory = [System.Security.SecurityElement]::Escape($ProjectDir)
$StartBoundary = $NextRun.ToString("yyyy-MM-ddTHH:mm:ss")

$TaskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Sauvegarde PostgreSQL et S3 vers Dropbox, tous les 5 jours a 15 h.</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$StartBoundary</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>5</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$Sid</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT4H</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$Command</Command>
      <Arguments>$Arguments</Arguments>
      <WorkingDirectory>$WorkingDirectory</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

Register-ScheduledTask -TaskName $TaskName -Xml $TaskXml -Force | Out-Null
Write-Host "Tache planifiee installee : $TaskName"
Write-Host "Projet : $ProjectDir"
Write-Host "Prochaine execution : $StartBoundary (puis tous les 5 jours a 15 h)"
