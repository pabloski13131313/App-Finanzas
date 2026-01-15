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
        print(f"--- Parser: Leyendo PnL real de {file_path} ---")
        
        # 1. Leemos el archivo y buscamos la tabla 'Sells' igual que antes
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"No encuentro {file_path}")

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

        # 2. Convertimos a DataFrame
        csv_content = "".join(sells_lines)
        df = pd.read_csv(io.StringIO(csv_content))

        # 3. Mapeo REAL de datos financieros
        for index, row in df.iterrows():
            try:
                # Cost Basis = Lo que invertiste
                invested = float(row.get('Cost basis', 0.0))
                
                # Gross PnL = Tu ganancia o pérdida neta en dólares
                pnl = float(row.get('Gross PnL', 0.0))
                
                t = Transaction(
                    id=str(index),
                    date=pd.to_datetime(row['Date sold']),
                    description=row['Security name'],
                    invested=invested,
                    profit_amount=pnl  # Guardamos el PnL directo del CSV
                )
                transactions.append(t)
            except Exception as e:
                continue

        return transactions
    
