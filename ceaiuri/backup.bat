@echo off
setlocal DisableDelayedExpansion
if not defined PGHOST set "PGHOST=localhost"
if not defined PGPORT set "PGPORT=5433"
if not defined PGUSER set "PGUSER=frunza_ceai_app"
if not defined PGDATABASE set "PGDATABASE=frunza_ceai"
where pg_dump.exe >nul 2>&1 || set "PATH=%ProgramFiles%\PostgreSQL\18\bin;%PATH%"
rem PGPASSWORD poate fi transmis de Django sau din terminal. Se poate folosi si pgpass.conf.

set "dest=%~dp0fisier.sql"
if not "%~1"=="" set "dest=%~f1"
for %%F in ("%dest%") do set "atribute=%%~aF"
if "%atribute:~0,1%"=="d" (
    echo Alege un fisier SQL ca destinatie. 1>&2
    exit /b 1
)
set "temp_sql=%dest%.%RANDOM%-%RANDOM%.tmp"
set "tabele_existente=%temp_sql%.tabele.tmp"

rem Inainte de migrare pot exista doar tabelele din versiunea anterioara.
psql.exe -X -At -v ON_ERROR_STOP=1 -c "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'" > "%tabele_existente%"
if errorlevel 1 goto :eroare

> "%temp_sql%" echo BEGIN;|| goto :eroare
set "exportat="
for %%T in (
    auth_user
    ceaiuri_categorie ceaiuri_aroma ceaiuri_sediu ceaiuri_raion ceaiuri_ceai
    ceaiuri_ceai_arome ceaiuri_ceai_raioane
    ceaiuri_departament ceaiuri_tipmesaj ceaiuri_tipmesaj_departamente
    ceaiuri_dateutilizator ceaiuri_profil ceaiuri_angajat
    ceaiuri_comanda ceaiuri_liniecomanda ceaiuri_recenzie ceaiuri_intrebare ceaiuri_voucher
) do (
    findstr.exe /L /X /C:"%%T" "%tabele_existente%" >nul
    if errorlevel 2 goto :eroare
    if not errorlevel 1 (
        echo Export tabel: %%T
        pg_dump.exe --column-inserts --data-only --inserts -h "%PGHOST%" -U "%PGUSER%" -p "%PGPORT%" -d "%PGDATABASE%" --schema public -t "public.%%T" >> "%temp_sql%"
        if errorlevel 1 goto :eroare
        set "exportat=1"
    )
)
if not defined exportat (
    echo Baza nu contine niciun tabel din lista de backup. 1>&2
    goto :eroare
)
>> "%temp_sql%" echo COMMIT;|| goto :eroare
move /y "%temp_sql%" "%dest%" >nul || goto :eroare
del /q "%tabele_existente%"
echo Backup salvat in "%dest%".
exit /b 0

:eroare
if exist "%temp_sql%" del /q "%temp_sql%"
if exist "%tabele_existente%" del /q "%tabele_existente%"
echo Backup esuat. Verifica accesul la PostgreSQL si destinatia. 1>&2
exit /b 1
