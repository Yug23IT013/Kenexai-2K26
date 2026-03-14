# Schedule pipeline to run in 1 hour
$scriptPath = "C:\Users\Dell\OneDrive\Desktop\Football\run_pipeline.py"
$pythonExe = "D:\Program Files\Python\python.exe"
$workingDir = "C:\Users\Dell\OneDrive\Desktop\Football"

# Calculate time 1 hour from now
$futureTime = (Get-Date).AddHours(1)
$taskName = "FootballPipeline_$(Get-Date -Format 'HHmmss')"

# Create the action
$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "run_pipeline.py" `
    -WorkingDirectory $workingDir

# Create the trigger for 1 hour from now
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At $futureTime

# Create the task
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal

# Register the task
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force

Write-Host ""
Write-Host "========================================"
Write-Host "Pipeline scheduled successfully!"
Write-Host "========================================"
Write-Host "Task Name: $taskName"
Write-Host "Scheduled Time: $($futureTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "Status: Pipeline will run automatically in 1 hour"
Write-Host "========================================"
