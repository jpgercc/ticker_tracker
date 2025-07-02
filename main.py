import streamlit as st
import yfinance as yf
import requests
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

# --- Configurações Iniciais ---
# Períodos disponíveis para gráfico
CHART_PERIODS = {
    "30 dias": 30,
    "60 dias": 60,
    "90 dias": 90,
    "6 meses": 180,
    "1 ano": 365,
    "2 anos": 730,
    "3 anos": 1095,
    "5 anos": 1825,
    "Máximo": "max"
}

# Arquivo para salvar configurações
CONFIG_FILE = "assets_config.json"

# --- Funções de Carregamento/Salvamento de Ativos ---
def load_user_assets():
    """Carrega ativos do arquivo de configuração."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # Retorna configuração padrão se arquivo não existir ou houver erro
    return {
        "stocks": [
            {"ticker": "PETR4.SA", "display_name": "Petrobras", "purchase_date": "2023-01-15", "quantity": 100, "purchase_price": 25.00},
            {"ticker": "ITSA4.SA", "display_name": "Itausa", "purchase_date": "2024-03-01", "quantity": 200, "purchase_price": 9.50},
        ],
        "cryptos": [
            {"id": "bitcoin", "display_name": "Bitcoin", "symbol": "BTC", "purchase_date": "2022-06-20", "quantity": 0.05, "purchase_price": 20000.00},
            {"id": "ethereum", "display_name": "Ethereum", "symbol": "ETH", "purchase_date": "2023-11-10", "quantity": 0.5, "purchase_price": 2000.00},
        ]
    }

def save_user_assets(assets):
    """Salva ativos no arquivo de configuração."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")
        return False

# Inicializa USER_ASSETS na sessão do Streamlit
if 'user_assets' not in st.session_state:
    st.session_state.user_assets = load_user_assets()

