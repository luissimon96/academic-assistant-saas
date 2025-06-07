# 📋 REGRAS DE NEGÓCIO - ACADEMIC ASSISTANT

## Visão Geral

Este documento define todas as regras de negócio, políticas e lógicas comerciais que governam o funcionamento do Academic Assistant como plataforma SaaS educacional.

---

## 👥 GESTÃO DE USUÁRIOS

### **Cadastro e Registro**

#### **Elegibilidade**

- **Idade mínima**: 16 anos
- **Email**: Obrigatório e único no sistema
- **Verificação**: Email deve ser verificado em 24h
- **Estudante**: Aceita emails .edu com desconto especial

#### **Processo de Cadastro**

1. **Dados obrigatórios**: Nome, email, senha
2. **Dados opcionais**: Universidade, curso, semestre
3. **Verificação email**: Link válido por 24h
4. **Trial automático**: 7 dias free plan
5. **Onboarding**: Tutorial guiado obrigatório

#### **Política de Senhas**

- **Mínimo**: 8 caracteres
- **Obrigatório**: 1 maiúscula, 1 minúscula, 1 número
- **Recomendado**: Símbolos especiais
- **Bloqueios**: Senhas comuns (dictionary attack)

---

## 💰 PLANOS E ASSINATURAS

### **Estrutura de Planos**

#### **🆓 FREE (Trial - 7 dias)**

```yaml
Duração: 7 dias corridos
Consultas: 20 total (não renovável)
Recursos:
  - OCR básico
  - Claude Haiku
  - Suporte por email
  - Sem histórico persistente
  
Regras:
  - Apenas 1 trial por email/CPF
  - Não aceita cartão pré-pago
  - Downgrade automático após expiração
```

#### **💎 PRO (R$ 19,90/mês)**

```yaml
Consultas: 300/mês (reset no dia da renovação)
Recursos:
  - OCR avançado + LaTeX
  - Claude Sonnet
  - Suporte prioritário (12h)
  - Histórico 6 meses
  - Export PDF/DOCX
  - 2 dispositivos simultâneos
  
Preços:
  - Mensal: R$ 19,90
  - Semestral: R$ 149,90 (16% desconto)
  - Anual: R$ 249,90 (30% desconto)
```

#### **🚀 MAX (R$ 29,90/mês)**

```yaml
Consultas: Ilimitadas
Recursos:
  - Multi-LLM (GPT-4, Claude, Gemini)
  - Voting system para qualidade
  - Suporte 24/7 (2h resposta)
  - Histórico ilimitado
  - API access (1000 calls/dia)
  - 5 dispositivos simultâneos
  - Sessions colaborativas
  - Priority processing
  
Preços:
  - Mensal: R$ 59,90
  - Semestral: R$ 299,90 (16% desconto)
  - Anual: R$ 499,90 (30% desconto)
```

### **Regras de Cobrança**

#### **Ciclo de Faturamento**

- **Data base**: Data da primeira assinatura
- **Renovação**: Automática até cancelamento
- **Tentativas**: 3 tentativas em 7 dias
- **Falha pagamento**: Downgrade para FREE

#### **Upgrades e Downgrades**

- **Upgrade**: Imediato com pro-rata
- **Downgrade**: Efetivo no próximo ciclo
- **Cancelamento**: Acesso até fim do período pago

#### **Política de Reembolso**

- **7 dias**: Reembolso total se <5 consultas
- **30 dias**: Reembolso proporcional em casos excepcionais
- **Anual**: Reembolso dos meses não utilizados

---

## 🔢 SISTEMA DE QUOTAS

### **Contagem de Consultas**

#### **O que conta como 1 consulta**

- 1 imagem processada + resposta IA
- Re-processamento da mesma imagem = nova consulta
- Falha de processamento = não conta

#### **Reset de Quotas**

- **FREE**: Sem reset (limite total)
- **PRO**: Reset no dia da renovação mensal
- **MAX**: Sem limites

#### **Compartilhamento de Quotas**

- **Não permitido**: Cada conta é individual
- **Família**: Plano futuro para múltiplos usuários
- **Institucional**: Plano B2B futuro

