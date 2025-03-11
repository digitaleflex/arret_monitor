import os
import psutil
import winreg
import time

PROTECTION_SCRIPT = "start.py"  # Remplace par le nom du script de protection
LOG_FILE = "shutdown_log.txt"

# 1️⃣ Réactiver les touches Alt+F4 et Ctrl+Alt+Del
def enable_shutdown_keys():
    key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)  # Réactiver le gestionnaire de tâches
            winreg.SetValueEx(regkey, "ShutdownWithoutLogon", 0, winreg.REG_DWORD, 1)  # Réactiver arrêt sans connexion
            print("[INFO] Rétablissement des raccourcis Windows.")
    except Exception as e:
        print(f"[ERREUR] Impossible de modifier le registre : {e}")

# 2️⃣ Trouver et tuer le script Python en cours d'exécution
def stop_protection_script():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] and "python" in proc.info['name'].lower():
            cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
            if PROTECTION_SCRIPT in cmdline:
                print(f"[INFO] Arrêt du script de protection : {proc.info['name']} (PID: {proc.info['pid']})")
                proc.terminate()
                time.sleep(1)
                if proc.is_running():
                    proc.kill()
                print("[SUCCESS] Script de protection stoppé.")

if __name__ == "__main__":
    enable_shutdown_keys()  # Rétablir les fonctions Windows
    stop_protection_script()  # Arrêter le script de protection
    print("[SUCCESS] La protection a été désactivée.")
    input("Appuyez sur Entrée pour quitter...")
