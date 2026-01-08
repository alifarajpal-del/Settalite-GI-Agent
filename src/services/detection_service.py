"""
خدمة كشف الشذوذ باستخدام ML
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

class AnomalyDetectionService:
    """
    خدمة كشف الأنماط الشاذة
    """
    
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
        
    def detect_anomalies(
        self,
        indices: Dict[str, np.ndarray],
        algorithm: str = 'isolation_forest',
        contamination: float = 0.1,
        n_estimators: int = 100,
        features: list = None
    ) -> Dict:
        """
        كشف الشذوذ من المؤشرات الطيفية
        
        Args:
            indices: قاموس المؤشرات
            algorithm: خوارزمية الكشف
            contamination: نسبة التلوث
            n_estimators: عدد المقدرات
            features: المميزات المستخدمة
        
        Returns:
            قاموس يحتوي على نتائج الكشف
        """
        self.logger.info(f"بدء كشف الشذوذ باستخدام {algorithm}")
        
        # تحضير البيانات
        X = self._prepare_features(indices, features)
        
        # تطبيع البيانات
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X.reshape(-1, X.shape[-1]))
        
        # تطبيق الخوارزمية
        if algorithm == 'isolation_forest':
            model = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                random_state=42
            )
        elif algorithm == 'local_outlier_factor':
            model = LocalOutlierFactor(
                contamination=contamination,
                novelty=False
            )
        else:
            self.logger.warning(f"خوارزمية غير مدعومة: {algorithm}, استخدام isolation_forest")
            model = IsolationForest(contamination=contamination, random_state=42)
        
        # التنبؤ
        predictions = model.fit_predict(X_scaled)
        
        # تحويل إلى خريطة شذوذ
        anomaly_map = predictions.reshape(list(indices.values())[0].shape)
        anomaly_map = (anomaly_map == -1).astype(float)
        
        # حساب درجة الشذوذ
        if hasattr(model, 'score_samples'):
            anomaly_scores = -model.score_samples(X_scaled)
            anomaly_surface = anomaly_scores.reshape(list(indices.values())[0].shape)
            anomaly_surface = (anomaly_surface - anomaly_surface.min()) / (anomaly_surface.max() - anomaly_surface.min())
        else:
            anomaly_surface = anomaly_map
        
        result = {
            'anomaly_map': anomaly_map,
            'anomaly_surface': anomaly_surface,
            'statistics': {
                'total_pixels': anomaly_map.size,
                'anomaly_pixels': int(np.sum(anomaly_map)),
                'anomaly_percentage': float(np.mean(anomaly_map) * 100),
                'mean_anomaly_score': float(np.mean(anomaly_surface))
            }
        }
        
        self.logger.info(f"تم اكتشاف {result['statistics']['anomaly_pixels']} بكسل شاذ")
        
        return result
    
    def _prepare_features(self, indices: Dict, features: list = None) -> np.ndarray:
        """
        تحضير المميزات للتحليل
        """
        if features is None:
            features = list(indices.keys())
        
        # استخراج المميزات المحددة
        feature_arrays = []
        for feature in features:
            if feature in indices:
                feature_arrays.append(indices[feature])
        
        if not feature_arrays:
            raise ValueError("لا توجد مميزات متاحة")
        
        # تكديس المميزات
        X = np.stack(feature_arrays, axis=-1)
        
        # استبدال NaN بالمتوسط
        for i in range(X.shape[-1]):
            channel = X[:, :, i]
            channel_mean = np.nanmean(channel)
            channel[np.isnan(channel)] = channel_mean
        
        return X
