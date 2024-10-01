$CurrentDirectory = Get-Location
Get-ChildItem -Recurse -Path "$CurrentDirectory\*\migrations\*.py" | ForEach-Object {
    if ($_.Name -ne "__init__.py" -and $_.Directory.FullName -notlike "*\.venv\") {
        Remove-Item $_.FullName -Force
    }
}
