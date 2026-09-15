$files = Get-ChildItem -Recurse -Filter *.py
foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $modified = $false

    if ($content -match '\| None = None' -or $content -match '\| None') {
        # We need to replace str | None -> Optional[str]
        $content = $content -replace 'str\s*\|\s*None', 'Optional[str]'
        $content = $content -replace 'int\s*\|\s*None', 'Optional[int]'
        $content = $content -replace 'Type\[BaseModel\]\s*\|\s*None', 'Optional[Type[BaseModel]]'
        
        # Add Optional to typing import if not there
        if ($content -notmatch 'import.*Optional') {
            if ($content -match 'from typing import ([^\r\n]*)') {
                $content = $content -replace 'from typing import ([^\r\n]*)', 'from typing import $1, Optional'
            } else {
                $content = "from typing import Optional`n" + $content
            }
        }
        $modified = $true
    }

    if ($modified) {
        Write-Host "Fixing | None in $($file.FullName)"
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
    }
}
