$exclude = @("venv", "hellobot.zip")
$files = Get-ChildItem -Path . -Exclude $exclude
Compress-Archive -Path $files -DestinationPath "hellobot.zip" -Force