# RF Combiner Analysis Application

Desktop GUI application for analyzing 9-way RF combiner S2P files, generating plots, and checking compliance against configurable thresholds.

## Features

- **Multi-file Selection**: Select all 9 S2P files at once
- **Filename Parsing**: Automatically extracts metadata (date, serial number, port path) from filenames
- **4 Plots**:
  1. Return Loss (Sxx) for all 10 ports
  2. Thru Paths (Sxy) from input to each output
  3. Branch-to-Branch Magnitude (relative to S21)
  4. Branch-to-Branch Phase (relative to S21)
- **Compliance Checking**: 
  - Return Loss < -14dB
  - Gain Flatness < 0.8dBpp (per branch)
  - Max Gain Difference < 0.5dB (between branches)
  - Max Phase Difference < 10 degrees (between branches)
- **Adjustable Axis Limits**: Default X-axis 2.5-4.3 GHz, customizable
- **Compliance Table**: Copy/paste and save as image

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Click "Select S2P Files (9 files)" and select all 9 files at once

3. The application will:
   - Parse filenames to identify port paths
   - Extract S-parameters from each file
   - Generate all 4 plots
   - Run compliance checks

4. Adjust frequency range using X-axis controls and click "Update Plots"

5. View compliance results in the table on the right
   - Copy results to clipboard
   - Save results as image

## Filename Format

Files must follow this naming convention:
```
YYYYMMDD_COMBINER_SNXXXX_Path_01_02_AMB.S2P
```

Where:
- `YYYYMMDD`: Date (e.g., 20241201)
- `SNXXXX`: Serial number (e.g., SN1234)
- `Path_01_02`: Port path (01 = input, 02-10 = outputs)
- `AMB`: Environment identifier

Expected port paths:
- `Path_01_02` (S21 file)
- `Path_01_03` (S31 file)
- `Path_01_04` (S41 file)
- ...
- `Path_01_10` (S10_1 file)

## Configuration

Edit `compliance_config.json` to adjust compliance thresholds:

```json
{
  "return_loss_threshold_db": -14,
  "gain_flatness_threshold_db": 0.8,
  "max_gain_difference_db": 0.5,
  "max_phase_difference_degrees": 10
}
```

## File Structure

- `main.py`: Main GUI application
- `s2p_parser.py`: S2P file parsing and filename parsing
- `plotter.py`: Plot generation
- `compliance.py`: Compliance checking
- `compliance_config.json`: Threshold configuration

## Dependencies

- `skrf`: S-parameter file parsing
- `matplotlib`: Plotting
- `numpy`: Numerical calculations
- `tkinter`: GUI framework (built-in with Python)

