#!/usr/bin/env powershell

# Kiro-mini Network Configuration Script
# This script helps configure the application to work with your machine's IP address

Write-Host "=== Kiro-mini Network Configuration ===" -ForegroundColor Green
Write-Host ""

# Get machine's IP addresses
Write-Host "Detecting your machine's IP addresses..." -ForegroundColor Yellow
$networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual" }

Write-Host "Available IP addresses:" -ForegroundColor Cyan
foreach ($adapter in $networkAdapters) {
    $interfaceAlias = (Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex).Name
    Write-Host "  - $($adapter.IPAddress) ($interfaceAlias)" -ForegroundColor White
}

Write-Host ""
Write-Host "Please select the IP address you want to use:" -ForegroundColor Yellow
$ipAddresses = $networkAdapters.IPAddress
for ($i = 0; $i -lt $ipAddresses.Count; $i++) {
    $interfaceAlias = (Get-NetAdapter -InterfaceIndex $networkAdapters[$i].InterfaceIndex).Name
    Write-Host "  [$($i + 1)] $($ipAddresses[$i]) ($interfaceAlias)"
}

do {
    $selection = Read-Host "Enter selection (1-$($ipAddresses.Count))"
    $selectionIndex = [int]$selection - 1
} while ($selectionIndex -lt 0 -or $selectionIndex -ge $ipAddresses.Count)

$selectedIP = $ipAddresses[$selectionIndex]
Write-Host "Selected IP: $selectedIP" -ForegroundColor Green

# Update frontend .env file
Write-Host ""
Write-Host "Updating frontend configuration..." -ForegroundColor Yellow

$envPath = "frontend/.env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath
    
    # Update API URL
    $envContent = $envContent -replace "REACT_APP_API_URL=.*", "REACT_APP_API_URL=http://${selectedIP}:8000"
    $envContent = $envContent -replace "REACT_APP_WS_URL=.*", "REACT_APP_WS_URL=ws://${selectedIP}:8000"
    $envContent = $envContent -replace "REACT_APP_ORTHANC_URL=.*", "REACT_APP_ORTHANC_URL=http://${selectedIP}:8042"
    
    Set-Content -Path $envPath -Value $envContent
    Write-Host "✓ Updated $envPath" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend .env file not found at $envPath" -ForegroundColor Red
}

# Update backend CORS configuration
Write-Host "Updating backend CORS configuration..." -ForegroundColor Yellow

$mainPyPath = "backend/main.py"
if (Test-Path $mainPyPath) {
    $mainPyContent = Get-Content $mainPyPath -Raw
    
    # Add the selected IP to CORS origins
    $corsPattern = '("http://192\.168\.\d+\.\d+:3000")'
    $newOrigin = "`"http://${selectedIP}:3000`""
    
    if ($mainPyContent -match $corsPattern) {
        $mainPyContent = $mainPyContent -replace $corsPattern, $newOrigin
    } else {
        # Add new origin to the list
        $insertPattern = '("http://frontend:3000",)'
        $replacement = "`"http://frontend:3000`",`n    $newOrigin,"
        $mainPyContent = $mainPyContent -replace $insertPattern, $replacement
    }
    
    Set-Content -Path $mainPyPath -Value $mainPyContent
    Write-Host "✓ Updated $mainPyPath" -ForegroundColor Green
} else {
    Write-Host "✗ Backend main.py file not found at $mainPyPath" -ForegroundColor Red
}

# Update docker-compose.yml
Write-Host "Updating Docker Compose configuration..." -ForegroundColor Yellow

$dockerComposePath = "docker-compose.yml"
if (Test-Path $dockerComposePath) {
    $dockerContent = Get-Content $dockerComposePath
    
    # Update environment variables
    $dockerContent = $dockerContent -replace "REACT_APP_BACKEND_URL=.*", "REACT_APP_BACKEND_URL=http://${selectedIP}:8000"
    $dockerContent = $dockerContent -replace "REACT_APP_ORTHANC_URL=.*", "REACT_APP_ORTHANC_URL=http://${selectedIP}:8042"
    $dockerContent = $dockerContent -replace "FRONTEND_URL=.*", "FRONTEND_URL=http://${selectedIP}:3000"
    $dockerContent = $dockerContent -replace "BACKEND_URL=.*", "BACKEND_URL=http://${selectedIP}:8000"
    
    Set-Content -Path $dockerComposePath -Value $dockerContent
    Write-Host "✓ Updated $dockerComposePath" -ForegroundColor Green
} else {
    Write-Host "✗ Docker Compose file not found at $dockerComposePath" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Configuration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Your Kiro-mini application is now configured to use IP: $selectedIP" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://${selectedIP}:3000" -ForegroundColor White
Write-Host "  Backend:   http://${selectedIP}:8000" -ForegroundColor White
Write-Host "  Orthanc:   http://${selectedIP}:8042" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart the Docker containers: docker-compose down && docker-compose up -d" -ForegroundColor White
Write-Host "  2. Access the application from any device on your network using the URLs above" -ForegroundColor White
Write-Host ""
Write-Host "Note: Make sure your firewall allows connections on ports 3000, 8000, and 8042" -ForegroundColor Cyan