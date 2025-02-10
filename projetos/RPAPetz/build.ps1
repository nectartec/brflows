$exclude = @("venv", "RPAPetz.zip")
$files = Get-ChildItem -Path . -Exclude $exclude
Compress-Archive -Path $files -DestinationPath "RPAPetz.zip" -Force