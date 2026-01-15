from abc import ABC, abstractmethod

class PerformanceStrategy(ABC):
    @abstractmethod
    def calculate(self, invested: float, profit: float) -> float:
        pass

class RoiStrategy(PerformanceStrategy):
    """
    Calcula el Retorno de Inversión (ROI) en porcentaje.
    Fórmula: (Ganancia / Inversión Inicial) * 100
    """
    def calculate(self, invested: float, profit: float) -> float:
        if invested == 0:
            return 0.0
        return (profit / invested) * 100