import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yfinance as yf
import requests
import threading
from datetime import datetime, timedelta
import webbrowser

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

tempo_grafico = 30  # Dias para o histórico

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

    def get_chart_link(self):
        """Retorna o link para o gráfico completo."""
        if self.api_choice == "yahoo_stock" and self.stock_ticker:
            return f"https://finance.yahoo.com/quote/{self.stock_ticker}/chart?p={self.stock_ticker}"
        elif self.api_choice == "coingecko" and self.crypto_id:
            return f"https://www.coingecko.com/en/coins/{self.crypto_id}"
        return ""

class AssetTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Ativos")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Configurar estilo
        self.setup_styles()
        
        # Criar interface
        self.setup_ui()
        
    def setup_styles(self):
        """Configura estilos customizados."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar cores
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        style.configure('Info.TLabel', font=('Arial', 10), background='#f0f0f0')
        style.configure('Success.TLabel', font=('Arial', 10), background='#f0f0f0', foreground='green')
        style.configure('Error.TLabel', font=('Arial', 10), background='#f0f0f0', foreground='red')
        
    def setup_ui(self):
        """Configura a interface do usuário."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Monitor de Ativos", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Frame esquerdo - Lista de ativos
        left_frame = ttk.LabelFrame(main_frame, text="Meus Ativos", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Notebook para separar ações e criptos
        self.notebook = ttk.Notebook(left_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab Ações
        stocks_frame = ttk.Frame(self.notebook)
        self.notebook.add(stocks_frame, text="Ações")
        self.setup_asset_list(stocks_frame, USER_ASSETS["stocks"], "yahoo_stock")
        
        # Tab Criptos
        cryptos_frame = ttk.Frame(self.notebook)
        self.notebook.add(cryptos_frame, text="Criptomoedas")
        self.setup_asset_list(cryptos_frame, USER_ASSETS["cryptos"], "coingecko")
        
        # Frame direito - Detalhes do ativo
        right_frame = ttk.LabelFrame(main_frame, text="Detalhes do Ativo", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Área de informações
        self.info_text = scrolledtext.ScrolledText(right_frame, width=50, height=15, wrap=tk.WORD)
        self.info_text.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame para gráfico
        self.chart_frame = ttk.Frame(right_frame)
        self.chart_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botões
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.refresh_btn = ttk.Button(button_frame, text="Atualizar", command=self.refresh_current_asset)
        self.refresh_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.chart_btn = ttk.Button(button_frame, text="Ver Gráfico Completo", command=self.open_full_chart)
        self.chart_btn.grid(row=0, column=1)
        
        # Frame inferior - Busca personalizada
        search_frame = ttk.LabelFrame(main_frame, text="Buscar Ativo", padding="10")
        search_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(search_frame, text="Tipo:").grid(row=0, column=0, padx=(0, 5))
        self.asset_type_var = tk.StringVar(value="crypto")
        type_combo = ttk.Combobox(search_frame, textvariable=self.asset_type_var, 
                                  values=["crypto", "stock"], state="readonly", width=10)
        type_combo.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(search_frame, text="Ticker/ID:").grid(row=0, column=2, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.grid(row=0, column=3, padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self.search_asset())
        
        search_btn = ttk.Button(search_frame, text="Buscar", command=self.search_asset)
        search_btn.grid(row=0, column=4)
        
        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # Variáveis de controle
        self.current_tracker = None
        self.chart_link = ""
        
    def setup_asset_list(self, parent, assets, api_choice):
        """Configura a lista de ativos."""
        listbox = tk.Listbox(parent, height=8)
        listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para a listbox
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Preencher lista
        for asset in assets:
            name = asset.get('display_name', asset.get('ticker', asset.get('id')))
            ticker = asset.get('ticker', asset.get('symbol', ''))
            listbox.insert(tk.END, f"{name} ({ticker})")
        
        # Bind para seleção
        listbox.bind('<<ListboxSelect>>', lambda e: self.on_asset_select(e, assets, api_choice))
        
        # Configurar redimensionamento
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
    def on_asset_select(self, event, assets, api_choice):
        """Manipula a seleção de um ativo."""
        selection = event.widget.curselection()
        if not selection:
            return
            
        idx = selection[0]
        asset = assets[idx]
        
        # Criar tracker em thread separada para não travar a interface
        threading.Thread(target=self.load_asset_data, args=(asset, api_choice), daemon=True).start()
        
    def load_asset_data(self, asset, api_choice):
        """Carrega dados do ativo em thread separada."""
        try:
            identifier = asset.get('ticker') or asset.get('id')
            symbol = asset.get('display_name') or asset.get('symbol')
            
            self.current_tracker = AssetTracker(
                api_choice=api_choice,
                identifier=identifier,
                display_symbol=symbol,
                purchase_date=asset['purchase_date'],
                quantity=asset['quantity'],
                purchase_price=asset['purchase_price']
            )
            
            # Atualizar interface na thread principal
            self.root.after(0, self.update_asset_display)
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Erro ao carregar ativo: {e}"))
    
    def update_asset_display(self):
        """Atualiza a exibição do ativo selecionado."""
        if not self.current_tracker:
            return
            
        # Mostrar loading
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "Carregando dados...")
        
        # Carregar dados em thread separada
        threading.Thread(target=self.fetch_asset_data, daemon=True).start()
    
    def fetch_asset_data(self):
        """Busca dados do ativo."""
        try:
            current_price = self.current_tracker.get_current_price()
            historical_data = self.current_tracker.get_historical_data(tempo_grafico)
            
            # Atualizar na thread principal
            self.root.after(0, lambda: self.display_asset_info(current_price, historical_data))
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Erro ao buscar dados: {e}"))
    
    def display_asset_info(self, current_price, historical_data):
        """Exibe informações do ativo."""
        # Limpar área de informações
        self.info_text.delete(1.0, tk.END)
        
        # Cabeçalho
        info = f"{self.current_tracker.display_symbol}\n"
        info += "=" * 50 + "\n\n"
        
        if self.current_tracker.purchase_date and self.current_tracker.purchase_price:
            info += f"Comprado em: {self.current_tracker.purchase_date}\n"
            info += f"Preço de compra: {self.current_tracker.format_price(self.current_tracker.purchase_price)}\n"
            info += f"Quantidade: {self.current_tracker.quantity}\n\n"
        
        if current_price is None:
            info += "❌ Não foi possível obter o preço atual\n"
        else:
            info += f"💰 Preço atual: {self.current_tracker.format_price(current_price)}\n\n"
            
            # Métricas do portfolio
            metrics = self.current_tracker._calculate_portfolio_metrics(current_price)
            if metrics:
                info += "📊 ANÁLISE DO INVESTIMENTO:\n"
                info += f"  {metrics['status']} Variação: {metrics['variation']:+.2f}%\n"
                info += f"  💵 Valor atual: {self.current_tracker.format_price(metrics['current_value'])}\n"
                info += f"  💸 Investido: {self.current_tracker.format_price(metrics['purchase_total'])}\n"
                
                profit_loss = metrics['current_value'] - metrics['purchase_total']
                profit_emoji = "💚" if profit_loss > 0 else "❤️" if profit_loss < 0 else "💛"
                info += f"  {profit_emoji} Lucro/Prejuízo: {self.current_tracker.format_price(abs(profit_loss))} {'📈' if profit_loss > 0 else '📉' if profit_loss < 0 else '➡️'}\n\n"
        
        if historical_data:
            info += f"📈 Histórico disponível: {len(historical_data)} dias\n"
            info += f"📅 Período: {tempo_grafico} dias\n"
        
        self.info_text.insert(tk.END, info)
        
        # Criar gráfico
        if historical_data:
            self.create_chart(historical_data)
        
        # Salvar link do gráfico
        self.chart_link = self.current_tracker.get_chart_link()
    
    def create_chart(self, data):
        """Cria gráfico matplotlib."""
        # Limpar frame do gráfico
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(data, linewidth=2, color='#1f77b4')
        ax.set_title(f'{self.current_tracker.display_symbol} - Últimos {len(data)} dias')
        ax.set_xlabel('Dias')
        ax.set_ylabel('Preço (USD)')
        ax.grid(True, alpha=0.3)
        
        # Adicionar ao frame
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def refresh_current_asset(self):
        """Atualiza o ativo atual."""
        if self.current_tracker:
            self.update_asset_display()
    
    def open_full_chart(self):
        """Abre gráfico completo no navegador."""
        if self.chart_link:
            webbrowser.open(self.chart_link)
        else:
            messagebox.showwarning("Aviso", "Link do gráfico não disponível.")
    
    def search_asset(self):
        """Busca ativo personalizado."""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Aviso", "Digite um ticker ou ID para buscar.")
            return
        
        asset_type = self.asset_type_var.get()
        
        if asset_type == "crypto":
            api_choice = "coingecko"
            identifier = search_term.lower()
            symbol = search_term.upper()
        else:
            api_choice = "yahoo_stock"
            identifier = search_term.upper()
            symbol = identifier
        
        # Criar asset temporário
        temp_asset = {
            "ticker" if asset_type == "stock" else "id": identifier,
            "display_name": symbol,
            "symbol": symbol,
            "purchase_date": None,
            "quantity": None,
            "purchase_price": None
        }
        
        # Carregar dados
        threading.Thread(target=self.load_asset_data, args=(temp_asset, api_choice), daemon=True).start()
    
    def show_error(self, message):
        """Exibe mensagem de erro."""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, f"❌ ERRO: {message}")

def main():
    """Função principal."""
    root = tk.Tk()
    app = AssetTrackerGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nEncerrando aplicação...")
        root.quit()

if __name__ == "__main__":
    main()