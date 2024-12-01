@echo off

rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

<<<<<<< HEAD:apienv/Scripts/activate.bat
set VIRTUAL_ENV=C:\Users\rufin\OneDrive\Desktop\school_monitoring\API\apienv
=======
set VIRTUAL_ENV=C:\Users\Johny\Documents\Projects\FRONT-END\school_management_api\env
>>>>>>> aba9edcf1b812bf10678502e3d2b0b67ef8e026b:env/Scripts/activate.bat

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%

<<<<<<< HEAD:apienv/Scripts/activate.bat
set "_OLD_VIRTUAL_PROMPT=%PROMPT%"
set "PROMPT=(apienv) %PROMPT%"
=======
set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(env) %PROMPT%
>>>>>>> aba9edcf1b812bf10678502e3d2b0b67ef8e026b:env/Scripts/activate.bat

if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%

set PATH=%VIRTUAL_ENV%\Scripts;%PATH%
<<<<<<< HEAD:apienv/Scripts/activate.bat
set VIRTUAL_ENV_PROMPT=apienv
=======
set VIRTUAL_ENV_PROMPT=(env) 
>>>>>>> aba9edcf1b812bf10678502e3d2b0b67ef8e026b:env/Scripts/activate.bat

:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)
