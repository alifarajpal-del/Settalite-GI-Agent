"""
نموذج كشف الشذوذ
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetector:
    """
    كاشف الشذوذ المتقدم
    """
    
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.model = None
        self.scaler = StandardScaler()
    
    def fit(self, X: np.ndarray):
        """
        تدريب النموذج
        """
        x_scaled = self.scaler.fit_transform(X)
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42
        )
        self.model.fit(x_scaled)
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        التنبؤ بالشذوذ
        """
        x_scaled = self.scaler.transform(X)
        predictions = self.model.predict(x_scaled)
        return (predictions == -1).astype(int)
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """
        حساب درجة الشذوذ
        """
        x_scaled = self.scaler.transform(X)
        scores = -self.model.score_samples(x_scaled)
        return scores