# --- Classe AssetTracker (adaptada para Streamlit) ---
class AssetTracker:
    def __init__(self, api_choice, identifier, display_symbol, purchase_date=None, quantity=None, purchase_price=None):
        self.api_choice = api_choice
        self.display_symbol = display_symbol
        self.purchase_date = purchase_date
        self.quantity = quantity
        self.purchase_price = purchase_price
        
        self._setup_api_config(identifier)

    def _setup_api_config(self, identifier):
        if self.api_choice == "coingecko":
            self.crypto_id = identifier
            self.base_url = "https://api.coingecko.com/api/v3"
            self.stock_ticker = None
        elif self.api_choice == "yahoo_stock":
            self.stock_ticker = identifier
            self.crypto_id = None
        else:
            raise ValueError("API inválida. Use 'coingecko' ou 'yahoo_stock'.")

    def get_current_price(self):
        """Obtém o preço atual do ativo."""
        if self.api_choice == "coingecko":
            return self._get_crypto_price()
        return self._get_stock_price()

    def _get_crypto_price(self):
        url = f"{self.base_url}/simple/price?ids={self.crypto_id}&vs_currencies=usd"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[self.crypto_id]['usd'])
        except (requests.exceptions.RequestException, KeyError, ValueError) as e:
            st.error(f"Erro ao obter preço de {self.display_symbol}: {e}")
            return None

    def _get_stock_price(self):
        try:
            ticker = yf.Ticker(self.stock_ticker)
            price = ticker.fast_info.last_price
            return float(price) if price else None
        except Exception as e:
            st.error(f"Erro ao obter preço de {self.stock_ticker}: {e}")
            return None

    def get_historical_data(self, days_or_period):
        """Obtém dados históricos do ativo."""
        if self.api_choice == "coingecko":
            return self._get_crypto_history(days_or_period)
        return self._get_stock_history(days_or_period)

    def _get_crypto_history(self, days_or_period):
        url = f"{self.base_url}/coins/{self.crypto_id}/market_chart"
        
        if days_or_period == "max":
            params = {'vs_currency': 'usd', 'days': 'max', 'interval': 'daily'}
        elif days_or_period > 90:
            params = {'vs_currency': 'usd', 'days': days_or_period, 'interval': 'daily'}
        else:
            params = {'vs_currency': 'usd', 'days': days_or_period, 'interval': 'daily'}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Retorna um DataFrame para compatibilidade com Plotly
            df = pd.DataFrame(data.get('prices', []), columns=['timestamp', 'price'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('date')['price']
            return df
        except (requests.exceptions.RequestException, KeyError) as e:
            st.error(f"Erro ao obter histórico de {self.display_symbol}: {e}")
            return pd.Series()

    def _get_stock_history(self, days_or_period):
        try:
            ticker = yf.Ticker(self.stock_ticker)
            if days_or_period == "max":
                hist = ticker.history(period="max", interval="1d")
            else:
                hist = ticker.history(period=f"{days_or_period}d", interval="1d")
            return hist['Close'] if not hist.empty else pd.Series()
        except Exception as e:
            st.error(f"Erro ao obter histórico de {self.stock_ticker}: {e}")
            return pd.Series()

    def format_price(self, price):
        """Formata o preço para exibição."""
        if price is None:
            return "N/A"
        if price < 1:
            return f"${price:.6f}"
        elif price < 100:
            return f"${price:.2f}"
        else:
            return f"${price:,.2f}"

    def _calculate_portfolio_metrics(self, current_price):
        """Calcula métricas do portfólio se houver dados de compra."""
        if not all([self.purchase_date, self.purchase_price, self.quantity]):
            return None
            
        variation = ((current_price - self.purchase_price) / self.purchase_price) * 100
        current_value = current_price * self.quantity
        purchase_total = self.purchase_price * self.quantity
        
        return {
            'variation': variation,
            'current_value': current_value,
            'purchase_total': purchase_total,
            'status': "📈" if variation > 0 else "📉"
        }

    def get_chart_link(self):
        """Retorna o link para o gráfico completo."""
        if self.api_choice == "yahoo_stock" and self.stock_ticker:
            return f"https://finance.yahoo.com/quote/{self.stock_ticker}/chart?p={self.stock_ticker}"
        elif self.api_choice == "coingecko" and self.crypto_id:
            return f"https://www.coingecko.com/en/coins/{self.crypto_id}"
        return ""

# --- Funções para a Interface Streamlit ---
def display_asset_info(current_tracker, current_price, historical_data, current_period):
    """Exibe informações do ativo no Streamlit."""
    if not current_tracker:
        st.info("Selecione um ativo na barra lateral para visualizar informações.")
        return

    st.subheader(current_tracker.display_symbol)
    st.write("---")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**💰 Preço atual:** {current_tracker.format_price(current_price)}")
        if current_tracker.purchase_date and current_tracker.purchase_price:
            st.write(f"**Comprado em:** {current_tracker.purchase_date}")
            st.write(f"**Preço de compra:** {current_tracker.format_price(current_tracker.purchase_price)}")
            st.write(f"**Quantidade:** {current_tracker.quantity}")

    with col2:
        if current_price is None:
            st.error("❌ Não foi possível obter o preço atual.")
        else:
            metrics = current_tracker._calculate_portfolio_metrics(current_price)
            if metrics:
                st.write("### 📊 Análise do Investimento:")
                st.markdown(f"**{metrics['status']} Variação:** `{metrics['variation']:+.2f}%`")
                st.write(f"**💵 Valor atual:** {current_tracker.format_price(metrics['current_value'])}")
                st.write(f"**💸 Investido:** {current_tracker.format_price(metrics['purchase_total'])}")
                
                profit_loss = metrics['current_value'] - metrics['purchase_total']
                profit_emoji = "💚" if profit_loss > 0 else "❤️" if profit_loss < 0 else "💛"
                st.markdown(f"**{profit_emoji} Lucro/Prejuízo:** {current_tracker.format_price(abs(profit_loss))} {'📈' if profit_loss > 0 else '📉' if profit_loss < 0 else '➡️'}")
    
    st.write("---")

    if not historical_data.empty:
        st.write(f"📈 Histórico disponível: {len(historical_data)} dias")
        st.write(f"📅 Período: {current_period}")
        
        # Criar gráfico com Plotly
        fig = px.line(historical_data, x=historical_data.index, y=historical_data.values,
                      title=f'{current_tracker.display_symbol} - Últimos {len(historical_data)} dias',
                      labels={'x': 'Data', 'y': 'Preço (USD)'})
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Dados históricos não disponíveis para o período selecionado.")

    chart_link = current_tracker.get_chart_link()
    if chart_link:
        st.markdown(f"[Ver Gráfico Completo]({chart_link})", unsafe_allow_html=True)

def add_asset_form():
    """Formulário para adicionar novo ativo."""
    with st.expander("Adicionar Novo Ativo"):
        asset_type = st.radio("Tipo de Ativo:", ("stock", "crypto"), key="add_asset_type")

        display_name = st.text_input("Nome de Exibição:", key="add_display_name")
        identifier = st.text_input(f"{'Ticker da Ação' if asset_type == 'stock' else 'ID da Criptomoeda'}:", key="add_identifier")
        
        symbol = None
        if asset_type == "crypto":
            symbol = st.text_input("Símbolo (ex: BTC, ETH):", key="add_symbol")
        
        purchase_date = st.date_input("Data de Compra:", datetime.now(), key="add_purchase_date").strftime("%Y-%m-%d")
        quantity = st.number_input("Quantidade:", min_value=0.0, format="%.6f", key="add_quantity")
        purchase_price = st.number_input("Preço de Compra (USD):", min_value=0.0, format="%.2f", key="add_price")

        if st.button("Adicionar Ativo"):
            if not all([display_name, identifier, purchase_date, quantity, purchase_price]):
                st.error("Por favor, preencha todos os campos obrigatórios.")
                return
            if asset_type == "crypto" and not symbol:
                st.error("O Símbolo é obrigatório para criptomoedas.")
                return

            new_asset = {}
            if asset_type == "stock":
                new_asset = {
                    "ticker": identifier.upper(),
                    "display_name": display_name,
                    "purchase_date": purchase_date,
                    "quantity": quantity,
                    "purchase_price": purchase_price
                }
                st.session_state.user_assets['stocks'].append(new_asset)
            else:
                new_asset = {
                    "id": identifier.lower(),
                    "display_name": display_name,
                    "symbol": symbol.upper(),
                    "purchase_date": purchase_date,
                    "quantity": quantity,
                    "purchase_price": purchase_price
                }
                st.session_state.user_assets['cryptos'].append(new_asset)
            
            if save_user_assets(st.session_state.user_assets):
                st.success(f"Ativo '{display_name}' adicionado com sucesso!")
                st.rerun() # Recarrega a página para atualizar as listas

def remove_asset_form():
    """Formulário para remover ativo."""
    with st.expander("Remover Ativo"):
        asset_type_to_remove = st.radio("Tipo de Ativo a Remover:", ("stock", "crypto"), key="remove_asset_type")
        
        options = []
        if asset_type_to_remove == "stock":
            options = [f"{s['display_name']} ({s['ticker']})" for s in st.session_state.user_assets['stocks']]
        else:
            options = [f"{c['display_name']} ({c['symbol']})" for c in st.session_state.user_assets['cryptos']]
        
        if not options:
            st.info(f"Nenhuma {asset_type_to_remove} para remover.")
            return

        selected_asset_display = st.selectbox(f"Selecione o(a) {asset_type_to_remove} para remover:", options, key="remove_select")

        if st.button("Remover Ativo Selecionado"):
            if selected_asset_display:
                if asset_type_to_remove == "stock":
                    selected_ticker = selected_asset_display.split('(')[1][:-1]
                    st.session_state.user_assets['stocks'] = [s for s in st.session_state.user_assets['stocks'] if s['ticker'] != selected_ticker]
                else:
                    selected_symbol = selected_asset_display.split('(')[1][:-1]
                    st.session_state.user_assets['cryptos'] = [c for c in st.session_state.user_assets['cryptos'] if c['symbol'] != selected_symbol]
                
                if save_user_assets(st.session_state.user_assets):
                    st.success(f"Ativo '{selected_asset_display}' removido com sucesso!")
                    st.rerun() # Recarrega a página para atualizar as listas
            else:
                st.warning("Selecione um ativo para remover.")

# --- Funções para Organização do Portfólio ---
def extract_category_from_display_name(display_name):
    """Extrai a categoria do display_name dos ativos."""
    if ' - ' in display_name:
        category = display_name.split(' - ')[0]
        # Remove texto entre parênteses se houver
        if '(' in category:
            category = category.split('(')[0].strip()
        return category
    return "SEM CATEGORIA"

def organize_assets_by_category(assets):
    """Organiza ativos por categoria."""
    categories = {}
    
    # Organizar ações por categoria
    for stock in assets.get('stocks', []):
        category = extract_category_from_display_name(stock['display_name'])
        if category not in categories:
            categories[category] = {'stocks': [], 'cryptos': []}
        categories[category]['stocks'].append(stock)
    
    # Organizar criptomoedas (categoria CRYPTO)
    if assets.get('cryptos'):
        categories['CRYPTO'] = {'stocks': [], 'cryptos': assets['cryptos']}
    
    return categories

def calculate_category_totals(category_assets):
    """Calcula totais investidos e valores atuais por categoria."""
    total_invested = 0
    total_current = 0
    asset_count = 0
    
    # Calcular para ações
    for stock in category_assets['stocks']:
        total_invested += stock['purchase_price'] * stock['quantity']
        asset_count += 1
        
        # Obter preço atual
        try:
            tracker = AssetTracker("yahoo_stock", stock['ticker'], stock['display_name'])
            current_price = tracker.get_current_price()
            if current_price:
                total_current += current_price * stock['quantity']
        except:
            total_current += stock['purchase_price'] * stock['quantity']  # Fallback
    
    # Calcular para criptomoedas
    for crypto in category_assets['cryptos']:
        total_invested += crypto['purchase_price'] * crypto['quantity']
        asset_count += 1
        
        # Obter preço atual
        try:
            tracker = AssetTracker("coingecko", crypto['id'], crypto['display_name'])
            current_price = tracker.get_current_price()
            if current_price:
                total_current += current_price * crypto['quantity']
        except:
            total_current += crypto['purchase_price'] * crypto['quantity']  # Fallback
    
    return {
        'total_invested': total_invested,
        'total_current': total_current,
        'asset_count': asset_count,
        'profit_loss': total_current - total_invested,
        'profit_loss_pct': ((total_current - total_invested) / total_invested * 100) if total_invested > 0 else 0
    }

def show_portfolio_overview():
    """Mostra visão geral organizada do portfólio."""
    st.title("📊 Visão Geral do Portfólio")
    
    categories = organize_assets_by_category(st.session_state.user_assets)
    
    if not categories:
        st.info("Nenhum ativo encontrado no portfólio.")
        return
    
    # Calcular totais gerais
    total_portfolio_invested = 0
    total_portfolio_current = 0
    total_assets = 0
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    category_data = {}
    for category_name, category_assets in categories.items():
        totals = calculate_category_totals(category_assets)
        category_data[category_name] = totals
        total_portfolio_invested += totals['total_invested']
        total_portfolio_current += totals['total_current']
        total_assets += totals['asset_count']
    
    with col1:
        st.metric("💰 Total Investido", f"${total_portfolio_invested:,.2f}")
    
    with col2:
        st.metric("📈 Valor Atual", f"${total_portfolio_current:,.2f}")
    
    with col3:
        portfolio_pnl = total_portfolio_current - total_portfolio_invested
        portfolio_pnl_pct = (portfolio_pnl / total_portfolio_invested * 100) if total_portfolio_invested > 0 else 0
        st.metric("💵 P&L Total", f"${portfolio_pnl:,.2f}", f"{portfolio_pnl_pct:+.2f}%")
    
    with col4:
        st.metric("🏢 Total de Ativos", total_assets)
    
    st.markdown("---")
    
    # Exibir por categoria
    for category_name, totals in category_data.items():
        with st.expander(f"📂 {category_name} ({totals['asset_count']} ativos)", expanded=True):
            
            # Métricas da categoria
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Investido", f"${totals['total_invested']:,.2f}")
            
            with col2:
                st.metric("Valor Atual", f"${totals['total_current']:,.2f}")
            
            with col3:
                pnl_color = "normal"
                if totals['profit_loss'] > 0:
                    pnl_color = "inverse"
                elif totals['profit_loss'] < 0:
                    pnl_color = "off"
                st.metric("P&L", f"${totals['profit_loss']:,.2f}", 
                         f"{totals['profit_loss_pct']:+.2f}%")
            
            with col4:
                weight = (totals['total_invested'] / total_portfolio_invested * 100) if total_portfolio_invested > 0 else 0
                st.metric("Peso no Portfolio", f"{weight:.1f}%")
            
            # Lista de ativos da categoria
            category_assets = categories[category_name]
            
            if category_assets['stocks']:
                st.write("**📈 Ações:**")
                for stock in category_assets['stocks']:
                    col_name, col_ticker, col_qty, col_price, col_total = st.columns([3, 1, 1, 1, 1])
                    
                    with col_name:
                        clean_name = stock['display_name'].split(' - ')[1] if ' - ' in stock['display_name'] else stock['display_name']
                        st.write(f"• {clean_name}")
                    
                    with col_ticker:
                        st.write(f"`{stock['ticker']}`")
                    
                    with col_qty:
                        st.write(f"{stock['quantity']}")
                    
                    with col_price:
                        st.write(f"${stock['purchase_price']:.2f}")
                    
                    with col_total:
                        total_value = stock['purchase_price'] * stock['quantity']
                        st.write(f"${total_value:,.2f}")
            
            if category_assets['cryptos']:
                st.write("**₿ Criptomoedas:**")
                for crypto in category_assets['cryptos']:
                    col_name, col_symbol, col_qty, col_price, col_total = st.columns([3, 1, 1, 1, 1])
                    
                    with col_name:
                        st.write(f"• {crypto['display_name']}")
                    
                    with col_symbol:
                        st.write(f"`{crypto['symbol']}`")
                    
                    with col_qty:
                        st.write(f"{crypto['quantity']}")
                    
                    with col_price:
                        st.write(f"${crypto['purchase_price']:,.2f}")
                    
                    with col_total:
                        total_value = crypto['purchase_price'] * crypto['quantity']
                        st.write(f"${total_value:,.2f}")
    
    # Gráfico de distribuição do portfólio
    st.markdown("---")
    st.subheader("📊 Distribuição do Portfólio por Categoria")
    
    if category_data:
        # Preparar dados para o gráfico
        chart_data = []
        for category, totals in category_data.items():
            chart_data.append({
                'Categoria': category,
                'Valor Investido': totals['total_invested'],
                'Valor Atual': totals['total_current']
            })
        
        df_chart = pd.DataFrame(chart_data)
        
        # Gráfico de pizza para distribuição
        fig_pie = px.pie(df_chart, values='Valor Investido', names='Categoria',
                        title='Distribuição do Investimento por Categoria')
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Gráfico de barras comparativo
        fig_bar = px.bar(df_chart, x='Categoria', y=['Valor Investido', 'Valor Atual'],
                        title='Comparação: Valor Investido vs Valor Atual por Categoria',
                        barmode='group')
        st.plotly_chart(fig_bar, use_container_width=True)

# --- Layout Principal do Streamlit ---
st.set_page_config(layout="wide", page_title="Monitor de Ativos")

# Navegação de páginas
page = st.sidebar.selectbox("📍 Navegar para:", 
                           ["🏠 Monitor Principal", "📊 Visão Geral do Portfólio"], 
                           key="page_navigation")

if page == "📊 Visão Geral do Portfólio":
    show_portfolio_overview()
else:
    # Página principal (monitor de ativos)
    st.title("Monitor de Ativos")

    # Barra Lateral
    st.sidebar.title("Meus Ativos")

    selected_asset = None
    selected_api_choice = None

    # Abas na barra lateral para Ações e Criptomoedas
    tab_stocks, tab_cryptos = st.sidebar.tabs(["Ações", "Criptomoedas"])

    with tab_stocks:
        if st.session_state.user_assets['stocks']:
            stock_options = [f"{s['display_name']} ({s['ticker']})" for s in st.session_state.user_assets['stocks']]
            selected_stock_display = st.selectbox("Selecione uma ação:", [""] + stock_options, key="select_stock")
            if selected_stock_display:
                ticker_selected = selected_stock_display.split('(')[1][:-1]
                selected_asset = next((s for s in st.session_state.user_assets['stocks'] if s['ticker'] == ticker_selected), None)
                selected_api_choice = "yahoo_stock"
        else:
            st.info("Nenhuma ação cadastrada.")

    with tab_cryptos:
        if st.session_state.user_assets['cryptos']:
            crypto_options = [f"{c['display_name']} ({c['symbol']})" for c in st.session_state.user_assets['cryptos']]
            selected_crypto_display = st.selectbox("Selecione uma criptomoeda:", [""] + crypto_options, key="select_crypto")
            if selected_crypto_display:
                symbol_selected = selected_crypto_display.split('(')[1][:-1]
                selected_asset = next((c for c in st.session_state.user_assets['cryptos'] if c['symbol'] == symbol_selected), None)
                selected_api_choice = "coingecko"
        else:
            st.info("Nenhuma criptomoeda cadastrada.")

    # Controles de período do gráfico na barra lateral
    st.sidebar.markdown("---")
    st.sidebar.subheader("Configurações do Gráfico")
    current_period_key = st.sidebar.selectbox("Período do Gráfico:", list(CHART_PERIODS.keys()), key="chart_period_select")
    selected_period_days = CHART_PERIODS[current_period_key]

    # Se um ativo for selecionado, carrega e exibe os dados
    current_tracker = None
    current_price = None
    historical_data = pd.Series()

    if selected_asset and selected_api_choice:
        identifier = selected_asset.get('ticker') or selected_asset.get('id')
        display_symbol = selected_asset.get('display_name') or selected_asset.get('symbol')
        
        current_tracker = AssetTracker(
            api_choice=selected_api_choice,
            identifier=identifier,
            display_symbol=display_symbol,
            purchase_date=selected_asset.get('purchase_date'),
            quantity=selected_asset.get('quantity'),
            purchase_price=selected_asset.get('purchase_price')
        )
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Atualizar Dados"):
            st.rerun() # Força o recarregamento dos dados

        # Placeholder para a mensagem de carregamento
        loading_message_placeholder = st.empty()
        loading_message_placeholder.info("Carregando dados, por favor aguarde...")
        
        current_price = current_tracker.get_current_price()
        historical_data = current_tracker.get_historical_data(selected_period_days)
        
        loading_message_placeholder.empty() # Limpa a mensagem de "carregando"
        
        display_asset_info(current_tracker, current_price, historical_data, current_period_key)

    else:
        st.info("Selecione um ativo na barra lateral para visualizar informações.")

    # Seção de Busca de Ativos
    st.markdown("---")
    st.header("Buscar Ativo Personalizado")

    col_search1, col_search2, col_search3 = st.columns([0.2, 0.4, 0.2])

    # Adiciona um placeholder para os resultados da busca
    search_results_placeholder = st.empty()

    with col_search1:
        search_asset_type = st.radio("Tipo:", ("crypto", "stock"), key="search_asset_type")

    with col_search2:
        search_term = st.text_input(f"{'ID da Criptomoeda' if search_asset_type == 'crypto' else 'Ticker da Ação'}:", key="search_term_input")

    with col_search3:
        st.write("") # Espaço para alinhar o botão
        st.write("") # Espaço para alinhar o botão
        if st.button("Buscar Ativo"):
            search_results_placeholder.empty() # Limpa resultados anteriores ao iniciar nova busca
            with search_results_placeholder.container(): # Usa o container para exibir os novos resultados
                if search_term:
                    api_choice_search = "coingecko" if search_asset_type == "crypto" else "yahoo_stock"
                    identifier_search = search_term.lower() if search_asset_type == "crypto" else search_term.upper()
                    display_name_search = search_term.upper() # Usar o próprio termo de busca como display name
                    
                    # Criar um AssetTracker temporário para a busca
                    searched_tracker = AssetTracker(
                        api_choice=api_choice_search,
                        identifier=identifier_search,
                        display_symbol=display_name_search
                    )
                    
                    search_loading_placeholder = st.empty()
                    search_loading_placeholder.info(f"Buscando informações para {display_name_search}...")
                    
                    searched_price = searched_tracker.get_current_price()
                    searched_historical_data = searched_tracker.get_historical_data(CHART_PERIODS[current_period_key])

                    search_loading_placeholder.empty() # Limpa a mensagem de "buscando"

                    if searched_price is not None or not searched_historical_data.empty:
                        st.subheader(f"Resultado da Busca: {display_name_search}")
                        st.write(f"**💰 Preço atual:** {searched_tracker.format_price(searched_price)}")
                        
                        if not searched_historical_data.empty:
                            fig_search = px.line(searched_historical_data, x=searched_historical_data.index, y=searched_historical_data.values,
                                                 title=f'{display_name_search} - Histórico',
                                                 labels={'x': 'Data', 'y': 'Preço (USD)'})
                            fig_search.update_layout(hovermode="x unified")
                            st.plotly_chart(fig_search, use_container_width=True)
                        else:
                            st.warning("Não foi possível obter dados históricos para este ativo.")

                        search_chart_link = searched_tracker.get_chart_link()
                        if search_chart_link:
                            st.markdown(f"[Ver Gráfico Completo]({search_chart_link})", unsafe_allow_html=True)

                    else:
                        st.warning(f"Não foi possível encontrar informações para '{search_term}'. Verifique o Ticker/ID.")
                else:
                    st.warning("Por favor, digite um Ticker/ID para buscar.")

    # Formulários de Adicionar/Remover Ativos
    st.sidebar.markdown("---")
    add_asset_form()
    remove_asset_form()

# Exibir visão geral do portfólio
st.sidebar.markdown("---")
if st.sidebar.button("Visão Geral do Portfólio"):
    show_portfolio_overview()