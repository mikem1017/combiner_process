"""
Compliance Checker for RF Combiner Analysis

Checks compliance against configurable thresholds:
1. Return Loss < -14dB
2. Gain Flatness < 0.8dBpp (per branch)
3. Max Gain Difference < 0.5dB (between branches)
4. Max Phase Difference < 10 degrees (between branches)
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class ComplianceChecker:
    """Checks RF combiner compliance against thresholds."""
    
    def __init__(self, config_path: str = "compliance_config.json"):
        """
        Initialize compliance checker with thresholds from JSON config.
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """Load compliance thresholds from JSON file."""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.return_loss_threshold_db = config['return_loss_threshold_db']
        self.gain_flatness_threshold_db = config['gain_flatness_threshold_db']
        self.max_gain_difference_db = config['max_gain_difference_db']
        self.max_phase_difference_degrees = config['max_phase_difference_degrees']
    
    def check_return_loss(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Check return loss compliance for all ports.
        
        Returns dictionary with pass/fail status and detailed results per port.
        """
        # Filter frequency range if specified
        if x_min is not None and x_max is not None:
            freq_mask = (frequency >= x_min) & (frequency <= x_max)
        else:
            freq_mask = np.ones(len(frequency), dtype=bool)
        
        results = {}
        all_pass = True
        
        # Check S11 (input port)
        if 'S11' in s_params:
            s11_db = 20 * np.log10(np.abs(s_params['S11']))
            s11_in_range = s11_db[freq_mask]
            worst_value = np.max(s11_in_range)  # Most positive (least negative)
            pass_status = worst_value < self.return_loss_threshold_db
            all_pass = all_pass and pass_status
            
            results['S11'] = {
                'pass': pass_status,
                'worst_value_db': worst_value,
                'threshold_db': self.return_loss_threshold_db
            }
        
        # Check S22 through S1010 (output ports)
        for i in range(2, 11):
            s_key = f'S{i}{i}'
            if s_key in s_params:
                sxx_db = 20 * np.log10(np.abs(s_params[s_key]))
                sxx_in_range = sxx_db[freq_mask]
                worst_value = np.max(sxx_in_range)
                pass_status = worst_value < self.return_loss_threshold_db
                all_pass = all_pass and pass_status
                
                results[s_key] = {
                    'pass': pass_status,
                    'worst_value_db': worst_value,
                    'threshold_db': self.return_loss_threshold_db
                }
        
        return {
            'all_pass': all_pass,
            'results': results,
            'check_name': 'Return Loss'
        }
    
    def check_gain_flatness(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Check gain flatness (peak-to-peak variation) for each branch.
        
        Returns dictionary with pass/fail status and detailed results per branch.
        """
        # Filter frequency range if specified
        if x_min is not None and x_max is not None:
            freq_mask = (frequency >= x_min) & (frequency <= x_max)
        else:
            freq_mask = np.ones(len(frequency), dtype=bool)
        
        results = {}
        all_pass = True
        
        # Check each branch (S21, S31, ..., S10_1)
        for i in range(2, 11):
            s_key = f'S{i}1'
            if s_key in s_params:
                sxy_db = 20 * np.log10(np.abs(s_params[s_key]))
                sxy_in_range = sxy_db[freq_mask]
                
                # Calculate peak-to-peak variation
                max_val = np.max(sxy_in_range)
                min_val = np.min(sxy_in_range)
                p2p_variation = max_val - min_val
                
                pass_status = p2p_variation < self.gain_flatness_threshold_db
                all_pass = all_pass and pass_status
                
                results[s_key] = {
                    'pass': pass_status,
                    'p2p_variation_db': p2p_variation,
                    'max_db': max_val,
                    'min_db': min_val,
                    'threshold_db': self.gain_flatness_threshold_db
                }
        
        return {
            'all_pass': all_pass,
            'results': results,
            'check_name': 'Gain Flatness'
        }
    
    def check_max_gain_difference(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Check maximum gain difference between branches at each frequency point.
        
        Returns dictionary with pass/fail status and worst-case difference.
        """
        # Filter frequency range if specified
        if x_min is not None and x_max is not None:
            freq_mask = (frequency >= x_min) & (frequency <= x_max)
        else:
            freq_mask = np.ones(len(frequency), dtype=bool)
        
        # Collect all branch magnitudes
        branch_mags = []
        branch_keys = []
        
        for i in range(2, 11):
            s_key = f'S{i}1'
            if s_key in s_params:
                sxy_db = 20 * np.log10(np.abs(s_params[s_key]))
                branch_mags.append(sxy_db[freq_mask])
                branch_keys.append(s_key)
        
        if len(branch_mags) < 2:
            return {
                'all_pass': True,
                'results': {'error': 'Insufficient branches for comparison'},
                'check_name': 'Max Gain Difference'
            }
        
        # Stack into array: [n_branches, n_frequencies]
        branch_mags_array = np.array(branch_mags)
        
        # Calculate max difference at each frequency point
        max_vals = np.max(branch_mags_array, axis=0)
        min_vals = np.min(branch_mags_array, axis=0)
        diff_at_each_freq = max_vals - min_vals
        
        # Find worst-case difference
        worst_diff = np.max(diff_at_each_freq)
        worst_freq_idx = np.argmax(diff_at_each_freq)
        worst_freq = frequency[freq_mask][worst_freq_idx]
        
        pass_status = worst_diff < self.max_gain_difference_db
        
        return {
            'all_pass': pass_status,
            'worst_difference_db': worst_diff,
            'worst_frequency_hz': worst_freq,
            'threshold_db': self.max_gain_difference_db,
            'check_name': 'Max Gain Difference'
        }
    
    def check_max_phase_difference(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Check maximum phase difference between branches at each frequency point.
        
        Returns dictionary with pass/fail status and worst-case difference.
        """
        # Filter frequency range if specified
        if x_min is not None and x_max is not None:
            freq_mask = (frequency >= x_min) & (frequency <= x_max)
        else:
            freq_mask = np.ones(len(frequency), dtype=bool)
        
        # Collect all branch phases
        branch_phases = []
        branch_keys = []
        
        for i in range(2, 11):
            s_key = f'S{i}1'
            if s_key in s_params:
                sxy_phase = np.angle(s_params[s_key]) * 180 / np.pi  # Convert to degrees
                branch_phases.append(sxy_phase[freq_mask])
                branch_keys.append(s_key)
        
        if len(branch_phases) < 2:
            return {
                'all_pass': True,
                'results': {'error': 'Insufficient branches for comparison'},
                'check_name': 'Max Phase Difference'
            }
        
        # Stack into array: [n_branches, n_frequencies]
        branch_phases_array = np.array(branch_phases)
        
        # Calculate max difference at each frequency point
        max_vals = np.max(branch_phases_array, axis=0)
        min_vals = np.min(branch_phases_array, axis=0)
        diff_at_each_freq = max_vals - min_vals
        
        # Find worst-case difference
        worst_diff = np.max(diff_at_each_freq)
        worst_freq_idx = np.argmax(diff_at_each_freq)
        worst_freq = frequency[freq_mask][worst_freq_idx]
        
        pass_status = worst_diff < self.max_phase_difference_degrees
        
        return {
            'all_pass': pass_status,
            'worst_difference_degrees': worst_diff,
            'worst_frequency_hz': worst_freq,
            'threshold_degrees': self.max_phase_difference_degrees,
            'check_name': 'Max Phase Difference'
        }
    
    def check_all(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Perform all compliance checks.
        
        Returns dictionary with all check results.
        """
        return_loss = self.check_return_loss(frequency, s_params, x_min, x_max)
        gain_flatness = self.check_gain_flatness(frequency, s_params, x_min, x_max)
        max_gain_diff = self.check_max_gain_difference(frequency, s_params, x_min, x_max)
        max_phase_diff = self.check_max_phase_difference(frequency, s_params, x_min, x_max)
        
        overall_pass = (
            return_loss['all_pass'] and
            gain_flatness['all_pass'] and
            max_gain_diff['all_pass'] and
            max_phase_diff['all_pass']
        )
        
        return {
            'overall_pass': overall_pass,
            'return_loss': return_loss,
            'gain_flatness': gain_flatness,
            'max_gain_difference': max_gain_diff,
            'max_phase_difference': max_phase_diff
        }

