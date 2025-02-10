$exclude = @("venv", "PDFExtract.zip")
$files = Get-ChildItem -Path . -Exclude $exclude
Compress-Archive -Path $files -DestinationPath "PDFExtract.zip" -Force