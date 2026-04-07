@echo off
chcp 65001 >nul
title STARLAB - Gestion du Laboratoire
cd /d "%~dp0"

echo ===============================================
echo    🔬 STARLAB - Gestion Financière du Laboratoire
echo ===============================================
echo.

echo [1/3] Verification des dependances...
echo.

REM Installation de streamlit
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Installation de streamlit...
    pip install streamlit
) else (
    echo [OK] streamlit est installe
)

REM Installation de pandas
pip show pandas >nul 2>&1
if errorlevel 1 (
    echo Installation de pandas...
    pip install pandas
) else (
    echo [OK] pandas est installe
)

REM Installation de openpyxl
pip show openpyxl >nul 2>&1
if errorlevel 1 (
    echo Installation de openpyxl...
    pip install openpyxl
) else (
    echo [OK] openpyxl est installe
)

REM Installation de python-docx
pip show python-docx >nul 2>&1
if errorlevel 1 (
    echo Installation de python-docx...
    pip install python-docx
) else (
    echo [OK] python-docx est installe
)

REM Installation de pillow
pip show pillow >nul 2>&1
if errorlevel 1 (
    echo Installation de pillow...
    pip install pillow
) else (
    echo [OK] pillow est installe
)

echo.
echo [2/3] Verification des fichiers...
echo.

if not exist "app.py" (
    echo [ERREUR] app.py non trouve
    pause
    exit /b 1
)

if not exist "pages" (
    echo [ERREUR] Dossier 'pages' non trouve
    pause
    exit /b 1
)

if not exist "modules" (
    echo [ERREUR] Dossier 'modules' non trouve
    pause
    exit /b 1
)

echo [OK] Tous les fichiers sont presents

echo.
echo [3/3] Demarrage de l'application...
echo.

echo ===============================================
echo    L'application va s'ouvrir dans votre navigateur
echo    Adresse: http://localhost:8501
echo    Appuyez sur Ctrl+C pour arreter
echo ===============================================
echo.

streamlit run app.py

pause