# Windows shell test matrix

Primary machine:
- Windows 11 Home 25H2
- x64
- build 26200.9457

## Functional
- JPG
- JPEG
- PNG
- unsupported TXT/EXE hidden
- 1 selection
- N selection when feature enabled
- mixed selection
- path with spaces
- accented/Unicode filename
- long path
- OneDrive/local path if applicable later
- file deleted between GetState and Invoke
- app closed
- app already running

## Lifecycle
- clean install
- first registration
- app update
- package update
- reinstall
- uninstall
- verify sparse package removed
- verify classic registry removed
- verify CLSID/handler no longer visible

## Performance
- context menu open latency
- GetState bounded
- no network
- no image decode
- no Python startup until Invoke
- Explorer remains responsive

## Signing
- dev trusted self-signed path
- release signing path
- unsigned CI explicitly does not claim modern-menu coverage
