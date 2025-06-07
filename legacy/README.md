# 📦 Legacy Files - Academic Assistant (Desktop Version)

Esta pasta contém os arquivos do **projeto original desktop** Academic Assistant, que foi refatorado para a versão SaaS.

## 🗂️ Conteúdo

### **Arquivos Principais:**

- `main.py` - Aplicação desktop original
- `config.py` - Configurações do projeto desktop
- `requirements.txt` - Dependências Python originais
- `install.py` - Script de instalação desktop
- `env.example` - Template de environment original

### **Scripts:**

- `start_assistant.bat` - Script de inicialização Windows
- `manage_logs.py` - Gerenciamento de logs

### **Diretórios:**

- `config/` - Configurações específicas
- `utils/` - Utilitários do projeto desktop
- `ui/` - Interface desktop
- `data/` - Dados locais
- `temp/` - Arquivos temporários
- `logs/` - Logs históricos

## 🔄 Migração para SaaS

O projeto evoluiu de:

```
Desktop App (Legacy) → SaaS Multi-tenant (Atual)
```

### **Principais Mudanças:**

- ✅ **Desktop** → **Web + Desktop + Mobile**
- ✅ **Local Storage** → **Cloud Database (Supabase)**
- ✅ **Single User** → **Multi-tenant SaaS**
- ✅ **Local Processing** → **Cloud API**
- ✅ **Manual Setup** → **Zero-config Deploy**

## 🎯 Arquivos Úteis

### **Para Referência:**

- `main.py` - Lógica de negócio reutilizada
- `config.py` - Configurações migradas
- `utils/` - Funções utilitárias adaptadas

### **Para Backup:**

- `data/` - Dados de usuários (se houver)
- `logs/` - Histórico de uso

## ⚠️ Importante

**Esta pasta é mantida apenas para:**

1. **Referência histórica**
2. **Backup de dados importantes**
3. **Reutilização de código específico**

**Não execute estes arquivos no ambiente SaaS!**

---

*Projeto migrado para SaaS em Dezembro 2024*  
*Versão legacy preservada para referência*
