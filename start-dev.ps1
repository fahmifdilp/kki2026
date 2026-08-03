$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.venv')) { python -m venv .venv }
& .\.venv\Scripts\python -m pip install -r backend\requirements.txt
if (-not (Test-Path 'frontend\node_modules')) { Push-Location frontend; npm install; Pop-Location }
$backend = Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','backend.app:app','--reload','--host','0.0.0.0','--port','8000' -PassThru -WindowStyle Hidden
try { Push-Location frontend; npm run dev } finally { Pop-Location; Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue }
