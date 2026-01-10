"""
خدمة بيانات وهمية للاختبار والتطوير بدون الحاجة لبيانات أقمار صناعية حقيقية
تم تصميمها خصيصاً لمشروع Heritage Sentinel Pro
"""

import numpy as np
from numpy.random import default_rng
import pandas as pd
from shapely.geometry import Polygon, Point
import json
from datetime import datetime

class MockDataService:
    """خدمة توليد بيانات تجريبية وهمية للمشروع"""
    
    @staticmethod
    def get_mock_config():
        """إرجاع تكوين وهمي للتطبيق"""
        return {
            'app': {'name': 'Heritage Sentinel Pro', 'version': '1.0.0'},
            'paths': {
                'data_dir': 'data',
                'output_dir': 'outputs',
                'exports': 'exports'
            },
            'processing': {
                'anomaly_detection': {'confidence_threshold': 0.7},
                'coordinate_extraction': {'min_anomaly_area': 100}
            }
        }
    
    @staticmethod
    def create_mock_aoi(center_lon=31.2350, center_lat=30.0250, size=0.01):
        """
        إنشاء منطقة اهتمام وهمية (AOI) حول موقع معين
        
        Args:
            center_lon (float): خط الطول المركزي
            center_lat (float): خط العرض المركزي
            size (float): حجم المنطقة بالدرجات
            
        Returns:
            Polygon: منطقة اهتمام وهمية
        """
        half_size = size / 2
        return Polygon([
            (center_lon - half_size, center_lat - half_size),
            (center_lon + half_size, center_lat - half_size),
            (center_lon + half_size, center_lat + half_size),
            (center_lon - half_size, center_lat + half_size),
            (center_lon - half_size, center_lat - half_size)
        ])
    
    @staticmethod
    def generate_mock_satellite_data(width=100, height=100):
        """
        توليد بيانات أقمار صناعية وهمية بمختلف النطاقات الطيفية
        
        Args:
            width (int): عرض الصورة بالبكسل
            height (int): ارتفاع الصورة بالبكسل
            
        Returns:
            dict: بيانات الأقمار الصناعية الوهمية
        """
        rng = default_rng(42)  # لنتائج ثابتة
        
        # إنشاء بيانات وهمية ذات أنماط (ليست عشوائية بحتة)
        x = np.linspace(0, 10, width)
        y = np.linspace(0, 10, height)
        X, Y = np.meshgrid(x, y)
        
        # إنشاء أنماط مختلفة لكل نطاق طيفي
        bands_data = {
            'B02': np.sin(X) * np.cos(Y) + rng.normal(0, 0.1, (height, width)),  # Blue
            'B03': np.sin(X*0.8) * np.cos(Y*0.8) + rng.normal(0, 0.1, (height, width)),  # Green
            'B04': np.sin(X*1.2) * np.cos(Y*1.2) + rng.normal(0, 0.1, (height, width)),  # Red
            'B08': np.sin(X*0.5) * np.cos(Y*0.5) + rng.normal(0, 0.1, (height, width)),  # NIR
            'B11': np.sin(X*1.5) * np.cos(Y*1.5) + rng.normal(0, 0.1, (height, width)),  # SWIR1
            'B12': np.sin(X*2.0) * np.cos(Y*2.0) + rng.normal(0, 0.1, (height, width)),  # SWIR2
        }
        
        # تطبيع البيانات بين 0 و1
        for band in bands_data:
            bands_data[band] = (bands_data[band] - bands_data[band].min()) / (bands_data[band].max() - bands_data[band].min())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'satellite': 'Sentinel-2',
            'cloud_cover': 5.2,
            'resolution': 10,
            'crs': 'EPSG:4326',
            'transform': [31.2300, 0.000089, 0, 30.0300, 0, -0.000089],
            'bands': bands_data,
            'preview_generated': True
        }
    
    @staticmethod
    def generate_mock_anomaly_map(width=100, height=100, num_anomalies=8):
        """
        توليد خريطة شذوذ وهمية تحتوي على مناطق مكتشفة
        
        Args:
            width (int): عرض الخريطة
            height (int): ارتفاع الخريطة
            num_anomalies (int): عدد المناطق الشاذة
            
        Returns:
            numpy.ndarray: خريطة الشذوذ الوهمية
        """
        rng = default_rng(42)
        anomaly_map = np.zeros((height, width))
        
        # إضافة مناطق شاذة (دوائر بأنماط مختلفة)
        for _ in range(num_anomalies):
            center_x = rng.integers(20, width-20)
            center_y = rng.integers(20, height-20)
            radius = rng.integers(8, 25)
            intensity = rng.uniform(0.6, 0.95)
            
            # إنشاء دائرة من الشذوذ
            for x in range(max(0, center_x-radius), min(width, center_x+radius)):
                for y in range(max(0, center_y-radius), min(height, center_y+radius)):
                    distance = np.sqrt((x-center_x)**2 + (y-center_y)**2)
                    if distance < radius:
                        value = intensity * (1 - distance/radius)
                        anomaly_map[y, x] = max(anomaly_map[y, x], value)
        
        # إضافة ضجيج خلفية
        noise = rng.normal(0, 0.05, (height, width))
        anomaly_map = np.clip(anomaly_map + noise, 0, 1)
        
        return anomaly_map
    
    @staticmethod
    def generate_mock_detections(num_sites=12):
        """
        توليد اكتشافات أثرية وهمية مع خصائص متنوعة
        
        Args:
            num_sites (int): عدد المواقع المكتشفة
            
        Returns:
            pandas.DataFrame: جدول البيانات الوهمية
        """
        rng = default_rng(42)
        
        sites_data = []
        
        for i in range(num_sites):
            site_id = f"HS_{datetime.now().strftime('%Y%m')}_{i+1:03d}"
            
            # إحداثيات وهمية في منطقة القاهرة التاريخية
            lon = 31.2350 + rng.uniform(-0.005, 0.005)
            lat = 30.0250 + rng.uniform(-0.005, 0.005)
            
            # خصائص الموقع
            confidence = rng.uniform(0.65, 0.96)
            area_m2 = rng.uniform(300, 6000)
            anomaly_intensity = rng.uniform(0.7, 0.98)
            
            # تحديد الأولوية بناء على الثقة والشدة
            if confidence > 0.85 and anomaly_intensity > 0.9:
                priority = "عالي"
                priority_en = "high"
            elif confidence > 0.75:
                priority = "متوسط"
                priority_en = "medium"
            else:
                priority = "منخفض"
                priority_en = "low"
            
            # تحديد نوع الموقع المحتمل
            site_types = ["مستوطنة أثرية", "مبنى قديم", "هيكل دفاعي", "منطقة صناعية", "معبد"]
            site_type = rng.choice(site_types, p=[0.3, 0.25, 0.2, 0.15, 0.1])
            
            # توصية ميدانية
            if priority_en == "high":
                recommendation = "تحتاج لتحقق ميداني عاجل - احتمالية عالية لإكتشاف مهم"
            elif priority_en == "medium":
                recommendation = "يوصى بتحقق ميداني في المرحلة القادمة"
            else:
                recommendation = "مراقبة وتقييم بالمزيد من البيانات"
            
            sites_data.append({
                'ID الموقع': site_id,
                'خط الطول': round(lon, 6),
                'خط العرض': round(lat, 6),
                'الثقة (%)': round(confidence * 100, 1),
                'المساحة (م²)': round(area_m2),
                'شدة الشذوذ': round(anomaly_intensity, 3),
                'الأولوية': priority,
                'الأولوية (EN)': priority_en,
                'النوع المحتمل': site_type,
                'التوصية': recommendation,
                'تاريخ الاكتشاف': datetime.now().strftime('%Y-%m-%d')
            })
        
        return pd.DataFrame(sites_data)
    
    @staticmethod
    def create_mock_geojson_features():
        """إنشاء بيانات GeoJSON وهمية للعرض على الخريطة"""
        df = MockDataService.generate_mock_detections()
        
        features = []
        for _, row in df.iterrows():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['خط الطول'], row['خط العرض']]
                },
                "properties": {
                    "site_id": row['ID الموقع'],
                    "confidence": row['الثقة (%)'],
                    "area_m2": row['المساحة (م²)'],
                    "priority": row['الأولوية (EN)'],
                    "type": row['النوع المحتمل']
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
