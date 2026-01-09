"""
PROMPT 6: Ground Truth Evaluation
Compare detected sites against known archaeological sites.

Metrics:
- Precision: What % of detections are correct?
- Recall: What % of known sites are detected?
- F1 Score: Harmonic mean
- Confusion matrix (TP, FP, FN, TN)
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Any, List
import logging
import json


class GroundTruthEvaluator:
    """
    Evaluate detection results against ground truth archaeological data.
    
    PROMPT 6: Rigorous evaluation framework that:
    1. Loads known archaeological site locations
    2. Matches detected anomalies to known sites
    3. Computes precision/recall/F1
    4. Identifies new discoveries vs false positives
    """
    
    def __init__(self, logger: logging.Logger = None):
        """Initialize evaluator."""
        self.logger = logger or logging.getLogger(__name__)
        self.known_sites = None
    
    def load_ground_truth(
        self,
        source: str,
        format: str = 'geojson'
    ) -> bool:
        """
        Load known archaeological sites from file.
        
        Supported formats:
        - geojson: GeoJSON file with site locations
        - shapefile: ESRI Shapefile
        - csv: CSV with latitude, longitude columns
        
        Args:
            source: File path or URL
            format: File format
        
        Returns:
            True if successfully loaded
        """
        try:
            source_path = Path(source)
            
            if format == 'geojson' or source_path.suffix == '.geojson':
                self.known_sites = gpd.read_file(source, driver='GeoJSON')
            elif format == 'shapefile' or source_path.suffix == '.shp':
                self.known_sites = gpd.read_file(source)
            elif format == 'csv' or source_path.suffix == '.csv':
                df = pd.read_csv(source)
                geometry = gpd.points_from_xy(df['longitude'], df['latitude'])
                self.known_sites = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
            else:
                try:
                    self.known_sites = gpd.read_file(source)
                except Exception as e:
                    self.logger.error(f"Failed to load ground truth: {e}")
                    return False
            
            self.logger.info(f"Loaded {len(self.known_sites)} known archaeological sites")
            return True
        
        except Exception as e:
            self.logger.error(f"Error loading ground truth: {e}")
            return False
    
    def evaluate(
        self,
        detected_sites,
        match_distance_m: float = 250.0
    ) -> Dict[str, Any]:
        """
        Evaluate detected sites against ground truth.
        
        Args:
            detected_sites: GeoDataFrame with detected anomalies
            match_distance_m: Distance threshold for matching (default 250m)
        
        Returns:
            Dict with evaluation metrics:
            {
                'confusion_matrix': {
                    'true_positives': int,
                    'false_positives': int,
                    'false_negatives': int
                },
                'metrics': {
                    'precision': float,
                    'recall': float,
                    'f1_score': float,
                    'accuracy': float
                },
                'details': {
                    'detected_sites': [site details],
                    'matched_sites': [matched pairs],
                    'unmatched_known': [sites not detected]
                }
            }
        """
        if self.known_sites is None or self.known_sites.empty:
            self.logger.warning("No ground truth data loaded - cannot evaluate")
            return {
                'status': 'NO_GROUND_TRUTH',
                'message': 'Ground truth not loaded. Use load_ground_truth() first.',
                'detected_sites_count': len(detected_sites) if detected_sites is not None else 0
            }
        
        if detected_sites is None or detected_sites.empty:
            self.logger.warning("No detected sites to evaluate")
            return {
                'confusion_matrix': {
                    'true_positives': 0,
                    'false_positives': 0,
                    'false_negatives': len(self.known_sites)
                },
                'metrics': {
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1_score': 0.0
                }
            }
        
        # Convert distance threshold to degrees (~111km per degree)
        match_distance_deg = match_distance_m / 111000.0
        
        true_positives = []
        false_positives = []
        matched_known_indices = set()
        
        # Match detected sites to known sites
        for det_idx, detected in detected_sites.iterrows():
            best_match = None
            best_distance = match_distance_deg
            best_known_idx = None
            
            for known_idx, known in self.known_sites.iterrows():
                distance = detected.geometry.distance(known.geometry)
                if distance < best_distance:
                    best_distance = distance
                    best_match = known
                    best_known_idx = known_idx
            
            if best_match is not None:
                true_positives.append({
                    'detected': detected,
                    'known': best_match,
                    'distance_m': best_distance * 111000,
                    'detected_idx': det_idx,
                    'known_idx': best_known_idx
                })
                matched_known_indices.add(best_known_idx)
            else:
                false_positives.append({
                    'detected': detected,
                    'detected_idx': det_idx
                })
        
        # Remaining known sites are false negatives
        false_negatives = []
        for known_idx, known in self.known_sites.iterrows():
            if known_idx not in matched_known_indices:
                false_negatives.append({
                    'known': known,
                    'known_idx': known_idx
                })
        
        # Calculate metrics
        tp_count = len(true_positives)
        fp_count = len(false_positives)
        fn_count = len(false_negatives)
        
        precision = (
            tp_count / (tp_count + fp_count)
            if (tp_count + fp_count) > 0
            else 0.0
        )
        recall = (
            tp_count / (tp_count + fn_count)
            if (tp_count + fn_count) > 0
            else 0.0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        
        # Accuracy not defined in single-class scenario, use harmonic mean
        accuracy = f1_score
        
        self.logger.info(f"Evaluation: TP={tp_count}, FP={fp_count}, FN={fn_count}")
        self.logger.info(f"Precision={precision:.3f}, Recall={recall:.3f}, F1={f1_score:.3f}")
        
        return {
            'status': 'SUCCESS',
            'confusion_matrix': {
                'true_positives': tp_count,
                'false_positives': fp_count,
                'false_negatives': fn_count
            },
            'metrics': {
                'precision': round(precision, 3),
                'recall': round(recall, 3),
                'f1_score': round(f1_score, 3),
                'accuracy': round(accuracy, 3)
            },
            'details': {
                'matched_pairs': len(true_positives),
                'new_discoveries': fp_count,
                'missed_sites': fn_count,
                'total_detected': len(detected_sites),
                'total_known': len(self.known_sites)
            }
        }
    
    def save_evaluation(
        self,
        evaluation_result: Dict[str, Any],
        output_path: str = 'outputs/evaluation.json'
    ) -> bool:
        """Save evaluation results to JSON."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Convert numpy types for JSON serialization
            serializable = json.loads(json.dumps(evaluation_result, default=str))
            
            with open(output_path, 'w') as f:
                json.dump(serializable, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Evaluation saved to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save evaluation: {e}")
            return False
    
    def compare_detectors(
        self,
        results: List[Dict[str, Any]],
        output_path: str = 'outputs/comparison.csv'
    ) -> pd.DataFrame:
        """
        Compare multiple detection results.
        
        Args:
            results: List of evaluation results
            output_path: Where to save comparison
        
        Returns:
            DataFrame with comparison
        """
        comparisons = []
        
        for result in results:
            comparisons.append({
                'detector': result.get('name', 'unknown'),
                'detected': result.get('metrics', {}).get('total_detected', 0),
                'precision': result.get('metrics', {}).get('precision', 0),
                'recall': result.get('metrics', {}).get('recall', 0),
                'f1_score': result.get('metrics', {}).get('f1_score', 0)
            })
        
        df = pd.DataFrame(comparisons)
        df = df.sort_values('f1_score', ascending=False)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        self.logger.info(f"Comparison saved to {output_path}")
        return df
