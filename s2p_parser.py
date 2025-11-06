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
    
    # No longer using fixed expected paths - will sort by path number instead
    
    def __init__(self):
        self.files_data = {}
        self.metadata = {}
        
    def parse_filename(self, filepath: str) -> Dict[str, str]:
        """
        Parse filename format: YYYYMMDDTTTTTT_PMA_Combiner_SNXXXX_SM_Path_01_NN.s2p
        
        Returns:
            Dictionary with keys: date, serial_number, port_path, path_number, filename
        """
        filename = os.path.basename(filepath)
        
        # Pattern: YYYYMMDDTTTTTT_PMA_Combiner_SNXXXX_SM_Path_01_NN.s2p (case-insensitive)
        pattern = r'(\d{8})\d{6}_PMA_Combiner_(SN\d+)_SM_(Path_\d{2}_\d{2})\.s2p'
        match = re.match(pattern, filename, re.IGNORECASE)
        
        if not match:
            raise ValueError(f"Filename format not recognized: {filename}")
        
        date, serial_number, port_path = match.groups()
        
        # Extract path number (NN) from Path_01_NN
        path_match = re.match(r'Path_\d{2}_(\d{2})', port_path)
        if path_match:
            path_number = int(path_match.group(1))
        else:
            raise ValueError(f"Could not extract path number from: {port_path}")
        
        return {
            'date': date,
            'serial_number': serial_number,
            'port_path': port_path,
            'path_number': path_number,
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
        
        # Parse all filenames and extract path numbers
        file_data = []
        for filepath in filepaths:
            try:
                metadata = self.parse_filename(filepath)
            except ValueError as e:
                filename = os.path.basename(filepath)
                raise ValueError(f"Failed to parse filename '{filename}': {str(e)}")
            
            file_data.append({
                'filepath': filepath,
                'metadata': metadata,
                'path_number': metadata['path_number'],
                'port_path': metadata['port_path']
            })
        
        # Check we have exactly 9 files
        if len(file_data) != 9:
            raise ValueError(f"Expected 9 files, got {len(file_data)}")
        
        # Sort by path number (lowest path number = S21 reference)
        file_data.sort(key=lambda x: x['path_number'])
        
        # Check for duplicate path numbers
        path_numbers = [f['path_number'] for f in file_data]
        if len(set(path_numbers)) != len(path_numbers):
            raise ValueError(f"Duplicate path numbers found: {path_numbers}")
        
        # Load S2P files and extract S-parameters
        s_params = {}
        frequency = None
        all_metadata = {}
        path_labels = {}  # Map S-parameter keys to path labels for legends
        
        # Load first file (lowest path number) to get S11, S21, S22 and frequency
        first_file = file_data[0]
        first_net = self.load_s2p_file(first_file['filepath'])
        frequency = first_net.f  # Frequency in Hz
        
        # Extract S11, S21, S22 from first file (this is the reference path)
        s_params['S11'] = first_net.s[:, 0, 0]  # S11
        s_params['S21'] = first_net.s[:, 1, 0]  # S21
        s_params['S22'] = first_net.s[:, 1, 1]  # S22
        
        # Store path label for S21 (reference)
        path_labels['S21'] = first_file['port_path'].replace('_', ' ')
        all_metadata[first_file['port_path']] = first_file['metadata']
        
        # Load remaining files (sorted by path number)
        # Map them to S31, S33, S41, S44, etc.
        for idx, file_info in enumerate(file_data[1:], start=3):
            net = self.load_s2p_file(file_info['filepath'])
            
            # Verify frequency matches
            if not np.allclose(net.f, frequency):
                raise ValueError(f"Frequency mismatch in {file_info['port_path']} file")
            
            # Extract S-parameters: S(x1) and S(xx)
            # S(x1) is the forward transmission from port 1 to port x
            # S(xx) is the return loss at port x
            # In S2P file: port 0 = input (port 1), port 1 = output (port x)
            # S(x1) = transmission from port 0 to port 1 in file = s[:, 1, 0]
            # S(xx) = reflection at port 1 in file = s[:, 1, 1]
            s_params[f'S{idx}1'] = net.s[:, 1, 0]  # S(x1) where x = idx
            s_params[f'S{idx}{idx}'] = net.s[:, 1, 1]  # S(xx)
            
            # Store path label for this S-parameter
            path_labels[f'S{idx}1'] = file_info['port_path'].replace('_', ' ')
            path_labels[f'S{idx}{idx}'] = file_info['port_path'].replace('_', ' ')
            all_metadata[file_info['port_path']] = file_info['metadata']
        
        # Store metadata (use first file's metadata for common fields)
        first_file_metadata = file_data[0]['metadata']
        
        result_metadata = {
            'date': first_file_metadata.get('date', 'Unknown'),
            'serial_number': first_file_metadata.get('serial_number', 'Unknown'),
            'all_paths': all_metadata
        }
        
        return {
            'frequency': frequency,
            's_params': s_params,
            'metadata': result_metadata,
            'path_labels': path_labels  # Map S-parameter keys to path labels
        }

