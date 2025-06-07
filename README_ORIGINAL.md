# 🎯 Academic Assistant Stealth

Sistema stealth para assistência acadêmica com LLM integrado, projetado para funcionar de forma completamente invisível em gravações de tela e chamadas de vídeo.

## ⚠️ Aviso Legal

**Este software é destinado EXCLUSIVAMENTE para fins educacionais e de aprendizado.**

- Use apenas em ambiente de teste e desenvolvimento
- Respeite os termos de uso das plataformas educacionais
- O uso inadequado é de responsabilidade do usuário
- Não nos responsabilizamos por violações de políticas acadêmicas

## 🚀 Características Principais

### 🔍 Modo Stealth Avançado

- **Invisível em gravações**: Não aparece em screenshots de sistema
- **Sem rastros**: Não fica visível em Alt+Tab ou taskbar
- **Zero detecção**: Funciona silenciosamente em background
- **System tray oculto**: Ícone praticamente invisível

### ⌨️ Controle por Hotkeys

- **CTRL+Y**: Captura tela ativa
- **CTRL+B**: Toggle visibilidade do popup
- **CTRL+Enter**: Processa imagem com LLM

### 🤖 IA Integrada

- **Claude-3.5-Sonnet** via OpenRouter
- **OCR avançado** com Tesseract
- **Reconhecimento de fórmulas** matemáticas
- **Prompts otimizados** para contexto acadêmico

## 📋 Requisitos

### Sistema

- **Windows 10/11** (x64)
- **Python 3.8+**
- **4GB RAM** mínimo
- **Conexão à internet** para API

### Dependências

- PyQt5 5.15+
- OpenCV 4.8+
- Tesseract OCR
- Outras (ver requirements.txt)

## 🛠️ Instalação

### Método Automático (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/academic-assistant-stealth.git
cd academic-assistant-stealth

# 2. Execute o instalador
python install.py
```

### Método Manual

```bash
# 1. Instale Python 3.8+
# 2. Instale dependências
pip install -r requirements.txt

# 3. Baixe e instale Tesseract OCR
# https://github.com/UB-Mannheim/tesseract/wiki

# 4. Configure API key no config.py
# OPENROUTER_API_KEY = "sua-chave-aqui"
```

## ⚙️ Configuração

### 1. API Key

Edite o arquivo `config.py`:

```python
OPENROUTER_API_KEY = "sk-or-v1-sua-chave-aqui"
```

### 2. Hotkeys (Opcional)

```python
HOTKEY_CAPTURE = "ctrl+y"      # Capturar tela
HOTKEY_TOGGLE = "ctrl+b"       # Toggle visibilidade  
HOTKEY_PROCESS = "ctrl+enter"  # Processar
```

### 3. Configurações de Stealth

```python
HIDE_FROM_TASKBAR = True       # Ocultar da taskbar
NO_WINDOW_SHADOW = True        # Sem sombra da janela
POPUP_OPACITY = 0.95           # Transparência
```

## 🎮 Como Usar

### Início Rápido

```bash
# Inicie o sistema
python main.py

# Ou use o script (Windows)
start_assistant.bat
```

### Fluxo de Trabalho

1. **Inicie o sistema** - Execute main.py
2. **Capture a tela** - Pressione `Ctrl+Y`
3. **Processe com IA** - Pressione `Ctrl+Enter`
4. **Veja a resposta** - Popup aparece discretamente
5. **Copie a resposta** - Clique em "Copiar" ou `Ctrl+C`
6. **Oculte o popup** - Pressione `Ctrl+B` ou `ESC`

### Dicas de Uso

- **Posicionamento**: Deixe a questão bem visível na tela
- **Qualidade**: Screenshots nítidas geram melhores resultados
- **Contexto**: Inclua toda a questão na captura
- **Múltipla escolha**: O sistema identifica automaticamente

## 🔧 Estrutura do Projeto

```
academic-assistant-stealth/
├── main.py                 # Aplicação principal
├── config.py              # Configurações centrais
├── requirements.txt       # Dependências Python
├── install.py             # Instalador automático
├── README.md              # Documentação
├── utils/                 # Utilitários
│   ├── screenshot_manager.py  # Captura de tela
│   ├── hotkey_manager.py      # Gerenciador de hotkeys
│   └── api_client.py          # Cliente OpenRouter
├── ui/                    # Interface
│   └── popup_window.py        # Janela popup stealth
├── temp/                  # Arquivos temporários
└── logs/                  # Logs do sistema
```

## 🛡️ Recursos de Segurança

### Stealth Mode

- **Exclusão de captura**: Janelas não aparecem em screenshots
- **Processo oculto**: Não visível em gerenciadores de tarefa básicos
- **Memória limpa**: Auto-limpeza de arquivos temporários
- **Sem logs**: Operação silenciosa opcional

### Privacidade

- **Dados locais**: Screenshots processados localmente
- **API segura**: Comunicação criptografada com OpenRouter
- **Auto-limpeza**: Remoção automática de arquivos temporários
- **Sem armazenamento**: Não salva histórico por padrão

## 🔍 Solução de Problemas

### Problemas Comuns

**Hotkeys não funcionam**

```bash
# Execute como administrador
python main.py
```

**OCR não funciona**

```bash
# Verifique instalação do Tesseract
tesseract --version

