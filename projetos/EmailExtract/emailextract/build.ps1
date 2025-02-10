$exclude = @("venv", "emailextract.zip")
$files = Get-ChildItem -Path . -Exclude $exclude
Compress-Archive -Path $files -DestinationPath "emailextract.zip" -Force