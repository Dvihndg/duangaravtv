$files = Get-ChildItem -Recurse -Filter *.py
foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match 'timezone\.utc' -and $content -notmatch 'import .*timezone') {
        Write-Host "Fixing missing timezone in $($file.FullName)"
        # Try to find 'from datetime import datetime...' and append ', timezone'
        if ($content -match 'from datetime import ([^\r\n]*)') {
            # Only replace if it doesn't already have timezone
            if ($content -notmatch 'from datetime import .*timezone') {
                $content = $content -replace 'from datetime import ([^\r\n]*)', 'from datetime import $1, timezone'
            }
        } else {
            # Add to the top
            $content = "from datetime import timezone`n" + $content
        }
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
    }
}
