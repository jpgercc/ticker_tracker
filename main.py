import asciichartpy
import yfinance as yf
import requests
import sys
import time
from datetime import datetime, timedelta

# Configuração dos ativos do usuário
USER_ASSETS = {
    "stocks": [
        {"ticker": "PETR4.SA", "display_name": "Petrobras", "purchase_date": "2023-01-15", "quantity": 100, "purchase_price": 25.00},
        {"ticker": "ITSA4.SA", "display_name": "Itausa", "purchase_date": "2024-03-01", "quantity": 200, "purchase_price": 9.50},
    ],
    "cryptos": [
        {"id": "bitcoin", "display_name": "Bitcoin", "symbol": "BTC", "purchase_date": "2022-06-20", "quantity": 0.05, "purchase_price": 20000.00},
        {"id": "ethereum", "display_name": "Ethereum", "symbol": "ETH", "purchase_date": "2023-11-10", "quantity": 0.5, "purchase_price": 2000.00},
    ]
}

tempo_grafico = 30  # Dias para o histórico # suporta até 170 dias (varia de acordo com o tamanho do terminal e tela)

class AssetTracker:
    def __init__(self, api_choice, identifier, display_symbol, purchase_date=None, quantity=None, purchase_price=None):
        self.api_choice = api_choice
        self.display_symbol = display_symbol
        self.purchase_date = purchase_date
        self.quantity = quantity
        self.purchase_price = purchase_price
        
        self._setup_encoding()
        self._setup_api_config(identifier)

    def _setup_encoding(self):
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
        except (AttributeError, Exception):
            pass

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
            print(f"Erro ao obter preço de {self.display_symbol}: {e}")
            return None

    def _get_stock_price(self):
        try:
            ticker = yf.Ticker(self.stock_ticker)
            price = ticker.fast_info.last_price
            return float(price) if price else None
        except Exception as e:
            print(f"Erro ao obter preço de {self.stock_ticker}: {e}")
            return None

    def get_historical_data(self, days=tempo_grafico):
        """Obtém dados históricos do ativo."""
        if self.api_choice == "coingecko":
            return self._get_crypto_history(days)
        return self._get_stock_history(days)

    def _get_crypto_history(self, days):
        url = f"{self.base_url}/coins/{self.crypto_id}/market_chart"
        params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [price[1] for price in data.get('prices', [])]
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Erro ao obter histórico de {self.display_symbol}: {e}")
            return []

    def _get_stock_history(self, days):
        try:
            ticker = yf.Ticker(self.stock_ticker)
            hist = ticker.history(period=f"{days}d", interval="1d")
            return hist['Close'].tolist() if not hist.empty else []
        except Exception as e:
            print(f"Erro ao obter histórico de {self.stock_ticker}: {e}")
            return []

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

    def display_price_info(self, current_price):
        """Exibe informações de preço e portfolio."""
        print("\n" * 18)
        
        # Cabeçalho
        if self.purchase_date and self.purchase_price:
            print(f"{self.display_symbol} em {self.purchase_date}: {self.format_price(self.purchase_price)} USD (data de compra)\n")
        else:
            print(f"{self.display_symbol}\n")
            
        if current_price is None:
            print(f"Não foi possível obter o preço atual do {self.display_symbol}.")
            return
            
        print(f"Preço atual do {self.display_symbol}: {self.format_price(current_price)} USD")
        
        # Métricas do portfolio
        metrics = self._calculate_portfolio_metrics(current_price)
        if metrics:
            print(f"  Comprado em {self.purchase_date} por {self.format_price(self.purchase_price)} USD. Quantidade: {self.quantity:.2f}")
            print(f"  Variação desde a compra: {metrics['status']} {metrics['variation']:+.2f}%")
            print(f"  Valor atual total: {self.format_price(metrics['current_value'])} USD (Custo: {self.format_price(metrics['purchase_total'])} USD)")
        else:
            print("  Dados de compra não fornecidos para cálculo de variação.")

    def display_chart(self, historical_data):
        """Exibe gráfico ASCII e link para gráfico completo."""
        if not historical_data:
            print("Não foi possível gerar o gráfico - dados indisponíveis.")
            return
        
        print(f"\nGráfico do {self.display_symbol} (últimos {len(historical_data)} dias):")
        try:
            chart = asciichartpy.plot(historical_data, {'height': 15})
            print(chart)
        except Exception as e:
            print(f"Erro ao gerar gráfico: {e}")

        # Link para gráfico completo
        chart_link = self._get_chart_link()
        if chart_link:
            print(f"\nConfira o gráfico completo aqui: {chart_link}")

    def _get_chart_link(self):
        """Retorna o link para o gráfico completo."""
        if self.api_choice == "yahoo_stock" and self.stock_ticker:
            return f"https://finance.yahoo.com/quote/{self.stock_ticker}/chart?p={self.stock_ticker}"
        elif self.api_choice == "coingecko" and self.crypto_id:
            return f"https://www.coingecko.com/en/coins/{self.crypto_id}"
        return ""
    
    def run(self):
        """Executa o tracker completo."""
        current_price = self.get_current_price()
        self.display_price_info(current_price)
        
        historical_data = self.get_historical_data(tempo_grafico)
        self.display_chart(historical_data)

