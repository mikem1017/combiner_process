"""
Backend Processor for RF Combiner Analysis

Handles all data processing, leaving GUI to only display results.
"""

from typing import Dict, Optional, List, Tuple
import numpy as np
from pathlib import Path

from s2p_parser import S2PParser
from plotter import Plotter
from compliance import ComplianceChecker


class BackendProcessor:
    """Handles all backend processing for RF combiner analysis."""
    
    def __init__(self, config_path: str = "compliance_config.json"):
        """Initialize backend processor with all necessary components."""
        self.parser = S2PParser()
        self.plotter = Plotter()
        self.compliance_checker = ComplianceChecker(config_path)
        
        # Processed data
        self.frequency = None
        self.s_params = None
        self.metadata = None
        self.compliance_results = None
        
        # Default frequency range (Hz)
        self.default_x_min = 2.5e9
        self.default_x_max = 4.3e9
    
    def process_files(self, filepaths: List[str]) -> Dict:
        """
        Process S2P files and extract all data.
        
        Args:
            filepaths: List of 9 S2P file paths
            
        Returns:
            Dictionary with:
                - success: bool
                - error: str (if success is False)
                - metadata: dict (if success is True)
                - file_list: list of filenames (if success is True)
        """
        try:
            # Process files using parser
            data = self.parser.process_files(filepaths)
            
            # Store processed data
            self.frequency = data['frequency']
            self.s_params = data['s_params']
            self.metadata = data['metadata']
            
            # Get file list for display
            file_list = [Path(f).name for f in filepaths]
            
            # Format metadata for display
            metadata_display = self._format_metadata(self.metadata)
            
            return {
                'success': True,
                'metadata': metadata_display,
                'file_list': file_list
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_metadata(self, metadata: Dict) -> str:
        """Format metadata for display, handling missing fields gracefully."""
        if metadata is None:
            return "No metadata available"
        
        try:
            date = metadata.get('date', 'N/A')
            serial = metadata.get('serial_number', 'N/A')
            env = metadata.get('environment', 'N/A')
            return f"Date: {date} | SN: {serial} | Env: {env}"
        except Exception:
            return "Metadata parsing error"
    
    def get_plot_data(
        self,
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Get data needed for plotting.
        
        Args:
            x_min: Minimum frequency in Hz (default: 2.5 GHz)
            x_max: Maximum frequency in Hz (default: 4.3 GHz)
            
        Returns:
            Dictionary with:
                - success: bool
                - error: str (if success is False)
                - frequency: array (if success is True)
                - s_params: dict (if success is True)
                - x_min: float
                - x_max: float
        """
        if self.frequency is None or self.s_params is None:
            return {
                'success': False,
                'error': 'No data loaded. Please load files first.'
            }
        
        try:
            # Use provided limits or defaults
            if x_min is None:
                x_min = self.default_x_min
            if x_max is None:
                x_max = self.default_x_max
            
            # Validate frequency range
            freq_min = np.min(self.frequency)
            freq_max = np.max(self.frequency)
            
            if x_min < freq_min:
                x_min = freq_min
            if x_max > freq_max:
                x_max = freq_max
            if x_min >= x_max:
                return {
                    'success': False,
                    'error': f'Invalid frequency range: {x_min/1e9:.2f} - {x_max/1e9:.2f} GHz'
                }
            
            return {
                'success': True,
                'frequency': self.frequency,
                's_params': self.s_params,
                'x_min': x_min,
                'x_max': x_max
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error preparing plot data: {str(e)}'
            }
    
    def generate_plots(
        self,
        axes: List,
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Generate all plots on provided axes.
        
        Args:
            axes: List of 4 matplotlib axes objects
            x_min: Minimum frequency in Hz
            x_max: Maximum frequency in Hz
            
        Returns:
            Dictionary with success status and error message if failed
        """
        plot_data = self.get_plot_data(x_min, x_max)
        
        if not plot_data['success']:
            return plot_data
        
        try:
            frequency = plot_data['frequency']
            s_params = plot_data['s_params']
            x_min = plot_data['x_min']
            x_max = plot_data['x_max']
            
            # Clear all axes
            for ax in axes:
                ax.clear()
            
            # Generate all 4 plots
            self.plotter.plot_sxx_return_loss(
                frequency, s_params, x_min, x_max, ax=axes[0]
            )
            
            self.plotter.plot_sxy_thru_paths(
                frequency, s_params, x_min, x_max, ax=axes[1]
            )
            
            self.plotter.plot_branch_to_branch_magnitude(
                frequency, s_params, x_min, x_max, ax=axes[2]
            )
            
            self.plotter.plot_branch_to_branch_phase(
                frequency, s_params, x_min, x_max, ax=axes[3]
            )
            
            return {'success': True}
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating plots: {str(e)}'
            }
    
    def run_compliance_checks(
        self,
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> Dict:
        """
        Run all compliance checks.
        
        Args:
            x_min: Minimum frequency in Hz
            x_max: Maximum frequency in Hz
            
        Returns:
            Dictionary with:
                - success: bool
                - error: str (if success is False)
                - results: compliance results dict (if success is True)
        """
        if self.frequency is None or self.s_params is None:
            return {
                'success': False,
                'error': 'No data loaded. Please load files first.'
            }
        
        try:
            # Use provided limits or defaults
            if x_min is None:
                x_min = self.default_x_min
            if x_max is None:
                x_max = self.default_x_max
            
            # Run compliance checks
            self.compliance_results = self.compliance_checker.check_all(
                self.frequency,
                self.s_params,
                x_min,
                x_max
            )
            
            return {
                'success': True,
                'results': self.compliance_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error running compliance checks: {str(e)}'
            }
    
    def format_compliance_for_copy(self) -> str:
        """
        Format compliance results as text for clipboard copy.
        
        Returns:
            Formatted text string
        """
        if self.compliance_results is None:
            return "No compliance results available"
        
        lines = []
        lines.append("Compliance Results")
        lines.append("=" * 60)
        lines.append("")
        
        # Return Loss
        rl = self.compliance_results['return_loss']
        lines.append(f"Return Loss: {'PASS' if rl['all_pass'] else 'FAIL'}")
        for port, result in rl['results'].items():
            status = "PASS" if result['pass'] else "FAIL"
            lines.append(f"  {port}: {status} - Worst: {result['worst_value_db']:.2f} dB")
        
        # Gain Flatness
        gf = self.compliance_results['gain_flatness']
        lines.append(f"\nGain Flatness: {'PASS' if gf['all_pass'] else 'FAIL'}")
        for branch, result in gf['results'].items():
            status = "PASS" if result['pass'] else "FAIL"
            lines.append(f"  {branch}: {status} - P2P: {result['p2p_variation_db']:.3f} dB")
        
        # Max Gain Difference
        max_gain = self.compliance_results['max_gain_difference']
        lines.append(f"\nMax Gain Difference: {'PASS' if max_gain['all_pass'] else 'FAIL'}")
        lines.append(f"  Worst: {max_gain['worst_difference_db']:.3f} dB")
        
        # Max Phase Difference
        max_phase = self.compliance_results['max_phase_difference']
        lines.append(f"\nMax Phase Difference: {'PASS' if max_phase['all_pass'] else 'FAIL'}")
        lines.append(f"  Worst: {max_phase['worst_difference_degrees']:.2f}°")
        
        return "\n".join(lines)
    
    def format_compliance_for_image(self) -> str:
        """
        Format compliance results as text for image generation.
        
        Returns:
            Formatted text string
        """
        if self.compliance_results is None:
            return "No compliance results available"
        
        text_content = []
        text_content.append("RF Combiner Compliance Results\n")
        text_content.append("=" * 60 + "\n\n")
        
        rl = self.compliance_results['return_loss']
        text_content.append(f"Return Loss: {'✓ PASS' if rl['all_pass'] else '✗ FAIL'}\n")
        for port, result in rl['results'].items():
            status = "✓" if result['pass'] else "✗"
            text_content.append(f"  {port}: {status} {result['worst_value_db']:.2f} dB\n")
        
        gf = self.compliance_results['gain_flatness']
        text_content.append(f"\nGain Flatness: {'✓ PASS' if gf['all_pass'] else '✗ FAIL'}\n")
        for branch, result in gf['results'].items():
            status = "✓" if result['pass'] else "✗"
            text_content.append(f"  {branch}: {status} {result['p2p_variation_db']:.3f} dB\n")
        
        max_gain = self.compliance_results['max_gain_difference']
        status = "✓" if max_gain['all_pass'] else "✗"
        text_content.append(f"\nMax Gain Difference: {status} {max_gain['worst_difference_db']:.3f} dB\n")
        
        max_phase = self.compliance_results['max_phase_difference']
        status = "✓" if max_phase['all_pass'] else "✗"
        text_content.append(f"Max Phase Difference: {status} {max_phase['worst_difference_degrees']:.2f}°\n")
        
        return "".join(text_content)