# Reinstale se necessário
# https://github.com/UB-Mannheim/tesseract/wiki
```

**API não responde**

```bash
# Verifique conexão
ping openrouter.ai

# Teste a API key
python -c "from utils.api_client import *; client = OpenRouterClient(); print(client.test_connection())"
```

**Popup não aparece**

```bash
# Verifique permissões de janela
# Desative antivírus temporariamente
# Execute como administrador
```

### Logs e Debug

```bash
# Execute com debug
python main.py --debug

# Verifique logs
type logs\debug.log

# Teste componentes individualmente
python -c "from utils.screenshot_manager import *; s = ScreenshotManager(); print(s.capture_screen())"
```

## 🔄 Atualizações

### Sistema de Auto-Atualização

O sistema verifica automaticamente por atualizações:

```python
# Desabilitar auto-update
AUTO_UPDATE_CHECK = False
```

### Atualização Manual

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

## 🤝 Desenvolvimento

### Estrutura de Desenvolvimento

```bash
# Setup ambiente de dev
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Testes

```bash
# Execute testes
python -m pytest tests/

# Teste individual
python test_screenshot.py
```

### Build

```bash
# Gerar executável
python build.py

# Saída em dist/
```

## 📊 Performance

### Benchmarks

- **Captura de tela**: ~50ms
- **OCR processamento**: ~200ms  
- **API response**: ~2-5s
- **Memória utilizada**: ~50MB

### Otimizações

- Cache de respostas frequentes
- Compressão de imagens
- Threading assíncrono
- Limpeza automática de memória

## 🎓 Casos de Uso Acadêmicos

### Disciplinas Suportadas

- ✅ **Matemática**: Cálculo, Álgebra, Estatística
- ✅ **Física**: Mecânica, Eletromagnetismo  
- ✅ **Química**: Orgânica, Inorgânica, Físico-química
- ✅ **Programação**: Python, Java, C++, SQL
- ✅ **Engenharia**: Circuitos, Estruturas
- ✅ **Múltipla Escolha**: Todas as áreas

### Tipos de Questões

- Problemas com cálculos
- Questões teóricas
- Análise de gráficos
- Interpretação de código
- Fórmulas e equações
- Diagramas e esquemas

## 📝 Changelog

### v1.0.0 (Atual)

- ✅ Sistema stealth completo
- ✅ Integração com Claude-3.5-Sonnet
- ✅ OCR com Tesseract
- ✅ Hotkeys globais
- ✅ Interface popup stealth
- ✅ Auto-instalador

### Roadmap v1.1.0

- 🔄 Cache inteligente de respostas
- 🔄 Suporte a múltiplos monitores
- 🔄 OCR de fórmulas matemáticas avançado
- 🔄 Integração com outros LLMs
- 🔄 Modo batch para múltiplas questões

## 🆘 Suporte

### Canais de Suporte

- **Issues**: GitHub Issues para bugs
- **Discussions**: GitHub Discussions para dúvidas
- **Email**: <suporte@academicassistant.dev> (se disponível)

### FAQ

**Q: É seguro usar em provas online?**
A: O sistema é projetado para ser stealth, mas o uso é por sua conta e risco.

**Q: Funciona em Mac/Linux?**
A: Atualmente apenas Windows. Suporte para outros sistemas em desenvolvimento.

**Q: Quanto custa usar?**
A: O software é gratuito. Custos apenas da API OpenRouter (~$0.01 por questão).

**Q: Precisa de internet?**
A: Sim, para comunicação com a API do LLM.

**Q: Armazena histórico?**
A: Não por padrão. Apenas cache temporário que é limpo automaticamente.

---

## 📄 Licença

Este projeto é distribuído sob licença MIT. Veja `LICENSE` para mais detalhes.

## ⚖️ Disclaimer

**USO POR SUA CONTA E RISCO**

Os desenvolvedores não se responsabilizam por:

- Violações de políticas acadêmicas
- Consequências disciplinares
- Uso inadequado do software
- Problemas técnicos durante uso

**Use com responsabilidade e ética!**

---

*Desenvolvido com ❤️ para a comunidade acadêmica*
