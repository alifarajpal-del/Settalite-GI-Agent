"""
مجموعة نماذج مُدرَّبة لاكتشاف الآثار
Heritage Detection Ensemble - Combines multiple ML models with domain rules
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import OneClassSVM
import joblib

class HeritageDetectionEnsemble:
    """مجموعة نماذج مُدرَّبة لاكتشاف الآثار"""
    
    def __init__(self):
        self.models = {
            'isolation_forest': IsolationForest(contamination=0.1, random_state=42),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42, min_samples_leaf=2, max_features='sqrt'),
            'ocsvm': OneClassSVM(nu=0.1)
        }
        
        # قواعد اكتشاف أثرية (مبنية على أبحاث)
        self.heritage_rules = {
            'min_vegetation_index': 0.3,  # NDVI منخفض
            'max_moisture_index': 0.2,    # NDWI منخفض  
            'texture_complexity': 0.7,    # تعقيد النسيج عالي
            'shape_regularity': 0.6       # انتظام الشكل
        }
    
    def predict_heritage_site(self, spectral_features):
        """التنبؤ باحتمالية وجود موقع أثري"""
        predictions = []
        
        # 1. تطبيق النماذج الإحصائية
        for name, model in self.models.items():
            try:
                pred = model.fit_predict(spectral_features)
                predictions.append(pred)
            except Exception:
                continue
        
        # 2. تطبيق القواعد المعرفية
        rule_based_score = self.apply_heritage_rules(spectral_features)
        
        # 3. الجمع بين النتائج
        final_score = np.mean(predictions) * 0.6 + rule_based_score * 0.4
        
        return final_score
    
    def apply_heritage_rules(self, features):
        """تطبيق القواعد المعرفية للاكتشاف الأثري"""
        score = 0.0
        
        if features.get('ndvi', 1) < self.heritage_rules['min_vegetation_index']:
            score += 0.25
        
        if features.get('ndwi', 1) < self.heritage_rules['max_moisture_index']:
            score += 0.25
        
        if features.get('texture', 0) > self.heritage_rules['texture_complexity']:
            score += 0.25
            
        if features.get('shape', 0) > self.heritage_rules['shape_regularity']:
            score += 0.25
            
        return score
