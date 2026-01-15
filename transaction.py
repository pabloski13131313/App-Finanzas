from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    id: str
    date: datetime
    description: str      # Nombre de la acción (ej. Nike)
    invested: float       # Cost Basis (Lo que te costó)
    profit_amount: float  # Gross PnL (Dinero ganado/perdido en $)
    
    # Este será el resultado calculado (El porcentaje %)
    roi_percentage: float = 0.0