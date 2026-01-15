from typing import List
from transaction import Transaction
from parsers import IDataParser
from strategies import PerformanceStrategy

class Portfolio:
    def __init__(self, strategy: PerformanceStrategy):
        self._transactions: List[Transaction] = []
        self._strategy = strategy

    def load_data(self, parser: IDataParser, file_path: str):
        # Llenamos la lista usando el parser
        self._transactions = parser.parse(file_path)

    def analyze(self):
        # 1. Cabecera nueva: Mostramos Inversión, Ganancia y ROI
        print(f"\n{'FECHA':<12} | {'ACTIVO':<18} | {'INVERTIDO ($)':<14} | {'GANANCIA ($)':<14} | {'ROI (%)':<10}")
        print("-" * 75)
        
        for t in self._transactions:
            # 2. CÁLCULO REAL
            # Le pasamos a la estrategia lo que te costó (invested) y lo que ganaste (profit_amount)
            # Esto guardará el porcentaje resultante en 'roi_percentage'
            t.roi_percentage = self._strategy.calculate(t.invested, t.profit_amount)
            
            # 3. Formateo visual
            date_str = t.date.strftime("%Y-%m-%d")
            # Cortamos el nombre si es muy largo
            name = (t.description[:15] + '..') if len(t.description) > 15 else t.description
            
            # 4. Imprimir fila con datos financieros
            # :.2f significa "muéstrame solo 2 decimales"
            print(f"{date_str:<12} | {name:<18} | {t.invested:<14.2f} | {t.profit_amount:<14.2f} | {t.roi_percentage:.2f}%")