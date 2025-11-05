"""
Plot Generator for RF Combiner Analysis

Generates 4 plots:
1. Sxx (Return Loss) for all ports
2. Sxy (Thru Paths) from input to each output
3. Branch-to-Branch Magnitude (relative to S21)
4. Branch-to-Branch Phase (relative to S21)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Dict, Optional, Tuple


class Plotter:
    """Generates plots for RF combiner analysis."""
    
    def __init__(self, default_x_min: float = 2.5e9, default_x_max: float = 4.3e9):
        """
        Initialize plotter with default frequency range.
        
        Args:
            default_x_min: Default minimum frequency in Hz (2.5 GHz)
            default_x_max: Default maximum frequency in Hz (4.3 GHz)
        """
        self.default_x_min = default_x_min
        self.default_x_max = default_x_max
    
    def _convert_to_ghz(self, freq_hz: np.ndarray) -> np.ndarray:
        """Convert frequency from Hz to GHz."""
        return freq_hz / 1e9
    
    def _magnitude_db(self, s_param: np.ndarray) -> np.ndarray:
        """Convert S-parameter to magnitude in dB."""
        return 20 * np.log10(np.abs(s_param))
    
    def _phase_degrees(self, s_param: np.ndarray) -> np.ndarray:
        """Convert S-parameter to phase in degrees."""
        return np.angle(s_param) * 180 / np.pi
    
    def plot_sxx_return_loss(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None,
        ax: Optional[plt.Axes] = None
    ) -> Tuple[Figure, plt.Axes]:
        """
        Plot Sxx (Return Loss) for all ports.
        
        Plots S11, S22, S33, ..., S1010 vs frequency.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        freq_ghz = self._convert_to_ghz(frequency)
        
        # Plot S11 (input port)
        if 'S11' in s_params:
            s11_db = self._magnitude_db(s_params['S11'])
            ax.plot(freq_ghz, s11_db, label='S11', linewidth=2)
        
        # Plot S22 through S1010 (output ports)
        for i in range(2, 11):
            s_key = f'S{i}{i}'
            if s_key in s_params:
                sxx_db = self._magnitude_db(s_params[s_key])
                ax.plot(freq_ghz, sxx_db, label=s_key, linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('Frequency (GHz)', fontsize=12)
        ax.set_ylabel('Return Loss (dB)', fontsize=12)
        ax.set_title('Return Loss (Sxx)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9, ncol=2)
        
        # Set x-axis limits
        if x_min is not None and x_max is not None:
            ax.set_xlim(x_min / 1e9, x_max / 1e9)
        else:
            ax.set_xlim(self.default_x_min / 1e9, self.default_x_max / 1e9)
        
        plt.tight_layout()
        return fig, ax
    
    def plot_sxy_thru_paths(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None,
        ax: Optional[plt.Axes] = None
    ) -> Tuple[Figure, plt.Axes]:
        """
        Plot Sxy (Thru Paths) from input to each output.
        
        Plots S21, S31, S41, ..., S10_1 vs frequency.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        freq_ghz = self._convert_to_ghz(frequency)
        
        # Plot all thru paths
        for i in range(2, 11):
            s_key = f'S{i}1'
            if s_key in s_params:
                sxy_db = self._magnitude_db(s_params[s_key])
                ax.plot(freq_ghz, sxy_db, label=s_key, linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('Frequency (GHz)', fontsize=12)
        ax.set_ylabel('Insertion Loss / Gain (dB)', fontsize=12)
        ax.set_title('Thru Paths (Sxy)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9, ncol=2)
        
        # Set x-axis limits
        if x_min is not None and x_max is not None:
            ax.set_xlim(x_min / 1e9, x_max / 1e9)
        else:
            ax.set_xlim(self.default_x_min / 1e9, self.default_x_max / 1e9)
        
        plt.tight_layout()
        return fig, ax
    
    def plot_branch_to_branch_magnitude(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None,
        ax: Optional[plt.Axes] = None
    ) -> Tuple[Figure, plt.Axes]:
        """
        Plot Branch-to-Branch Magnitude relative to S21.
        
        Calculates: 20*log10(|S(x1)| / |S21|) for x = 3, 4, ..., 10
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        if 'S21' not in s_params:
            raise ValueError("S21 not found in S-parameters")
        
        freq_ghz = self._convert_to_ghz(frequency)
        s21_mag = np.abs(s_params['S21'])
        
        # Calculate relative magnitude for each branch
        for i in range(3, 11):
            s_key = f'S{i}1'
            if s_key in s_params:
                sxy_mag = np.abs(s_params[s_key])
                # dB(S(xy)/S(21)) = 20*log10(|S(x1)| / |S21|)
                relative_mag_db = 20 * np.log10(sxy_mag / s21_mag)
                ax.plot(freq_ghz, relative_mag_db, label=s_key, linewidth=1.5, alpha=0.8)
        
        ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.5, label='Reference (S21)')
        ax.set_xlabel('Frequency (GHz)', fontsize=12)
        ax.set_ylabel('Relative Magnitude (dB)', fontsize=12)
        ax.set_title('Branch-to-Branch Magnitude (Relative to S21)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9, ncol=2)
        
        # Set x-axis limits
        if x_min is not None and x_max is not None:
            ax.set_xlim(x_min / 1e9, x_max / 1e9)
        else:
            ax.set_xlim(self.default_x_min / 1e9, self.default_x_max / 1e9)
        
        # Set y-axis limits to -0.5 to 0.5 dB
        ax.set_ylim(-0.5, 0.5)
        
        plt.tight_layout()
        return fig, ax
    
    def plot_branch_to_branch_phase(
        self,
        frequency: np.ndarray,
        s_params: Dict[str, np.ndarray],
        x_min: Optional[float] = None,
        x_max: Optional[float] = None,
        ax: Optional[plt.Axes] = None
    ) -> Tuple[Figure, plt.Axes]:
        """
        Plot Branch-to-Branch Phase relative to S21.
        
        Calculates: phase(S(x1)) - phase(S21) for x = 3, 4, ..., 10
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        if 'S21' not in s_params:
            raise ValueError("S21 not found in S-parameters")
        
        freq_ghz = self._convert_to_ghz(frequency)
        s21_phase = np.angle(s_params['S21'])
        
        # Calculate relative phase for each branch
        for i in range(3, 11):
            s_key = f'S{i}1'
            if s_key in s_params:
                sxy_phase = np.angle(s_params[s_key])
                # phase(S(xy)/S(21)) = phase(S(x1)) - phase(S21)
                relative_phase_deg = (sxy_phase - s21_phase) * 180 / np.pi
                ax.plot(freq_ghz, relative_phase_deg, label=s_key, linewidth=1.5, alpha=0.8)
        
        ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.5, label='Reference (S21)')
        ax.set_xlabel('Frequency (GHz)', fontsize=12)
        ax.set_ylabel('Relative Phase (degrees)', fontsize=12)
        ax.set_title('Branch-to-Branch Phase (Relative to S21)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9, ncol=2)
        
        # Set x-axis limits
        if x_min is not None and x_max is not None:
            ax.set_xlim(x_min / 1e9, x_max / 1e9)
        else:
            ax.set_xlim(self.default_x_min / 1e9, self.default_x_max / 1e9)
        
        # Set y-axis limits to -5 to +5 degrees
        ax.set_ylim(-5, 5)
        
        plt.tight_layout()
        return fig, ax

