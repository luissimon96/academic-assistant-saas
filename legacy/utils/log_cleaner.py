#!/usr/bin/env python3
"""
Sistema de limpeza e backup de logs para execuções isoladas
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import config

def clean_logs_for_new_execution():
    """
    Limpa logs para nova execução, fazendo backup dos logs anteriores
    """
    logs_dir = Path(config.LOGS_DIR)
    backup_dir = logs_dir / "backups"
    
    # Cria diretórios se não existem
    logs_dir.mkdir(exist_ok=True)
    backup_dir.mkdir(exist_ok=True)
    
    # Timestamp para o backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup_dir = backup_dir / f"execution_{timestamp}"
    
    # Lista de arquivos de log para processar
    log_files = [
        "academic_assistant.log",
        "errors.log", 
        "threading.log"
    ]
    
    # Verifica se há logs existentes para fazer backup
    has_existing_logs = any((logs_dir / log_file).exists() and (logs_dir / log_file).stat().st_size > 0 
                           for log_file in log_files)
    
    if has_existing_logs:
        print(f"📦 Fazendo backup dos logs anteriores...")
        current_backup_dir.mkdir(exist_ok=True)
        
        # Faz backup de cada log existente
        for log_file in log_files:
            source_path = logs_dir / log_file
            if source_path.exists() and source_path.stat().st_size > 0:
                backup_path = current_backup_dir / log_file
                shutil.copy2(source_path, backup_path)
                print(f"  ✅ {log_file} → backups/execution_{timestamp}/")
        
        # Limpa os logs atuais
        for log_file in log_files:
            log_path = logs_dir / log_file
            if log_path.exists():
                log_path.unlink()
        
        print(f"🧹 Logs limpos para nova execução")
        print(f"📂 Backup salvo em: logs/backups/execution_{timestamp}/")
    else:
        print("🧹 Logs limpos (nenhum log anterior encontrado)")
    
    # Limita número de backups (mantém últimos 10)
    cleanup_old_backups(backup_dir, max_backups=10)
    
    return current_backup_dir if has_existing_logs else None

def cleanup_old_backups(backup_dir: Path, max_backups: int = 10):
    """
    Remove backups antigos, mantendo apenas os mais recentes
    """
    if not backup_dir.exists():
        return
    
    # Lista todas as pastas de backup
    backup_folders = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("execution_")]
    
    # Ordena por data de criação (mais recente primeiro)
    backup_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
    
    # Remove backups antigos se exceder o limite
    if len(backup_folders) > max_backups:
        old_backups = backup_folders[max_backups:]
        for old_backup in old_backups:
            shutil.rmtree(old_backup)
            print(f"🗑️ Backup antigo removido: {old_backup.name}")

def get_backup_info():
    """
    Retorna informações sobre backups disponíveis
    """
    backup_dir = Path(config.LOGS_DIR) / "backups"
    if not backup_dir.exists():
        return []
    
    backups = []
    for backup_folder in backup_dir.iterdir():
        if backup_folder.is_dir() and backup_folder.name.startswith("execution_"):
            # Extrai timestamp do nome da pasta
            timestamp_str = backup_folder.name.replace("execution_", "")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                # Conta arquivos no backup
                log_files = list(backup_folder.glob("*.log"))
                
                backups.append({
                    'folder': backup_folder.name,
                    'timestamp': timestamp,
                    'formatted_time': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    'log_count': len(log_files),
                    'path': str(backup_folder)
                })
            except ValueError:
                continue
    
    # Ordena por timestamp (mais recente primeiro)
    backups.sort(key=lambda x: x['timestamp'], reverse=True)
    return backups

def restore_backup(backup_name: str):
    """
    Restaura um backup específico
    """
    backup_dir = Path(config.LOGS_DIR) / "backups" / backup_name
    logs_dir = Path(config.LOGS_DIR)
    
    if not backup_dir.exists():
        print(f"❌ Backup não encontrado: {backup_name}")
        return False
    
    print(f"🔄 Restaurando backup: {backup_name}")
    
    # Lista arquivos no backup
    log_files = list(backup_dir.glob("*.log"))
    
    for log_file in log_files:
        target_path = logs_dir / log_file.name
        shutil.copy2(log_file, target_path)
        print(f"  ✅ Restaurado: {log_file.name}")
    
    print(f"✅ Backup restaurado com sucesso!")
    return True

def list_backups():
    """
    Lista todos os backups disponíveis
    """
    backups = get_backup_info()
    
    if not backups:
        print("📦 Nenhum backup encontrado")
        return
    
    print(f"📦 Backups disponíveis ({len(backups)}):")
    for backup in backups:
        print(f"  📂 {backup['folder']} - {backup['formatted_time']} ({backup['log_count']} logs)")

if __name__ == "__main__":
    # Teste da função
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clean":
            clean_logs_for_new_execution()
        elif command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Uso: python log_cleaner.py [clean|list|restore <backup_name>]")
    else:
        clean_logs_for_new_execution() 