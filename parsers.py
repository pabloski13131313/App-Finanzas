import pandas as pd
import io
from abc import ABC, abstractmethod
from typing import List
from transaction import Transaction

class IDataParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Transaction]:
        pass

class RevolutCSVParser(IDataParser):
    def parse(self, file_path: str) -> List[Transaction]:
        transactions = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            return []

        # Limpieza de cabeceras
        sells_lines = []
        capture = False
        expected_header = "Date acquired" 
        
        for line in lines:
            if expected_header in line:
                capture = True
                sells_lines.append(line)
                continue
            if capture:
                if not line.strip() or "Other income" in line:
                    break
                sells_lines.append(line)

        if not sells_lines:
            return []

        csv_content = "".join(sells_lines)
        df = pd.read_csv(io.StringIO(csv_content))

        for index, row in df.iterrows():
            try:
                # Datos básicos
                invested = float(row.get('Cost basis', 0.0))
                pnl = float(row.get('Gross PnL', 0.0))
                qty = float(row.get('Quantity', 0.0))
                
                # --- NUEVO: Capturamos Fecha de Compra ---
                date_acquired_str = row.get('Date acquired')
                
                t = Transaction(
                    id=str(index),
                    date=pd.to_datetime(row['Date sold']), # Fecha Venta
                    description=row['Security name'],
                    invested=invested,
                    profit_amount=pnl
                )
                
                # Guardamos los datos extra
                t.quantity = qty 
                t.date_acquired = pd.to_datetime(date_acquired_str) # Guardamos fecha compra
                
                transactions.append(t)
            except Exception:
                continue

        return transactions
