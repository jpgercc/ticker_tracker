import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yfinance as yf
import requests
import threading
from datetime import datetime, timedelta
import webbrowser
import json
import os

tempo_grafico = 30  # Dias para o histórico

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

def load_user_assets():
    """Carrega ativos do arquivo de configuração."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # Retorna configuração padrão se arquivo não existir
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
        print(f"Erro ao salvar configurações: {e}")
        return False

# Configuração dos ativos do usuário
USER_ASSETS = load_user_assets()

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
        
        # Ajustar parâmetros baseado no período
        if days == "max":
            params = {'vs_currency': 'usd', 'days': 'max', 'interval': 'daily'}
        elif days > 90:
            params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
        else:
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
            if days == "max":
                hist = ticker.history(period="max", interval="1d")
            else:
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
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variáveis de controle
        self.current_tracker = None
        self.chart_link = ""
        self.current_period = "30 dias"
        self.user_assets = USER_ASSETS
        
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
        self.stocks_listbox = self.setup_asset_list(stocks_frame, self.user_assets["stocks"], "yahoo_stock")
        
        # Tab Criptos
        cryptos_frame = ttk.Frame(self.notebook)
        self.notebook.add(cryptos_frame, text="Criptomoedas")
        self.cryptos_listbox = self.setup_asset_list(cryptos_frame, self.user_assets["cryptos"], "coingecko")
        
        # Frame direito - Detalhes do ativo
        right_frame = ttk.LabelFrame(main_frame, text="Detalhes do Ativo", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Área de informações
        info_frame = ttk.Frame(right_frame)
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Controles do gráfico
        controls_frame = ttk.LabelFrame(info_frame, text="Controles", padding="5")
        controls_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(controls_frame, text="Período:").grid(row=0, column=0, padx=(0, 5))
        self.period_var = tk.StringVar(value=self.current_period)
        period_combo = ttk.Combobox(controls_frame, textvariable=self.period_var, 
                                   values=list(CHART_PERIODS.keys()), state="readonly", width=15)
        period_combo.grid(row=0, column=1, padx=(0, 10))
        period_combo.bind('<<ComboboxSelected>>', self.on_period_change)
        
        # Botões de ação
        ttk.Button(controls_frame, text="Adicionar Ativo", command=self.show_add_asset_dialog).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(controls_frame, text="Remover Ativo", command=self.remove_selected_asset).grid(row=0, column=3, padx=(0, 5))
        
        self.info_text = scrolledtext.ScrolledText(right_frame, width=50, height=12, wrap=tk.WORD)
        self.info_text.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame para gráfico
        self.chart_frame = ttk.Frame(right_frame)
        self.chart_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botões
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
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
        right_frame.rowconfigure(1, weight=1)  # Mudança aqui para o info_text
        right_frame.rowconfigure(2, weight=1)  # Mudança aqui para o chart_frame
        
        # Variáveis de controle removidas daqui (já estão no __init__)
        
    def setup_asset_list(self, parent, assets, api_choice):
        """Configura a lista de ativos."""
        # Frame para lista e botões
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        listbox = tk.Listbox(list_frame, height=8)
        listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para a listbox
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Preencher lista
        self.update_listbox(listbox, assets)
        
        # Bind para seleção
        listbox.bind('<<ListboxSelect>>', lambda e: self.on_asset_select(e, assets, api_choice))
        
        # Configurar redimensionamento
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        return listbox
    
    def update_listbox(self, listbox, assets):
        """Atualiza o conteúdo da listbox."""
        listbox.delete(0, tk.END)
        for asset in assets:
            name = asset.get('display_name', asset.get('ticker', asset.get('id')))
            ticker = asset.get('ticker', asset.get('symbol', ''))
            listbox.insert(tk.END, f"{name} ({ticker})")
        
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
            period_days = CHART_PERIODS[self.current_period]
            historical_data = self.current_tracker.get_historical_data(period_days)
            
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
            info += f"📅 Período: {self.current_period}\n"
        
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
    
    def on_period_change(self, event=None):
        """Manipula mudança do período do gráfico."""
        self.current_period = self.period_var.get()
        if self.current_tracker:
            self.update_asset_display()
    
    def show_add_asset_dialog(self):
        """Exibe diálogo para adicionar novo ativo."""
        dialog = AddAssetDialog(self.root, self.add_asset_callback)
    
    def add_asset_callback(self, asset_data):
        """Callback para adicionar novo ativo."""
        asset_type = asset_data['type']
        asset_info = asset_data['data']
        
        # Adicionar ao dicionário de ativos
        if asset_type == 'stock':
            self.user_assets['stocks'].append(asset_info)
            self.update_listbox(self.stocks_listbox, self.user_assets['stocks'])
        else:
            self.user_assets['cryptos'].append(asset_info)
            self.update_listbox(self.cryptos_listbox, self.user_assets['cryptos'])
        
        # Salvar configurações
        save_user_assets(self.user_assets)
        messagebox.showinfo("Sucesso", f"Ativo {asset_info['display_name']} adicionado com sucesso!")
    
    def remove_selected_asset(self):
        """Remove o ativo selecionado."""
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        
        if tab_text == "Ações":
            listbox = self.stocks_listbox
            assets = self.user_assets['stocks']
            asset_type = "ação"
        else:
            listbox = self.cryptos_listbox
            assets = self.user_assets['cryptos']
            asset_type = "criptomoeda"
        
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", f"Selecione uma {asset_type} para remover.")
            return
        
        idx = selection[0]
        asset_name = assets[idx]['display_name']
        
        # Confirmar remoção
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover {asset_name}?"):
            # Remover do dicionário
            assets.pop(idx)
            
            # Atualizar listbox
            self.update_listbox(listbox, assets)
            
            # Salvar configurações
            save_user_assets(self.user_assets)
            
            # Limpar exibição se era o ativo atual
            if self.current_tracker and self.current_tracker.display_symbol == asset_name:
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "Selecione um ativo para visualizar informações.")
                for widget in self.chart_frame.winfo_children():
                    widget.destroy()
                self.current_tracker = None
            
            messagebox.showinfo("Sucesso", f"{asset_name} removido com sucesso!")

class AddAssetDialog:
    def __init__(self, parent, callback):
        self.callback = callback
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Adicionar Novo Ativo")
        self.dialog.geometry("400x500")
        self.dialog.resizable(True, True)
        self.dialog.grab_set()  # Modal
        
        # Centralizar janela
        self.dialog.transient(parent)
        self.center_window()
        
        self.setup_ui()
    
    def center_window(self):
        """Centraliza a janela na tela."""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"400x500+{x}+{y}")
    
    def setup_ui(self):
        """Configura a interface do diálogo."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Adicionar Novo Ativo", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        
        # Tipo de ativo
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="Tipo de Ativo:").pack(anchor=tk.W)
        self.asset_type_var = tk.StringVar(value="stock")
        type_frame_radio = ttk.Frame(type_frame)
        type_frame_radio.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Radiobutton(type_frame_radio, text="Ação", variable=self.asset_type_var, 
                       value="stock", command=self.on_type_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(type_frame_radio, text="Criptomoeda", variable=self.asset_type_var, 
                       value="crypto", command=self.on_type_change).pack(side=tk.LEFT)
        
        # Campo ticker/ID
        ticker_frame = ttk.Frame(main_frame)
        ticker_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ticker_label = ttk.Label(ticker_frame, text="Ticker da Ação:")
        self.ticker_label.pack(anchor=tk.W)
        self.ticker_entry = ttk.Entry(ticker_frame, width=30)
        self.ticker_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Nome de exibição
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Nome de Exibição:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(name_frame, width=30)
        self.name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Símbolo (apenas para criptos)
        self.symbol_frame = ttk.Frame(main_frame)
        self.symbol_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.symbol_label = ttk.Label(self.symbol_frame, text="Símbolo:")
        self.symbol_label.pack(anchor=tk.W)
        self.symbol_entry = ttk.Entry(self.symbol_frame, width=30)
        self.symbol_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Data de compra
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(date_frame, text="Data de Compra (YYYY-MM-DD):").pack(anchor=tk.W)
        self.date_entry = ttk.Entry(date_frame, width=30)
        self.date_entry.pack(fill=tk.X, pady=(5, 0))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Quantidade
        qty_frame = ttk.Frame(main_frame)
        qty_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(qty_frame, text="Quantidade:").pack(anchor=tk.W)
        self.qty_entry = ttk.Entry(qty_frame, width=30)
        self.qty_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Preço de compra
        price_frame = ttk.Frame(main_frame)
        price_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(price_frame, text="Preço de Compra (USD):").pack(anchor=tk.W)
        self.price_entry = ttk.Entry(price_frame, width=30)
        self.price_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Adicionar", command=self.add_asset).pack(side=tk.RIGHT)
        
        # Configuração inicial
        self.on_type_change()
    
    def on_type_change(self):
        """Manipula mudança do tipo de ativo."""
        asset_type = self.asset_type_var.get()
        
        if asset_type == "stock":
            self.ticker_label.config(text="Ticker da Ação:")
            self.symbol_frame.pack_forget()
        else:
            self.ticker_label.config(text="ID da Criptomoeda:")
            self.symbol_frame.pack(fill=tk.X, pady=(0, 10), before=self.date_entry.master)
    
    def add_asset(self):
        """Adiciona o ativo."""
        try:
            # Validar campos obrigatórios
            ticker = self.ticker_entry.get().strip()
            name = self.name_entry.get().strip()
            date = self.date_entry.get().strip()
            quantity = self.qty_entry.get().strip()
            price = self.price_entry.get().strip()
            
            if not all([ticker, name, date, quantity, price]):
                messagebox.showerror("Erro", "Todos os campos são obrigatórios!")
                return
            
            # Validar data
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro", "Data deve estar no formato YYYY-MM-DD!")
                return
            
            # Validar números
            try:
                quantity = float(quantity)
                price = float(price)
                if quantity <= 0 or price <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Erro", "Quantidade e preço devem ser números positivos!")
                return
            
            # Criar dados do ativo
            asset_type = self.asset_type_var.get()
            
            if asset_type == "stock":
                asset_data = {
                    "ticker": ticker.upper(),
                    "display_name": name,
                    "purchase_date": date,
                    "quantity": quantity,
                    "purchase_price": price
                }
            else:
                symbol = self.symbol_entry.get().strip()
                if not symbol:
                    messagebox.showerror("Erro", "Símbolo é obrigatório para criptomoedas!")
                    return
                
                asset_data = {
                    "id": ticker.lower(),
                    "display_name": name,
                    "symbol": symbol.upper(),
                    "purchase_date": date,
                    "quantity": quantity,
                    "purchase_price": price
                }
            
            # Callback para adicionar
            self.callback({
                'type': asset_type,
                'data': asset_data
            })
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar ativo: {str(e)}")

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