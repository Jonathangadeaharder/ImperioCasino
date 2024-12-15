# Ensure elevated privileges
if (-not ([Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Restarting as Administrator..."
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`"" -Verb RunAs
    Exit
}

# Define paths and commands (rest of your script remains the same)
$blackjackPath = "C:\Users\Jonandrop\IdeaProjects\ImperioCasino\blackjack-master"
$cherryCharmPath = "C:\Users\Jonandrop\IdeaProjects\ImperioCasino\cherry-charm"
$roulettePath = "C:\Users\Jonandrop\IdeaProjects\ImperioCasino\roulette"
$sessionManagementPath = "C:\Users\Jonandrop\IdeaProjects\ImperioCasino\session_management"

$flaskCommand = "flask run"
$cherryCharmCommand = "yarn dev"

function Start-Server($path, $command, $title) {
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd $path; $command" -WindowStyle Normal -WorkingDirectory $path
    Start-Sleep -Seconds 1
}

Write-Host "Starting Blackjack server..." -ForegroundColor Green
Start-Server $blackjackPath $flaskCommand "Blackjack Server"

Write-Host "Starting Cherry Charm server..." -ForegroundColor Green
Start-Server $cherryCharmPath $cherryCharmCommand "Cherry Charm Server"

Write-Host "Starting Roulette server..." -ForegroundColor Green
Start-Server $roulettePath $flaskCommand "Roulette Server"

Write-Host "Starting Session Management server..." -ForegroundColor Green
Start-Server $sessionManagementPath $flaskCommand "Session Management Server"

Write-Host "All servers started. Check individual windows for output." -ForegroundColor Yellow