### **Gestão de Uso**

#### **Alertas de Quota**

```yaml
75% utilizada: Email de aviso
90% utilizada: Notificação no app
95% utilizada: Sugestão de upgrade
100% utilizada: Bloqueio com opção upgrade
```

#### **Overflow Policy**

- **FREE**: Bloqueio absoluto
- **PRO**: Opção de compra de pacotes extras (R$ 9,90 = 50 consultas)
- **MAX**: Sem limites

---

## 🤖 POLÍTICA DE IA

### **Qualidade e Precisão**

#### **SLA por Plano**

```yaml
FREE:
  - Response time: <10s
  - Accuracy: >90%
  - Uptime: >99%
  
PRO:
  - Response time: <5s
  - Accuracy: >95%
  - Uptime: >99.5%
  
MAX:
  - Response time: <3s
  - Accuracy: >98% (multi-model voting)
  - Uptime: >99.9%
```

#### **Limitações de Conteúdo**

- **Não permitido**: Conteúdo adulto, violento, ilegal
- **Limitado**: Trabalhos completos (apenas excerpts)
- **Aceito**: Exercícios, dúvidas específicas, explicações

#### **Política Anti-Fraude**

- **Detecção**: Padrões suspeitos de uso
- **Watermarks**: Respostas marcadas discretamente
- **Educativo**: Foco em explicação, não resposta direta

---

## 🔒 PRIVACIDADE E DADOS

### **Coleta e Uso de Dados**

#### **Dados Coletados**

```yaml
Pessoais:
  - Nome, email, senha (hash)
  - Universidade, curso (opcional)
  - IP, device info (analytics)
  
Uso:
  - Imagens enviadas (temporárias)
  - Consultas e respostas
  - Tempo de uso, frequência
  - Feedback e ratings
```

#### **Retenção de Dados**

```yaml
FREE: 
  - Consultas: 30 dias
  - Conta: Deletada após 90 dias inatividade
  
PRO:
  - Consultas: 6 meses
  - Conta: Mantida enquanto ativa
  
MAX:
  - Consultas: Ilimitado
  - Backup: 7 anos para auditoria
```

#### **Compartilhamento**

- **Nunca compartilhamos**: Dados pessoais ou conteúdo
- **Analytics**: Dados agregados e anonimizados
- **Legal**: Apenas com ordem judicial

### **Direitos dos Usuários (LGPD)**

- **Acesso**: Exportar todos os dados
- **Retificação**: Corrigir dados incorretos
- **Exclusão**: Deletar conta e dados
- **Portabilidade**: Formato JSON estruturado

---

## 🛡️ SEGURANÇA E COMPLIANCE

### **Política de Segurança**

#### **Autenticação**

- **2FA**: Opcional para todos, obrigatório para MAX
- **Login**: Bloqueio após 5 tentativas (15min)
- **Sessão**: Expire automático (24h web, 7d desktop)

#### **Detecção de Fraude**

```yaml
Monitoramento:
  - Múltiplos IPs em pouco tempo
  - Volume anormal de consultas
  - Padrões de bot/automação
  - Cartões de crédito suspeitos
  
Ações:
  - Alerta automático
  - Verificação manual
  - Bloqueio temporário
  - Cancelamento de conta
```

### **Compliance Educacional**

#### **Uso Ético**

- **Transparência**: Usuário sabe que está usando IA
- **Educativo**: Foco em aprendizado, não cola
- **Citação**: Orientação sobre citação de IA

#### **Monitoramento de Abuso**

- **Detecção**: Provas completas, exames cronometrados
- **Prevenção**: Rate limiting durante períodos de prova
- **Cooperação**: Com instituições para compliance

---

## 📞 SUPORTE E ATENDIMENTO

### **Níveis de Suporte**

#### **FREE**

- **Canal**: Email apenas
- **SLA**: 72h resposta
- **Horário**: Comercial (9-18h)
- **Idiomas**: Português

#### **PRO**

- **Canais**: Email, chat, WhatsApp
- **SLA**: 12h resposta
- **Horário**: Estendido (8-22h)
- **Prioridade**: Média

