# SMART ECO BIN — Verification Notes

Run tests with a temporary ledger so test fixtures cannot clear or overwrite
`backend/data/classification_records.json`.

## Backend tests

From the repository root in PowerShell:

For the complete suite, point `MODEL_PATH` at a temporary copy of the validated
checkpoint from Git and point storage at a new temporary ledger. This isolates
test runs from the active model and does not touch the project's history:

```powershell
$checkpoint = Join-Path $env:TEMP ("smart-eco-bin-checkpoint-" + [guid]::NewGuid().ToString() + ".pth")
$ledger = Join-Path $env:TEMP ("smart-eco-bin-tests-" + [guid]::NewGuid().ToString() + "-classification_records.json")
$testLog = Join-Path $env:TEMP ("smart-eco-bin-tests-" + [guid]::NewGuid().ToString() + ".log")
python -c "import subprocess,sys; open(sys.argv[1],'wb').write(subprocess.check_output(['git','show','HEAD:ml/model/waste_model.pth']))" $checkpoint
if ($LASTEXITCODE -ne 0) { throw "Could not copy the committed test checkpoint." }
$env:MODEL_PATH = $checkpoint
$env:LOCAL_STORAGE_FILE = $ledger
$env:ENVIRONMENT = "development"
$env:ALLOW_DEV_AUTH = "true"
$env:AUTH_PROVIDER = "auto"
$pythonPath = (Resolve-Path .\backend\.venv\Scripts\python.exe).Path
$testCommand = '"' + $pythonPath + '" -m unittest discover -s tests -p test_*.py -q > "' + $testLog + '" 2>&1'
& $env:ComSpec /c $testCommand
$testExit = $LASTEXITCODE
Get-Content -LiteralPath $testLog -Tail 8
Remove-Item Env:MODEL_PATH, Env:LOCAL_STORAGE_FILE, Env:ENVIRONMENT, Env:ALLOW_DEV_AUTH, Env:AUTH_PROVIDER -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $checkpoint, $ledger, $testLog -Force -ErrorAction SilentlyContinue
if ($testExit -ne 0) { throw "The backend test suite failed with exit code $testExit." }
```

For focused tests that do not load a model, run:

```powershell
$env:LOCAL_STORAGE_FILE = Join-Path $env:TEMP ("smart-eco-bin-tests-" + [guid]::NewGuid().ToString() + "-classification_records.json")
$env:ENVIRONMENT = "development"
$env:ALLOW_DEV_AUTH = "true"
$env:AUTH_PROVIDER = "auto"
python -m unittest discover -s tests -p "test_stage*.py" -v
$stageExit = $LASTEXITCODE
python -m unittest tests.test_api tests.test_routing -v
$apiExit = $LASTEXITCODE
Remove-Item Env:LOCAL_STORAGE_FILE, Env:ENVIRONMENT, Env:ALLOW_DEV_AUTH, Env:AUTH_PROVIDER -ErrorAction SilentlyContinue
if ($stageExit -ne 0 -or $apiExit -ne 0) { throw "One or more backend test commands failed." }
```

The temporary checkpoint is for test isolation only; it does not replace the
active model. The checked-in model files should remain unmodified by test runs.

## Frontend build and source checks

```powershell
npm --prefix frontend run build
python -m compileall -q backend tests
```

## Live API checks

With the backend and frontend running, verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-WebRequest http://127.0.0.1:8001/docs
Invoke-WebRequest http://127.0.0.1:5173/
```

The health endpoint's HTTP response indicates API availability, not that every
model is loaded. A valid real-image inference and browser drag-and-drop
interaction require separate testing; neither should be inferred from a
successful build or controlled routing unit tests.

## Current verification record

- `npm --prefix frontend run build`: passed (Vite production build).
- `python -m compileall -q backend tests`: passed.
- `python -m unittest discover -s tests -p "test_*.py" -q`: 152 tests passed,
  1 skipped. Ran against a temporary ledger and a temporary copy of the
  validated committed classifier checkpoint; the working-tree checkpoint was
  not replaced.
- JSON parsing: 9 project JSON files validated.
- Multi-object detector: loaded from `ml/model/waste_detector.pt` after
  correcting relative-path resolution.
- Local model initialization: classifier loaded and detector loaded in the
  existing backend virtual environment during publication preparation.
- Vite startup log: development server reported ready.
- Direct HTTP and browser checks: not verified. Localhost access was denied by
  the environment's network-domain policy.

No real-world detector-accuracy or browser-interaction claim is made.
