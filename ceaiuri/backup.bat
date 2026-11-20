@echo off
setlocal
if not defined PGHOST set "PGHOST=localhost"
if not defined PGPORT set "PGPORT=5433"
if not defined PGUSER set "PGUSER=frunza_ceai_app"
if not defined PGDATABASE set "PGDATABASE=frunza_ceai"
where pg_dump >nul 2>&1 || set "PATH=%ProgramFiles%\PostgreSQL\18\bin;%PATH%"

set "dest=%~dp0fisier.sql"
if not "%~1"=="" set "dest=%~f1"
set "temp_sql=%dest%.%RANDOM%-%RANDOM%.tmp"
pg_dump --data-only --column-inserts --table="public.ceaiuri_*" --table="public.auth_user" --table="public.auth_user_id_seq" --file="%temp_sql%"
if errorlevel 1 (
    if exist "%temp_sql%" del "%temp_sql%"
    echo Backup esuat. Verifica accesul la PostgreSQL.
    exit /b 1
)
move /y "%temp_sql%" "%dest%" >nul || exit /b 1
echo Backup salvat in "%dest%".
