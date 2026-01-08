"""
خدمة الوضع الفعلي - تدمج جميع الخدمات الحقيقية
"""
import sys
import os
from pathlib import Path
import yaml
import logging
from datetime import datetime

class LiveModeService:
    """إدارة وتحويل النظام من الوضع التجريبي إلى الفعلي"""
    
    def __init__(self, config_path="config/config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.services = {}
        
    def _load_config(self, config_path):
        """تحميل تكوين النظام"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"ملف التكوين غير موجود: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logger(self):
        """إعداد نظام التسجيل"""
        logger = logging.getLogger("HeritageSentinelLive")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # ملف السجل
            log_file = Path("logs/live_mode.log")
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            
            # وحدة التحكم
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def initialize_services(self):
        """تهيئة جميع الخدمات الفعلية"""
        self.logger.info("بدء تهيئة خدمات الوضع الفعلي...")
        
        services_status = {}
        
        try:
            # 1. خدمة استخراج الإحداثيات
            from .coordinate_extractor import CoordinateExtractor
            self.services['coordinate_extractor'] = CoordinateExtractor(
                self.config, 
                self.logger
            )
            services_status['coordinate_extractor'] = "✅"
            self.logger.info("تهيئة خدمة استخراج الإحداثيات - ناجحة")
        except Exception as e:
            services_status['coordinate_extractor'] = f"❌ ({str(e)})"
            self.logger.error(f"فشل تهيئة خدمة استخراج الإحداثيات: {e}")
        
        try:
            # 2. خدمة المعالجة المتقدمة
            from .processing_service import AdvancedProcessingService
            self.services['processing_service'] = AdvancedProcessingService(
                self.config,
                self.logger
            )
            services_status['processing_service'] = "✅"
            self.logger.info("تهيئة خدمة المعالجة المتقدمة - ناجحة")
        except Exception as e:
            services_status['processing_service'] = f"❌ ({str(e)})"
            self.logger.error(f"فشل تهيئة خدمة المعالجة المتقدمة: {e}")
        
        try:
            # 3. خدمة كشف الشذوذ
            from .detection_service import AnomalyDetectionService
            self.services['detection_service'] = AnomalyDetectionService(
                self.config,
                self.logger
            )
            services_status['detection_service'] = "✅"
            self.logger.info("تهيئة خدمة كشف الشذوذ - ناجحة")
        except Exception as e:
            services_status['detection_service'] = f"❌ ({str(e)})"
            self.logger.error(f"فشل تهيئة خدمة كشف الشذوذ: {e}")
        
        # محاولة تحميل خدمة الأقمار الصناعية (اختياري)
        try:
            from .satellite_service import SatelliteService
            self.services['satellite_service'] = SatelliteService(
                self.config,
                self.logger
            )
            services_status['satellite_service'] = "✅"
            self.logger.info("تهيئة خدمة الأقمار الصناعية - ناجحة")
        except Exception as e:
            services_status['satellite_service'] = f"⚠️ ({str(e)})"
            self.logger.warning(f"خدمة الأقمار الصناعية غير متوفرة: {e}")
        
        try:
            # 4. خدمة التصدير
            from .export_service import ExportService
            self.services['export_service'] = ExportService(
                self.config,
                self.logger
            )
            services_status['export_service'] = "✅"
            self.logger.info("تهيئة خدمة التصدير - ناجحة")
        except Exception as e:
            services_status['export_service'] = f"❌ ({str(e)})"
            self.logger.error(f"فشل تهيئة خدمة التصدير: {e}")
        
        self.logger.info(f"اكتملت تهيئة الخدمات: {services_status}")
        return services_status
    
    def run_full_pipeline(self, aoi_geometry, start_date, end_date, data_sources=None):
        """
        تشغيل خط الأنابيب الكامل في الوضع الفعلي
        
        Args:
            aoi_geometry: منطقة الاهتمام
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            data_sources: مصادر البيانات
            
        Returns:
            dict: نتائج التحليل
        """
        self.logger.info("بدء تشغيل خط الأنابيب الكامل...")
        
        results = {
            'status': 'pending',
            'steps': {},
            'detections': None,
            'reports': None
        }
        
        try:
            # الخطوة 1: جلب بيانات الأقمار الصناعية
            if 'satellite_service' in self.services:
                self.logger.info("جلب بيانات الأقمار الصناعية...")
                satellite_data = self.services['satellite_service'].download_sentinel_data(
                    aoi_geometry, start_date, end_date, max_cloud_cover=30
                )
                results['steps']['satellite_data'] = {
                    'status': 'success',
                    'message': f"تم جلب {len(satellite_data.get('bands', {}))} نطاق"
                }
            else:
                # استخدام بيانات وهمية كاحتياطي
                from .mock_data_service import MockDataService
                mock = MockDataService()
                satellite_data = mock.generate_mock_satellite_data()
                results['steps']['satellite_data'] = {
                    'status': 'warning',
                    'message': 'استخدام بيانات وهمية (خدمة الأقمار الصناعية غير متوفرة)'
                }
            
            # الخطوة 2: المعالجة المتقدمة
            if 'processing_service' in self.services:
                self.logger.info("المعالجة المتقدمة...")
                processed_data = self.services['processing_service'].calculate_spectral_indices(
                    satellite_data['bands']
                )
                results['steps']['processing'] = {
                    'status': 'success',
                    'message': f"تم حساب {len(processed_data)} مؤشر"
                }
            else:
                results['steps']['processing'] = {
                    'status': 'skipped',
                    'message': 'خدمة المعالجة غير متوفرة'
                }
                processed_data = {}
            
            # الخطوة 3: كشف الشذوذ
            if 'detection_service' in self.services and processed_data:
                self.logger.info("كشف الأنماط الشاذة...")
                anomaly_results = self.services['detection_service'].detect_anomalies(
                    processed_data
                )
                results['steps']['anomaly_detection'] = {
                    'status': 'success',
                    'message': 'اكتمل كشف الشذوذ'
                }
            else:
                # توليد شذوذ وهمي
                from .mock_data_service import MockDataService
                mock = MockDataService()
                anomaly_map = mock.generate_mock_anomaly_map()
                anomaly_results = {'anomaly_surface': anomaly_map}
                results['steps']['anomaly_detection'] = {
                    'status': 'warning',
                    'message': 'استخدام بيانات شذوذ وهمية'
                }
            
            # الخطوة 4: استخراج الإحداثيات
            if 'coordinate_extractor' in self.services:
                self.logger.info("استخراج الإحداثيات الدقيقة...")
                detections = self.services['coordinate_extractor'].extract_precise_coordinates(
                    anomaly_results['anomaly_surface'],
                    satellite_data['transform'],
                    satellite_data['crs'],
                    aoi_geometry
                )
                
                results['detections'] = detections
                results['steps']['coordinate_extraction'] = {
                    'status': 'success',
                    'message': f"تم اكتشاف {detections.get('total_detections', 0)} موقع"
                }
            else:
                results['steps']['coordinate_extraction'] = {
                    'status': 'error',
                    'message': 'خدمة استخراج الإحداثيات غير متوفرة'
                }
            
            results['status'] = 'completed'
            self.logger.info("اكتمل خط الأنابيب بنجاح")
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            self.logger.error(f"فشل خط الأنابيب: {e}")
        
        return results
    
    def generate_live_report(self, pipeline_results, output_format='html'):
        """إنشاء تقرير حي من نتائج خط الأنابيب"""
        self.logger.info(f"إنشاء تقرير بتنسيق {output_format}...")
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_status': pipeline_results['status'],
            'steps': pipeline_results['steps'],
            'summary': {}
        }
        
        if pipeline_results['detections']:
            detections = pipeline_results['detections']
            report_data['summary'] = {
                'total_sites': detections.get('total_detections', 0),
                'high_confidence': detections.get('statistics', {}).get('high_confidence_detections', 0),
                'success_rate': len([s for s in pipeline_results['steps'].values() 
                                   if s['status'] == 'success']) / max(len(pipeline_results['steps']), 1)
            }
        
        # حفظ التقرير
        report_dir = Path(self.config['paths']['outputs']) / 'live_reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"live_report_{timestamp}.json"
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"تم حفظ التقرير في: {report_file}")
        return report_file
    
    def export_results(self, detections, formats=['geojson', 'csv'], output_dir='exports'):
        """تصدير النتائج بتنسيقات متعددة"""
        if 'export_service' not in self.services:
            self.logger.warning("خدمة التصدير غير متوفرة")
            return None
        
        self.logger.info(f"تصدير النتائج بالتنسيقات: {formats}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"live_detections_{timestamp}"
        
        export_paths = self.services['export_service'].export_all(
            detections['clusters'],
            formats,
            output_dir,
            base_name
        )
        
        self.logger.info(f"تم التصدير إلى: {export_paths}")
        return export_paths
    
    def validate_api_keys(self):
        """التحقق من صحة مفاتيح API المطلوبة"""
        self.logger.info("التحقق من مفاتيح API...")
        
        api_keys_file = Path("config/api_keys.yaml")
        if not api_keys_file.exists():
            return {
                'status': 'missing',
                'message': 'ملف مفاتيح API غير موجود'
            }
        
        try:
            with open(api_keys_file, 'r', encoding='utf-8') as f:
                api_keys = yaml.safe_load(f)
            
            validation = {
                'sentinel': False,
                'nasa': False
            }
            
            # التحقق من Sentinel Hub
            if 'sentinel' in api_keys:
                sentinel = api_keys['sentinel']
                validation['sentinel'] = all([
                    sentinel.get('client_id'),
                    sentinel.get('client_secret'),
                    sentinel.get('instance_id')
                ])
            
            # التحقق من NASA Earthdata
            if 'nasa' in api_keys:
                nasa = api_keys['nasa']
                validation['nasa'] = all([
                    nasa.get('username'),
                    nasa.get('password')
                ])
            
            if any(validation.values()):
                return {
                    'status': 'valid',
                    'providers': validation
                }
            else:
                return {
                    'status': 'incomplete',
                    'message': 'مفاتيح API غير مكتملة'
                }
                
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من مفاتيح API: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
