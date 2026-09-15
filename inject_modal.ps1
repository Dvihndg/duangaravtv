$modals = (Get-Content index.html.bak | Select-Object -Skip 514 -First 199) -join "`n"
$newHtml = Get-Content index.html -Raw
$newHtml = $newHtml -replace '</body>', "`n$modals`n  <script src=`"app.js?v=11.0`"></script>`n</body>"
[System.IO.File]::WriteAllText('index.html', $newHtml, [System.Text.Encoding]::UTF8)
