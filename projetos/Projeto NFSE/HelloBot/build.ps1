$exclude = @("venv", "HelloBot.zip")
$files = Get-ChildItem -Path . -Exclude $exclude
Compress-Archive -Path $files -DestinationPath "HelloBot.zip" -Force