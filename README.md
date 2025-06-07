# 🎓 Academic Assistant SaaS

## Visão Geral

Transformação do Academic Assistant desktop em uma plataforma SaaS escalável para estudantes brasileiros.

### 🎯 Objetivos

- **SaaS Multi-usuário**: Suporte a milhares de usuários simultâneos
- **Multi-plataforma**: Web, Desktop (Windows/macOS/Linux), Mobile (PWA)
- **IA Avançada**: OCR + LLM otimizado para educação brasileira
- **Monetização**: 3 tiers (Free, Pro R$ 19.90, Max R$ 29.90)

### 🏗️ Arquitetura

```
📁 academic-assistant-saas/
├── 📁 frontend/          # Next.js 14 + TypeScript
├── 📁 backend/           # FastAPI + Python
├── 📁 desktop/           # Electron app
├── 📁 mobile/            # PWA configuration
├── 📁 shared/            # Tipos compartilhados
├── 📁 docs/              # Documentação
└── 📁 infra/             # Deploy configs
```

### 🛠️ Stack Tecnológico

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn/ui
- **Backend**: FastAPI, Python 3.11, Supabase (PostgreSQL)
- **Desktop**: Electron com shared React components
- **IA**: OpenRouter, Groq (free tier), Claude Haiku/Sonnet
- **OCR**: Tesseract, Google Vision API, Azure OCR
- **Hosting**: Vercel (frontend) + Render (backend) - **GRATUITO**

### 💰 Custo de Infraestrutura

- **Fase Inicial**: R$ 0/mês (100% gratuito)
- **Escala**: R$ 35/mês (para 500+ usuários)
- **vs AWS tradicional**: 97% mais barato

### 🚀 Status de Implementação

- [x] Planejamento estratégico e documentação
- [x] Definição de stack tecnológico econômico
- [x] **CONCLUÍDO**: Setup inicial do projeto
- [x] Backend MVP (FastAPI + estrutura completa)
- [x] Frontend MVP (Next.js + componentes essenciais)
- [x] Sistema de OCR multi-provider
- [x] Interface de upload e processamento
- [ ] **EM PROGRESSO**: Integração Supabase + LLMs
- [ ] Sistema de pagamentos (Stripe/Mercado Pago)
- [ ] Deploy e monitoring

### 📈 Metas 30 Dias

- **10 usuários pagantes**
- **R$ 199 MRR**
- **MVP funcional completo**
- **Custo zero de infraestrutura**

---

Para documentação completa, ver `docs/README.md`