def show_menu():
    """Exibe o menu principal."""
    print("\n" * 5)
    print("--- Monitor de Ativos ---")
    print("1. Ver Minhas Ações")
    print("2. Ver Minhas Criptos")
    print("3. Buscar Ativo Específico")
    print("4. Sair")

def show_assets(assets, asset_type):
    """Exibe lista de ativos do usuário."""
    if not assets:
        print(f"Você não tem {asset_type} registradas.")
        time.sleep(2)
        return None
    
    print(f"\n--- Minhas {asset_type.title()} ---")
    for i, asset in enumerate(assets):
        name = asset.get('display_name', asset.get('ticker', asset.get('id')))
        ticker = asset.get('ticker', asset.get('symbol', ''))
        print(f"{i+1}. {name} ({ticker}) - Compra: {asset['purchase_date']} ({asset['quantity']} unid.)")
    
    return assets

def get_user_choice(max_options, back_option='v'):
    """Obtém escolha do usuário com validação."""
    choice = input(f"Escolha o número (1-{max_options}) ou '{back_option}' para voltar: ")
    if choice.lower() == back_option:
        return None
    
    try:
        idx = int(choice) - 1
        return idx if 0 <= idx < max_options else -1
    except ValueError:
        return -1

def handle_asset_selection(assets, api_choice):
    """Gerencia seleção e exibição de ativos."""
    idx = get_user_choice(len(assets))
    if idx is None:
        return
    if idx == -1:
        print("Escolha inválida.")
        time.sleep(1)
        return
    
    try:
        asset = assets[idx]
        identifier = asset.get('ticker') or asset.get('id')
        symbol = asset.get('display_name') or asset.get('symbol')
        
        tracker = AssetTracker(
            api_choice=api_choice,
            identifier=identifier,
            display_symbol=symbol,
            purchase_date=asset['purchase_date'],
            quantity=asset['quantity'],
            purchase_price=asset['purchase_price']
        )
        tracker.run()
        input("\nPressione Enter para voltar ao menu...")
    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(2)

def search_specific_asset():
    """Busca ativo específico."""
    print("\n--- Buscar Ativo Específico ---")
    choice = input("1. Cripto ou 2. Ação? (Digite 1 ou 2): ")
    
    if choice == "1":
        identifier = input("ID da criptomoeda (ex: bitcoin): ").lower()
        symbol = input("Símbolo da criptomoeda (ex: BTC): ").upper()
        api_choice = "coingecko"
    elif choice == "2":
        identifier = input("Ticker da ação (ex: GOOG, PETR4.SA): ").upper()
        symbol = identifier
        api_choice = "yahoo_stock"
    else:
        print("Escolha inválida.")
        time.sleep(1)
        return

    try:
        tracker = AssetTracker(api_choice, identifier, symbol)
        tracker.run()
        input("\nPressione Enter para voltar ao menu...")
    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(2)

def main():
    """Função principal."""
    while True:
        show_menu()
        choice = input("Escolha uma opção: ")

        if choice == "4":
            print("Saindo do programa. Até mais!")
            sys.exit(0)
        elif choice == "1":
            assets = show_assets(USER_ASSETS["stocks"], "ações")
            if assets:
                handle_asset_selection(assets, "yahoo_stock")
        elif choice == "2":
            assets = show_assets(USER_ASSETS["cryptos"], "criptomoedas")
            if assets:
                handle_asset_selection(assets, "coingecko")
        elif choice == "3":
            search_specific_asset()
        else:
            print("Opção inválida. Tente novamente.")
            time.sleep(1)

if __name__ == "__main__":
    main()