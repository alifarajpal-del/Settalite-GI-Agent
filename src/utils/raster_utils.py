"""
أدوات معالجة البيانات النقطية (Raster)
"""
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask as rasterio_mask
from typing import Tuple, Dict
from shapely.geometry import mapping

def read_raster(file_path: str) -> Tuple[np.ndarray, Dict]:
    """
    قراءة ملف raster
    
    Args:
        file_path: مسار الملف
    
    Returns:
        tuple: (data_array, metadata)
    """
    with rasterio.open(file_path) as src:
        data = src.read(1)  # قراءة النطاق الأول
        metadata = {
            'transform': src.transform,
            'crs': src.crs.to_string(),
            'width': src.width,
            'height': src.height,
            'dtype': src.dtypes[0],
            'nodata': src.nodata
        }
    
    return data, metadata

def write_raster(
    data: np.ndarray,
    output_path: str,
    transform,
    crs: str,
    nodata_value: float = None
):
    """
    كتابة بيانات إلى ملف raster
    
    Args:
        data: مصفوفة البيانات
        output_path: مسار الملف الناتج
        transform: تحويل الإحداثيات
        crs: نظام الإحداثيات
        nodata_value: قيمة NoData
    """
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        nodata=nodata_value,
        compress='lzw'
    ) as dst:
        dst.write(data, 1)

def normalize_band(band: np.ndarray, method: str = 'minmax') -> np.ndarray:
    """
    تطبيع بيانات النطاق
    
    Args:
        band: مصفوفة النطاق
        method: طريقة التطبيع ('minmax', 'zscore')
    
    Returns:
        مصفوفة مُطبّعة
    """
    # تجاهل قيم NaN
    valid_data = band[~np.isnan(band)]
    
    if method == 'minmax':
        min_val = np.nanmin(valid_data)
        max_val = np.nanmax(valid_data)
        
        if max_val == min_val:
            return np.zeros_like(band)
        
        normalized = (band - min_val) / (max_val - min_val)
    
    elif method == 'zscore':
        mean_val = np.nanmean(valid_data)
        std_val = np.nanstd(valid_data)
        
        if std_val == 0:
            return np.zeros_like(band)
        
        normalized = (band - mean_val) / std_val
    
    else:
        raise ValueError(f"طريقة تطبيع غير مدعومة: {method}")
    
    return normalized

def clip_raster_by_geometry(
    raster_path: str,
    geometry,
    output_path: str = None
) -> Tuple[np.ndarray, Dict]:
    """
    قص raster باستخدام geometry
    
    Args:
        raster_path: مسار الملف
        geometry: كائن Shapely
        output_path: مسار الملف الناتج (اختياري)
    
    Returns:
        tuple: (clipped_data, metadata)
    """
    with rasterio.open(raster_path) as src:
        # قص البيانات
        clipped_data, clipped_transform = rasterio_mask(
            src,
            [mapping(geometry)],
            crop=True,
            all_touched=True
        )
        
        metadata = {
            'transform': clipped_transform,
            'crs': src.crs.to_string(),
            'width': clipped_data.shape[2],
            'height': clipped_data.shape[1],
            'dtype': clipped_data.dtype,
            'nodata': src.nodata
        }
        
        # حفظ النتيجة إذا كان هناك مسار
        if output_path:
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=clipped_data.shape[1],
                width=clipped_data.shape[2],
                count=clipped_data.shape[0],
                dtype=clipped_data.dtype,
                crs=src.crs,
                transform=clipped_transform,
                nodata=src.nodata
            ) as dst:
                dst.write(clipped_data)
    
    return clipped_data[0], metadata

def resample_raster(
    data: np.ndarray,
    src_transform,
    src_crs: str,
    target_resolution: float
) -> Tuple[np.ndarray, object]:
    """
    إعادة عينة raster إلى دقة جديدة
    
    Args:
        data: مصفوفة البيانات
        src_transform: التحويل الأصلي
        src_crs: نظام الإحداثيات
        target_resolution: الدقة المستهدفة
    
    Returns:
        tuple: (resampled_data, new_transform)
    """
    # حساب الأبعاد الجديدة
    scale_factor = abs(src_transform.a) / target_resolution
    new_width = int(data.shape[1] * scale_factor)
    new_height = int(data.shape[0] * scale_factor)
    
    # حساب التحويل الجديد
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs, src_crs,
        data.shape[1], data.shape[0],
        *rasterio.transform.array_bounds(data.shape[0], data.shape[1], src_transform)[:4],
        resolution=target_resolution
    )
    
    # إعادة العينة
    resampled = np.zeros((dst_height, dst_width), dtype=data.dtype)
    
    reproject(
        source=data,
        destination=resampled,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=src_crs,
        resampling=Resampling.bilinear
    )
    
    return resampled, dst_transform

def calculate_statistics(data: np.ndarray) -> Dict[str, float]:
    """
    حساب إحصاءات البيانات
    
    Args:
        data: مصفوفة البيانات
    
    Returns:
        قاموس الإحصاءات
    """
    valid_data = data[~np.isnan(data)]
    
    if len(valid_data) == 0:
        return {
            'min': np.nan,
            'max': np.nan,
            'mean': np.nan,
            'std': np.nan,
            'median': np.nan,
            'count': 0
        }
    
    return {
        'min': float(np.min(valid_data)),
        'max': float(np.max(valid_data)),
        'mean': float(np.mean(valid_data)),
        'std': float(np.std(valid_data)),
        'median': float(np.median(valid_data)),
        'percentile_25': float(np.percentile(valid_data, 25)),
        'percentile_75': float(np.percentile(valid_data, 75)),
        'count': len(valid_data)
    }

def apply_histogram_equalization(data: np.ndarray, bins: int = 256) -> np.ndarray:
    """
    تطبيق معادلة الهستوغرام لتحسين التباين
    
    Args:
        data: مصفوفة البيانات
        bins: عدد الفئات
    
    Returns:
        بيانات معادلة
    """
    from skimage import exposure
    
    # تجاهل قيم NaN
    mask = ~np.isnan(data)
    equalized = np.copy(data)
    
    if np.sum(mask) > 0:
        equalized[mask] = exposure.equalize_hist(data[mask], nbins=bins)
    
    return equalized
