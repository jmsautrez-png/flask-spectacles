# ====================================================================
# Inscrit la tache planifiee Windows :
#   - Backup distant (PostgreSQL + photos S3 -> Dropbox)
#   - Tous les 15 du mois a 15h00
#
# Usage (clic droit -> Executer avec PowerShell, OU dans un terminal admin) :
#   powershell -ExecutionPolicy Bypass -File .\register_backup_task.ps1
# ====================================================================

$ErrorActionPreference = "Stop"

$TaskName    = "BackupDistantSpectacles"
$ProjectDir  = "C:\Users\utilisateur\Desktop\flask-spectacles-git\flask-spectacles"
$BatFile     = Join-Path $ProjectDir "backup_distant.bat"

if (-not (Test-Path $BatFile)) {
    Write-Host "[ERREUR] Fichier introuvable : $BatFile" -ForegroundColor Red
    exit 1
}

# Action : lancer le .bat dans le dossier projet
$Action = New-ScheduledTaskAction `
    -Execute $BatFile `
    -WorkingDirectory $ProjectDir

# Declencheur : tous les 15 du mois a 15h00
# (Trigger mensuel via classe COM car New-ScheduledTaskTrigger ne supporte pas -Monthly)
$ServiceObj = New-Object -ComObject Schedule.Service
$ServiceObj.Connect()
$Definition = $ServiceObj.NewTask(0)

$MonthlyTrigger = $Definition.Triggers.Create(4)  # 4 = TASK_TRIGGER_MONTHLY
$MonthlyTrigger.StartBoundary  = (Get-Date -Day 15 -Hour 15 -Minute 0 -Second 0).ToString("yyyy-MM-ddTHH:mm:ss")
$MonthlyTrigger.DaysOfMonth    = 1 -shl (15 - 1)  # bitmask : 15e jour
$MonthlyTrigger.MonthsOfYear   = 4095             # tous les mois (bitmask 12 bits)
$MonthlyTrigger.Enabled        = $true

# Parametres : reveille le PC, retente si echec, demarre meme sur batterie
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

# Compte utilisateur courant (interactif, pas besoin de mot de passe stocke)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

# On utilise Register-ScheduledTask pour l'action + settings + principal,
# et on remplace ensuite les triggers par notre trigger mensuel COM.
$Task = New-ScheduledTask `
    -Action $Action `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Backup mensuel : PostgreSQL Render + photos S3 vers Dropbox (15 du mois a 15h)."

# Supprime l'ancienne tache si elle existe
$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Host "Suppression de l'ancienne tache '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Enregistrement
Register-ScheduledTask -TaskName $TaskName -InputObject $Task | Out-Null

# Remplace les triggers par notre trigger mensuel (COM)
$RegTask = Get-ScheduledTask -TaskName $TaskName
$XmlPath = Join-Path $env:TEMP "$TaskName.xml"
Export-ScheduledTask -TaskName $TaskName | Out-File $XmlPath -Encoding Unicode

[xml]$Xml = Get-Content $XmlPath
$NsMgr = New-Object System.Xml.XmlNamespaceManager($Xml.NameTable)
$NsMgr.AddNamespace("t", "http://schemas.microsoft.com/windows/2004/02/mit/task")

$TriggersNode = $Xml.SelectSingleNode("//t:Triggers", $NsMgr)
$TriggersNode.RemoveAll() | Out-Null

$NewTrigger = $Xml.CreateElement("CalendarTrigger", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$Start = $Xml.CreateElement("StartBoundary", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$Start.InnerText = (Get-Date -Day 15 -Hour 15 -Minute 0 -Second 0).ToString("yyyy-MM-ddTHH:mm:ss")
$NewTrigger.AppendChild($Start) | Out-Null

$Enabled = $Xml.CreateElement("Enabled", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$Enabled.InnerText = "true"
$NewTrigger.AppendChild($Enabled) | Out-Null

$Schedule = $Xml.CreateElement("ScheduleByMonth", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$DaysOfMonth = $Xml.CreateElement("DaysOfMonth", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$Day = $Xml.CreateElement("Day", "http://schemas.microsoft.com/windows/2004/02/mit/task")
$Day.InnerText = "15"
$DaysOfMonth.AppendChild($Day) | Out-Null
$Schedule.AppendChild($DaysOfMonth) | Out-Null

$Months = $Xml.CreateElement("Months", "http://schemas.microsoft.com/windows/2004/02/mit/task")
foreach ($m in @("January","February","March","April","May","June","July","August","September","October","November","December")) {
    $Mn = $Xml.CreateElement($m, "http://schemas.microsoft.com/windows/2004/02/mit/task")
    $Months.AppendChild($Mn) | Out-Null
}
$Schedule.AppendChild($Months) | Out-Null
$NewTrigger.AppendChild($Schedule) | Out-Null

$TriggersNode.AppendChild($NewTrigger) | Out-Null
$Xml.Save($XmlPath)

# Re-enregistre la tache avec le XML corrige
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Register-ScheduledTask -TaskName $TaskName -Xml (Get-Content $XmlPath -Raw) -User "$env:USERDOMAIN\$env:USERNAME" | Out-Null

Remove-Item $XmlPath -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Tache planifiee creee : $TaskName" -ForegroundColor Green
Write-Host " Declenchement : tous les 15 du mois a 15h00" -ForegroundColor Green
Write-Host " Script execute : $BatFile" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Verifier :   Get-ScheduledTask -TaskName $TaskName"
Write-Host "Tester maintenant :  Start-ScheduledTask -TaskName $TaskName"
Write-Host "Supprimer :  Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
