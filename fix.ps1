$files = @(
    "backend\app\routers\appointments.py",
    "backend\app\routers\customers.py",
    "backend\app\services\payment_service.py",
    "backend\app\services\quotation_service.py",
    "backend\app\services\repair_order_service.py",
    "backend\app\auth.py",
    "backend\app\routers\analytics.py",
    "backend\tests\test_customer_requests_e2e.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        $modified = $false
        
        if ($content -match 'from datetime import datetime(\r?\n)') {
            $content = $content -replace 'from datetime import datetime\r?\n', "from datetime import datetime, timezone`n"
            $modified = $true
        }
        
        if ($content -match 'datetime\.utcnow\(\)') {
            $content = $content -replace 'datetime\.utcnow\(\)', 'datetime.now(timezone.utc)'
            $modified = $true
        }

        # also fix datetime.datetime.utcnow()
        if ($content -match 'datetime\.datetime\.utcnow\(\)') {
            $content = $content -replace 'datetime\.datetime\.utcnow\(\)', 'datetime.now(timezone.utc)'
            $modified = $true
        }

        # also fix Default None type hints
        if ($content -match ':\s*str\s*=\s*None') {
            $content = $content -replace ':\s*str\s*=\s*None', ': str | None = None'
            $modified = $true
        }
        if ($content -match ':\s*int\s*=\s*None') {
            $content = $content -replace ':\s*int\s*=\s*None', ': int | None = None'
            $modified = $true
        }
        
        if ($modified) {
            Write-Host "Updating $file"
            # Use UTF-8 encoding without BOM
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText((Resolve-Path $file).Path, $content, $utf8NoBom)
        }
    }
}
