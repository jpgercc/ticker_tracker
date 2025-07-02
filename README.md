# 📈 Monitor de Ativos Financeiros

Um aplicativo em Python para monitoramento em tempo real de ações e criptomoedas, com gráficos ASCII e análise de portfólio.

## 🚀 Funcionalidades

- **Monitoramento de Ações**: Acompanhe ações brasileiras e internacionais usando dados do Yahoo Finance
- **Monitoramento de Criptomoedas**: Monitore criptomoedas usando a API do CoinGecko
- **Gráficos ASCII**: Visualize o histórico de preços diretamente no terminal
- **Análise de Portfólio**: Calcule ganhos/perdas baseado na data e preço de compra
- **Interface Interativa**: Menu intuitivo para navegar entre diferentes ativos
- **Busca Personalizada**: Pesquise qualquer ativo não cadastrado no seu portfólio

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Conexão com a internet

## 🔧 Instalação

1. Clone ou baixe o projeto para seu computador

2. Instale as dependências necessárias:
```bash
pip install asciichartpy yfinance requests
```

## ⚙️ Configuração

Antes de usar, configure seus ativos no arquivo `main.py`. Edite a variável `USER_ASSETS`:

```python
USER_ASSETS = {
    "stocks": [
        {
            "ticker": "PETR4.SA", 
            "display_name": "Petrobras", 
            "purchase_date": "2023-01-15", 
            "quantity": 100, 
            "purchase_price": 25.00
        },
        # Adicione mais ações aqui
    ],
    "cryptos": [
        {
            "id": "bitcoin", 
            "display_name": "Bitcoin", 
            "symbol": "BTC", 
            "purchase_date": "2022-06-20", 
            "quantity": 0.05, 
            "purchase_price": 20000.00
        },
        # Adicione mais criptomoedas aqui
    ]
}
```

### Configurando Ações

Para ações, você precisa do **ticker** correto:
- Ações brasileiras: adicione `.SA` (ex: `PETR4.SA`, `VALE3.SA`)
- Ações americanas: use o ticker direto (ex: `AAPL`, `GOOGL`)

### Configurando Criptomoedas

Para criptomoedas, use o **ID** do CoinGecko:
- Bitcoin: `bitcoin`
- Ethereum: `ethereum`
- Para outros, consulte: https://api.coingecko.com/api/v3/coins/list

## 🎮 Como Usar

Execute o programa:
```bash
python main.py
```

### Menu Principal

```
--- Monitor de Ativos ---
1. Ver Minhas Ações
2. Ver Minhas Criptos
3. Buscar Ativo Específico
4. Sair
```

### Funcionalidades do Menu

- **Opção 1**: Exibe suas ações cadastradas e permite selecionar uma para análise detalhada
- **Opção 2**: Exibe suas criptomoedas cadastradas e permite selecionar uma para análise
- **Opção 3**: Busca qualquer ativo (ação ou cripto) não cadastrado no seu portfólio
- **Opção 4**: Sair do programa

## 📊 Informações Exibidas

Para cada ativo, você verá:

- **Preço Atual**: Valor atual em USD
- **Dados de Compra**: Data, preço e quantidade comprada
- **Variação**: Percentual de ganho/perda desde a compra
- **Valor do Portfólio**: Valor atual total vs. custo inicial
- **Gráfico ASCII**: Histórico dos últimos 30 dias
- **Link para Gráfico Completo**: Link direto para o gráfico no Yahoo Finance ou CoinGecko

### Exemplo de Saída

```
Petrobras em 2023-01-15: $25.00 USD (data de compra)

Preço atual do Petrobras: $28.50 USD
  Comprado em 2023-01-15 por $25.00 USD. Quantidade: 100.00
  Variação desde a compra: 📈 +14.00%
  Valor atual total: $2,850.00 USD (Custo: $2,500.00 USD)

Gráfico do Petrobras (últimos 30 dias):
    28.50 ┤ ╭─╮
    27.80 ┤ │ ╰╮
    27.10 ┤╭╯  ╰╮
    26.40 ┤│    ╰─╮
    25.70 ┼╯      ╰╮
    25.00 ┤        ╰───

Confira o gráfico completo aqui: https://finance.yahoo.com/quote/PETR4.SA/chart
```

## 🛠️ Personalização

### Alterar Período do Gráfico

Modifique a variável `tempo_grafico` no início do código:
```python
tempo_grafico = 30  # Dias para o histórico (máximo ~170 dias)
```

### Adicionar Novos Ativos

Adicione novos ativos ao dicionário `USER_ASSETS` seguindo a estrutura existente.

## 🔍 APIs Utilizadas

- **Yahoo Finance** (via yfinance): Para dados de ações
- **CoinGecko API**: Para dados de criptomoedas

## 📝 Estrutura do Código

```
main.py
├── AssetTracker (classe principal)
│   ├── Configuração de APIs
│   ├── Obtenção de preços
│   ├── Dados históricos
│   ├── Cálculos de portfólio
│   └── Exibição de gráficos
├── Funções do menu
├── Gerenciamento de entrada do usuário
└── Loop principal
```

## ⚠️ Limitações

- Requer conexão com internet
- Dados de ações limitados aos mercados suportados pelo Yahoo Finance
- Dados de criptomoedas dependem da disponibilidade da API do CoinGecko
- Gráficos ASCII têm resolução limitada pelo tamanho do terminal

## 🤝 Contribuição

Sinta-se livre para:
- Reportar bugs
- Sugerir melhorias
- Adicionar novas funcionalidades
- Melhorar a documentação

## 📄 Licença

Este projeto é de uso livre para fins pessoais e educacionais.

## 📞 Suporte

Em caso de problemas:
1. Verifique sua conexão com internet
2. Confirme se os tickers/IDs dos ativos estão corretos
3. Verifique se todas as dependências estão instaladas
4. Para ações brasileiras, certifique-se de usar `.SA` no final do ticker

---

**Disclaimer**: Este aplicativo é apenas para fins informativos. Não constitui aconselhamento financeiro.
