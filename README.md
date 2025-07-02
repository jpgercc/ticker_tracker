# Monitor de Ativos 📈

Um aplicativo desktop moderno e intuitivo para monitoramento de ações e criptomoedas em tempo real, desenvolvido em Python com interface gráfica Tkinter.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## 🚀 Características

### 📊 Monitoramento de Ativos
- **Ações**: Integração com Yahoo Finance para dados de ações brasileiras e internacionais
- **Criptomoedas**: Integração com CoinGecko API para mais de 10.000 criptomoedas
- **Tempo Real**: Preços atualizados em tempo real
- **Histórico**: Gráficos históricos com múltiplos períodos (30 dias a máximo disponível)

### 💰 Análise de Portfolio
- **Controle de Investimentos**: Registre data de compra, quantidade e preço pago
- **Cálculo de Lucro/Prejuízo**: Análise automática de performance dos investimentos
- **Variação Percentual**: Acompanhe ganhos e perdas em tempo real
- **Valor Total**: Visualize o valor atual vs valor investido

### 🎯 Interface Amigável
- **Design Moderno**: Interface limpa e profissional
- **Organização por Abas**: Separação entre ações e criptomoedas
- **Gráficos Integrados**: Visualização matplotlib incorporada
- **Busca Personalizada**: Pesquise qualquer ativo não cadastrado

### 💾 Persistência de Dados
- **Configuração Automática**: Seus ativos são salvos automaticamente
- **Backup JSON**: Dados armazenados em formato legível
- **Restauração**: Configurações restauradas automaticamente na inicialização

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Conexão com internet (para APIs de preços)

## ⚡ Instalação Rápida

### 1. Clone ou baixe o projeto
```bash
git clone https://github.com/seu-usuario/monitor-ativos.git
cd monitor-ativos
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute o aplicativo
```bash
python main.py
```

## 📦 Dependências

```txt
tkinter (incluído no Python)
matplotlib>=3.5.0
yfinance>=0.2.0
requests>=2.28.0
```

Para instalar todas as dependências:
```bash
pip install matplotlib yfinance requests
```

## 🔧 Como Usar

### Primeira Execução
1. **Execute o aplicativo**: `python main.py`
2. **Ativos Pré-configurados**: O app vem com exemplos de PETR4, ITSA4, Bitcoin e Ethereum
3. **Explore a Interface**: Clique nos ativos para ver detalhes e gráficos

### Adicionando Novos Ativos

#### Para Ações:
1. Clique em **"Adicionar Ativo"**
2. Selecione **"Ação"**
3. Digite o ticker (ex: `PETR4.SA`, `AAPL`, `TSLA`)
4. Preencha os dados de compra (opcional)
5. Clique em **"Adicionar"**

#### Para Criptomoedas:
1. Clique em **"Adicionar Ativo"**
2. Selecione **"Criptomoeda"**
3. Digite o ID do CoinGecko (ex: `bitcoin`, `ethereum`, `cardano`)
4. Preencha símbolo e dados de compra
5. Clique em **"Adicionar"**

### Funcionalidades Principais

#### 🔍 Busca Rápida
- Use a barra de busca inferior para pesquisar ativos não cadastrados
- Selecione o tipo (crypto/stock) e digite o identificador
- Pressione Enter ou clique em "Buscar"

#### 📈 Visualização de Gráficos
- **Períodos Disponíveis**: 30 dias, 60 dias, 90 dias, 6 meses, 1 ano, 2 anos, 3 anos, 5 anos, Máximo
- **Gráfico Integrado**: Visualização direta no aplicativo
- **Gráfico Completo**: Link para gráfico detalhado no navegador

#### 💹 Análise de Performance
Quando você adiciona dados de compra, o app calcula automaticamente:
- **Variação %**: Ganho ou perda percentual
- **Valor Atual**: Valor total do investimento hoje
- **Lucro/Prejuízo**: Diferença em valores absolutos
- **Status Visual**: Emojis indicativos (📈📉)

## 📁 Estrutura de Arquivos

```
monitor-ativos/
│
├── main.py                 # Aplicativo principal
├── assets_config.json      # Configurações dos ativos (criado automaticamente)
├── README.md              # Este arquivo
└── requirements.txt       # Dependências (opcional)
```

## 🛠️ Configuração Avançada

### Arquivo de Configuração (assets_config.json)
O aplicativo cria automaticamente um arquivo JSON com suas configurações:

```json
{
  "stocks": [
    {
      "ticker": "PETR4.SA",
      "display_name": "Petrobras",
      "purchase_date": "2023-01-15",
      "quantity": 100,
      "purchase_price": 25.00
    }
  ],
  "cryptos": [
    {
      "id": "bitcoin",
      "display_name": "Bitcoin",
      "symbol": "BTC",
      "purchase_date": "2022-06-20",
      "quantity": 0.05,
      "purchase_price": 20000.00
    }
  ]
}
```

### Exemplos de Tickers Válidos

#### Ações Brasileiras:
- `PETR4.SA` (Petrobras)
- `VALE3.SA` (Vale)
- `ITSA4.SA` (Itausa)
- `BBDC4.SA` (Bradesco)

#### Ações Internacionais:
- `AAPL` (Apple)
- `TSLA` (Tesla)
- `GOOGL` (Google)
- `MSFT` (Microsoft)

#### Criptomoedas (IDs do CoinGecko):
- `bitcoin`
- `ethereum`
- `cardano`
- `polkadot`
- `chainlink`

## 🔌 APIs Utilizadas

### Yahoo Finance (yfinance)
- **Ações**: Dados de ações globais
- **Gratuita**: Sem necessidade de API key
- **Tempo Real**: Preços atualizados

### CoinGecko API
- **Criptomoedas**: Mais de 10.000 moedas disponíveis
- **Gratuita**: Limite de 100 requests/minuto
- **Histórico**: Dados históricos completos

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Roadmap

### Próximas Funcionalidades
- [ ] **Alertas de Preço**: Notificações quando ativo atingir valor
- [ ] **Exportação de Dados**: Export para Excel/CSV
- [ ] **Múltiplos Portfolios**: Criar e gerenciar vários portfolios
- [ ] **Indicadores Técnicos**: RSI, MACD, Médias móveis
- [ ] **Modo Escuro**: Tema escuro para a interface
- [ ] **Sincronização**: Backup na nuvem
- [ ] **Relatórios**: Relatórios detalhados de performance

### Melhorias Técnicas
- [ ] **Cache de Dados**: Cache local para melhor performance
- [ ] **Testes Unitários**: Cobertura de testes
- [ ] **Logs**: Sistema de logging
- [ ] **Configurações**: Painel de configurações avançadas

## 📊 Screenshots

### Tela Principal
*Interface principal com lista de ativos e gráfico*

### Adicionar Ativo
*Diálogo para adicionar novos ativos*

### Análise de Portfolio
*Visualização de lucros e perdas*
