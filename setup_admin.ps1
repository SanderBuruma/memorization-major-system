# Run this script as Administrator (one-time setup)
# Adds hosts entry and port proxy for http://memorization.local

$ErrorActionPreference = 'Stop'

# 1. Add hosts entry (if not already present)
$hostsFile = 'C:\Windows\System32\drivers\etc\hosts'
$entry = '127.0.0.1  memorization.local'
$content = Get-Content $hostsFile -Raw
if ($content -notmatch 'memorization\.local') {
    Add-Content -Path $hostsFile -Value "`n$entry" -Encoding ASCII
    Write-Host "Added hosts entry: $entry" -ForegroundColor Green
} else {
    Write-Host "Hosts entry already exists" -ForegroundColor Yellow
}

# 2. Add port proxy: port 80 -> 8734
netsh interface portproxy delete v4tov4 listenport=80 listenaddress=127.0.0.1 2>$null
netsh interface portproxy add v4tov4 listenport=80 listenaddress=127.0.0.1 connectport=8734 connectaddress=127.0.0.1
Write-Host "Port proxy: 80 -> 8734 configured" -ForegroundColor Green

# 3. Create scheduled task to run server at logon
$pythonPath = (Get-Command python).Source
$taskName = 'MajorSystemTrainer'
$action = New-ScheduledTaskAction -Execute $pythonPath.Replace('python.exe','pythonw.exe') -Argument 'server.py' -WorkingDirectory 'C:\Projects\memorization-major-system'
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Major System memorization trainer (http://memorization.local)' -RunLevel Highest
Write-Host "Scheduled task '$taskName' created (runs at logon)" -ForegroundColor Green

# 4. Start the task now
Start-ScheduledTask -TaskName $taskName
Write-Host "`nServer starting... visit http://memorization.local" -ForegroundColor Cyan
