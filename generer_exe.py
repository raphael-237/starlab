
import os
import subprocess
import sys

def create_exe():
    print("==================================================")
    print("   GÉNÉRATEUR D'EXÉCUTABLE STARLAB")
    print("==================================================")
    
    try:
        import PyInstaller.__main__
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Commande pour générer l'EXE
    # On utilise run_app.py comme point d'entrée
    args = [
        'run_app.py',
        '--onefile',
        '--name=STARLAB',
        '--icon=logo.png',
        '--add-data=app.py;.',
        '--add-data=pages;pages',
        '--add-data=modules;modules',
        '--add-data=data;data',
        '--add-data=logo.png;.',
        '--add-data=BE CORP.png;.',
        '--noconfirm',
        '--clean',
        '--console' # On garde la console pour voir les logs streamlit
    ]
    
    print("\nGénération en cours... Cela peut prendre quelques minutes.")
    PyInstaller.__main__.run(args)
    
    print("\n==================================================")
    print("TERMINÉ ! Votre fichier STARLAB.exe se trouve dans le dossier 'dist'.")
    print("Vous pouvez copier tout le contenu de 'dist' sur un autre PC.")
    print("==================================================")

if __name__ == "__main__":
    create_exe()
