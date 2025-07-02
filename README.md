# Monitor de Ativos

Um aplicativo web desenvolvido em Streamlit para monitoramento de ações e criptomoedas em tempo real.

![Image](https://github.com/user-attachments/assets/0aea8633-fb1b-464e-845c-574ef21a8e7a)
![Image](https://github.com/user-attachments/assets/4346652e-d89d-4d1a-9ff9-b68fee2fd468)

## O que o app faz

- **Monitora preços** de ações brasileiras e criptomoedas em tempo real
- **Calcula lucros/prejuízos** baseado no preço de compra e quantidade investida
- **Exibe gráficos históricos** com diferentes períodos (30 dias a 5 anos)
- **Gerencia portfólio** com funcionalidades para adicionar e remover ativos
- **Busca personalizada** para consultar qualquer ativo não cadastrado

## Como rodar

1. **Instale as dependências:**
```bash
pip install streamlit yfinance requests pandas plotly
```

2. **Execute o aplicativo:**
```bash
streamlit run main.py
```
ou
```bash
python -m streamlit run .\main.py
```

3. **Acesse no navegador:**
O app será aberto automaticamente em `http://localhost:8501`

## Como usar

- Use a **barra lateral** para navegar entre suas ações e criptomoedas
- **Adicione novos ativos** através do formulário na barra lateral
- **Consulte ativos** não cadastrados na seção "Buscar Ativo Personalizado"
- Ajuste o **período do gráfico** para diferentes análises temporais

> Os dados são obtidos via Yahoo Finance (ações) e CoinGecko (criptomoedas)
