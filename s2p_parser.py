"""
S2P File Parser for RF Combiner Analysis

Parses Touchstone S2P files and extracts S-parameters along with metadata
from filenames in the format: YYYYMMDD_COMBINER_SNXXXX_Path_01_02_AMB.S2P
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import skrf as rf


class S2PParser:
    """Parser for S2P files with filename metadata extraction."""
    
    # Expected port paths: Path_01_02 through Path_01_10
    EXPECTED_PATHS = [f"Path_01_{i:02d}" for i in range(2, 11)]
    
    def __init__(self):
        self.files_data = {}
        self.metadata = {}
        
    def parse_filename(self, filepath: str) -> Dict[str, str]:
        """
        Parse filename format: YYYYMMDD_COMBINER_SNXXXX_Path_01_02_AMB.S2P
        
        Returns:
            Dictionary with keys: date, serial_number, port_path, environment, filename
        """
        filename = os.path.basename(filepath)
        
        # Pattern: YYYYMMDD_COMBINER_SNXXXX_Path_01_02_AMB.S2P (case-insensitive)
        # Allow both uppercase and lowercase for environment and extension
        pattern = r'(\d{8})_COMBINER_(SN\d+)_(Path_\d{2}_\d{2})_([A-Za-z]+)\.s2p'
        match = re.match(pattern, filename, re.IGNORECASE)
        
        if not match:
            raise ValueError(f"Filename format not recognized: {filename}")
        
        date, serial_number, port_path, environment = match.groups()
        
        return {
            'date': date,
            'serial_number': serial_number,
            'port_path': port_path,
            'environment': environment,
            'filename': filename
        }
    
    def port_path_to_s_params(self, port_path: str) -> Tuple[int, int]:
        """
        Convert port path (e.g., 'Path_01_02') to port numbers.
        
        Returns:
            Tuple of (port1, port2) where port1 is input, port2 is output
        """
        match = re.match(r'Path_(\d{2})_(\d{2})', port_path)
        if not match:
            raise ValueError(f"Invalid port path format: {port_path}")
        
        port1, port2 = int(match.group(1)), int(match.group(2))
        return port1, port2
    
    def load_s2p_file(self, filepath: str) -> rf.Network:
        """Load S2P file using skrf."""
        try:
            return rf.Network(filepath)
        except Exception as e:
            raise ValueError(f"Error loading S2P file {filepath}: {str(e)}")
    
    def process_files(self, filepaths: List[str]) -> Dict:
        """
        Process multiple S2P files and extract all S-parameters.
        
        Args:
            filepaths: List of paths to S2P files
            
        Returns:
            Dictionary containing:
                - frequency: numpy array of frequencies (Hz)
                - s_params: Dictionary of S-parameters (S11, S21, S22, S31, S33, etc.)
                - metadata: Dictionary of metadata from filenames
        """
        if len(filepaths) != 9:
            raise ValueError(f"Expected 9 files, got {len(filepaths)}")
        
        # Parse all filenames and organize by port path
        file_data = {}
        for filepath in filepaths:
            try:
                metadata = self.parse_filename(filepath)
            except ValueError as e:
                # If filename parsing fails, try to extract what we can
                filename = os.path.basename(filepath)
                raise ValueError(f"Failed to parse filename '{filename}': {str(e)}")
            
            port_path = metadata['port_path']
            
            if port_path not in self.EXPECTED_PATHS:
                raise ValueError(f"Unexpected port path: {port_path}. Expected one of {self.EXPECTED_PATHS}")
            
            if port_path in file_data:
                raise ValueError(f"Duplicate port path found: {port_path}")
            
            file_data[port_path] = {
                'filepath': filepath,
                'metadata': metadata
            }
        
        # Check we have all 9 expected paths
        found_paths = set(file_data.keys())
        expected_paths = set(self.EXPECTED_PATHS)
        if found_paths != expected_paths:
            missing = expected_paths - found_paths
            raise ValueError(f"Missing port paths: {missing}")
        
        # Load S2P files and extract S-parameters
        s_params = {}
        frequency = None
        all_metadata = {}
        
        # Load S21 file first (Path_01_02) to get S11, S21, S22 and frequency
        s21_path = file_data['Path_01_02']['filepath']
        s21_net = self.load_s2p_file(s21_path)
        frequency = s21_net.f  # Frequency in Hz
        
        # Extract S11, S21, S22 from first file
        s_params['S11'] = s21_net.s[:, 0, 0]  # S11
        s_params['S21'] = s21_net.s[:, 1, 0]  # S21
        s_params['S22'] = s21_net.s[:, 1, 1]  # S22
        
        all_metadata['Path_01_02'] = file_data['Path_01_02']['metadata']
        
        # Load remaining files (Path_01_03 through Path_01_10)
        for i in range(3, 11):
            port_path = f"Path_01_{i:02d}"
            filepath = file_data[port_path]['filepath']
            net = self.load_s2p_file(filepath)
            
            # Verify frequency matches
            if not np.allclose(net.f, frequency):
                raise ValueError(f"Frequency mismatch in {port_path} file")
            
            # Extract S-parameters: S(x1) and S(xx)
            # S(x1) is the forward transmission from port 1 to port x
            # S(xx) is the return loss at port x
            # In S2P file: port 0 = input (port 1), port 1 = output (port x)
            # S(x1) = transmission from port 0 to port 1 in file = s[:, 1, 0]
            # S(xx) = reflection at port 1 in file = s[:, 1, 1]
            s_params[f'S{i}1'] = net.s[:, 1, 0]  # S(x1) where x = i
            s_params[f'S{i}{i}'] = net.s[:, 1, 1]  # S(xx)
            
            all_metadata[port_path] = file_data[port_path]['metadata']
        
        # Store metadata (use first file's metadata for common fields)
        # all_metadata[port_path] is already the metadata dict
        first_metadata = all_metadata.get('Path_01_02', {})
        
        result_metadata = {
            'date': first_metadata.get('date', 'Unknown'),
            'serial_number': first_metadata.get('serial_number', 'Unknown'),
            'environment': first_metadata.get('environment', 'Unknown'),
            'all_paths': all_metadata
        }
        
        return {
            'frequency': frequency,
            's_params': s_params,
            'metadata': result_metadata
        }

