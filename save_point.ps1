# ====================================================================
# save_point.ps1 - Cree un point de restauration Git (tag) horodate
# et le pousse sur GitHub.
#
# Usage :
#   .\save_point.ps1                         # tag automatique avec date/heure
#   .\save_point.ps1 -Message "avant refonte catalogue"
#   .\save_point.ps1 -Name "v1-launch"       # nom personnalise
#   .\save_point.ps1 -NoPush                 # cree le tag local seulement
#
# Double-clic : passer par save_point.bat
# ====================================================================

param(
    [string]$Message = "",
    [string]$Name = "",
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " CREATION D'UN POINT DE RESTAURATION GIT" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Verifier qu'on est bien dans un depot git
try {
    $branche = (git rev-parse --abbrev-ref HEAD).Trim()
} catch {
    Write-Host "[X] Ce dossier n'est pas un depot Git." -ForegroundColor Red
    exit 1
}

# 2. Verifier qu'il n'y a pas de changements non-committes
$dirty = (git status --porcelain)
if ($dirty) {
    Write-Host ""
    Write-Host "[!] ATTENTION : il y a des changements NON COMMITES :" -ForegroundColor Yellow
    Write-Host $dirty -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Le tag sera pose sur le DERNIER commit, pas sur ces changements." -ForegroundColor Yellow
    Write-Host ""
    $reply = Read-Host "Continuer quand meme ? (o/N)"
    if ($reply -ne "o" -and $reply -ne "O" -and $reply -ne "oui") {
        Write-Host "Annule." -ForegroundColor Yellow
        exit 0
    }
}

# 3. Construire le nom du tag
if ([string]::IsNullOrWhiteSpace($Name)) {
    $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
    $TagName = "stable-live-$stamp"
} else {
    $TagName = $Name
}

# 4. Verifier que le tag n'existe pas deja
$existing = git tag -l $TagName
if ($existing) {
    Write-Host "[X] Le tag '$TagName' existe deja." -ForegroundColor Red
    Write-Host "    Utilisez -Name 'autre-nom' ou attendez une minute." -ForegroundColor Red
    exit 1
}

# 5. Message de tag
$commit = (git rev-parse --short HEAD).Trim()
$commitMsg = (git log -1 --pretty=%s).Trim()
if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "Point de restauration cree le $(Get-Date -Format 'dd/MM/yyyy HH:mm') sur la branche $branche (commit $commit : $commitMsg)"
} else {
    $Message = "$Message [cree le $(Get-Date -Format 'dd/MM/yyyy HH:mm'), branche $branche, commit $commit]"
}

Write-Host ""
Write-Host " Branche courante  : $branche" -ForegroundColor White
Write-Host " Commit courant    : $commit ($commitMsg)" -ForegroundColor White
Write-Host " Nom du tag        : $TagName" -ForegroundColor Green
Write-Host " Message           : $Message" -ForegroundColor Gray
Write-Host ""

# 6. Creer le tag
git tag -a $TagName -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Echec de creation du tag." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Tag local cree." -ForegroundColor Green

# 7. Pusher (sauf si -NoPush)
if ($NoPush) {
    Write-Host "[!] Push desactive (-NoPush). Le tag n'existe qu'en local." -ForegroundColor Yellow
    Write-Host "    Pour pousser plus tard : git push origin $TagName" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Push vers GitHub..." -ForegroundColor Cyan
    git push origin $TagName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Push echoue - le tag est cree en local seulement." -ForegroundColor Yellow
        Write-Host "    Reessayer plus tard : git push origin $TagName" -ForegroundColor Yellow
        exit 2
    }
    Write-Host "[OK] Tag pousse sur origin/$TagName" -ForegroundColor Green
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " POINT DE RESTAURATION CREE : $TagName" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Pour restaurer plus tard :" -ForegroundColor White
Write-Host "   git reset --hard $TagName                     # local uniquement" -ForegroundColor Gray
Write-Host "   git reset --hard $TagName ; git push --force-with-lease  # local + redeploy" -ForegroundColor Gray
Write-Host ""
Write-Host " Voir tous les points de restauration :" -ForegroundColor White
Write-Host "   git tag -l 'stable-live-*'" -ForegroundColor Gray
Write-Host ""