#### **MAX**

- **Canais**: Todos + telefone
- **SLA**: 2h resposta crítica, 6h normal
- **Horário**: 24/7
- **Prioridade**: Alta
- **Dedicated**: Account manager opcional

### **Categorias de Suporte**

```yaml
Técnico:
  - Bugs, erros, performance
  - Configuração, instalação
  - Integração, API
  
Comercial:
  - Billing, pagamentos
  - Planos, upgrades
  - Cancelamentos
  
Produto:
  - Como usar features
  - Sugestões, feedback
  - Training e onboarding
```

---

## 📊 MÉTRICAS E ANALYTICS

### **Tracking de Usuário**

#### **Eventos Monitorados**

```python
# Product Analytics
user_signup, trial_start, first_query
plan_upgrade, plan_downgrade, churn
feature_usage, session_duration
query_success, query_failure, satisfaction

# Business Metrics  
revenue_per_user, customer_lifetime_value
acquisition_cost, conversion_rates
support_tickets, resolution_time
```

#### **Segmentação**

- **Por plano**: FREE, PRO, MAX
- **Por uso**: Power users, casual, at-risk
- **Por perfil**: Graduação, pós, professor
- **Por região**: Estados, universidades

### **Reporting**

- **Executivo**: Dashboard semanal com KPIs
- **Produto**: Métricas de engagement diário
- **Financeiro**: MRR, churn, forecasting
- **Suporte**: Volume, satisfaction, escalation

---

## 🚨 POLÍTICAS DE VIOLAÇÃO

### **Uso Indevido**

#### **Violações Menores**

- Compartilhamento de conta
- Uso comercial em plano pessoal
- Spam ou abuso de suporte

**Ações**: Warning, suspensão temporária

#### **Violações Graves**

- Tentativa de burlar quotas
- Uso para fraude acadêmica sistemática
- Reverse engineering da API

**Ações**: Cancelamento imediato, ban permanente

#### **Violações Críticas**

- Atividade ilegal
- Tentativa de hack/invasão
- Violação de propriedade intelectual

**Ações**: Ban, relatório às autoridades

### **Processo de Revisão**

1. **Detecção**: Automática ou manual
2. **Investigação**: Equipe de compliance (48h)
3. **Decisão**: Graduada conforme severidade
4. **Apelação**: Processo formal (7 dias)
5. **Resolução**: Final em 15 dias

---

## 🔄 ATUALIZAÇÕES E MUDANÇAS

### **Política de Mudanças**

#### **Features e Melhorias**

- **Menores**: Deploy contínuo
- **Maiores**: Comunicação prévia (7 dias)
- **Breaking changes**: 30 dias notice

#### **Preços e Planos**

- **Novos usuários**: Imediato
- **Usuários existentes**: Grandfathering por 6 meses
- **Comunicação**: Email + in-app (30 dias antes)

#### **Termos de Uso**

- **Mudanças**: 30 dias notice obrigatório
- **Aceite**: Implícito por uso continuado
- **Oposição**: Direito de cancelamento sem penalidade

---

## ✅ CHECKLIST DE COMPLIANCE

### **Implementação Obrigatória**

- [ ] Sistema de quotas por plano
- [ ] Rate limiting inteligente
- [ ] Tracking de uso detalhado
- [ ] Billing automatizado
- [ ] Suporte multi-canal
- [ ] Analytics de produto
- [ ] Monitoramento de fraude
- [ ] Política de privacidade
- [ ] Termos de uso claros
- [ ] Processo de cancelamento
- [ ] Sistema de reembolso
- [ ] Compliance LGPD

### **Métricas de Sucesso**

```yaml
Negócio:
  - Conversão FREE→PRO: >15%
  - Churn mensal: <5%
  - NPS: >50
  
Produto:
  - Accuracy IA: >95%
  - Response time: <5s
  - Uptime: >99.5%
  
Suporte:
  - CSAT: >4.5/5
  - Resolution time: <24h
  - First contact resolution: >80%
```

---

*Documento vivo - Atualizado em: Dezembro 2024*
*Próxima revisão: Mensal ou em mudanças regulatórias*
