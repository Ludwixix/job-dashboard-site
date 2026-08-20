$root = 'C:\Users\samlu\.openclaw\workspace'
Get-ChildItem -Path $root -Recurse -Include *.py,*.ps1 -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'build|dashboard|pdf|merge|ingest|pack|nonlinked' } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 60 FullName, Length, LastWriteTime |
  Format-Table -AutoSize | Out-String -Width 320
