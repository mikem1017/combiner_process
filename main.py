"""
Main GUI Application for RF Combiner Analysis

Desktop application using PyQt5 for displaying RF combiner analysis results.
All processing is done in the backend_processor module.
Main window with compliance table, 4 separate plot windows.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem,
                             QFrame, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from backend_processor import BackendProcessor


class PlotWindow(QDialog):
    """Individual window for a single plot."""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 6))
        self.ax = self.fig.add_subplot(111)
        
        # Canvas for matplotlib
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        # Navigation toolbar
        toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(toolbar)
    
    def clear(self):
        """Clear the plot."""
        self.ax.clear()
        self.canvas.draw()


class RFCombinerApp(QMainWindow):
    """Main application class for RF Combiner analysis - GUI only, no processing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RF Combiner Analysis")
        self.setGeometry(100, 100, 1400, 700)
        
        # Initialize backend processor (handles all processing)
        self.processor = BackendProcessor()
        
        # Plot windows
        self.plot_windows = {}
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top frame for file selection and metadata
        top_frame = QFrame()
        top_layout = QHBoxLayout(top_frame)
        
        # File selection button
        self.select_files_btn = QPushButton("Select S2P Files (9 files)")
        self.select_files_btn.clicked.connect(self.select_files)
        top_layout.addWidget(self.select_files_btn)
        
        # Metadata display
        self.metadata_label = QLabel("No files loaded")
        top_layout.addWidget(self.metadata_label)
        
        # File list
        self.file_list_label = QLabel("")
        self.file_list_label.setWordWrap(True)
        top_layout.addWidget(self.file_list_label)
        
        top_layout.addStretch()
        main_layout.addWidget(top_frame)
        
        # Axis controls frame
        axis_frame = QFrame()
        axis_layout = QHBoxLayout(axis_frame)
        
        axis_layout.addWidget(QLabel("X-axis (GHz):"))
        axis_layout.addWidget(QLabel("Min:"))
        self.x_min_edit = QLineEdit("2.5")
        self.x_min_edit.setMaximumWidth(80)
        axis_layout.addWidget(self.x_min_edit)
        
        axis_layout.addWidget(QLabel("Max:"))
        self.x_max_edit = QLineEdit("4.3")
        self.x_max_edit.setMaximumWidth(80)
        axis_layout.addWidget(self.x_max_edit)
        
        self.update_plots_btn = QPushButton("Update Plots")
        self.update_plots_btn.clicked.connect(self.update_plots)
        axis_layout.addWidget(self.update_plots_btn)
        
        axis_layout.addStretch()
        main_layout.addWidget(axis_frame)
        
        # Compliance table section at bottom
        compliance_label = QLabel("Compliance Results")
        compliance_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        main_layout.addWidget(compliance_label)
        
        # Compliance table
        self.compliance_tree = QTreeWidget()
        self.compliance_tree.setHeaderLabels(["Check", "Status", "Value", "Threshold"])
        self.compliance_tree.setColumnWidth(0, 200)
        self.compliance_tree.setColumnWidth(1, 80)
        self.compliance_tree.setColumnWidth(2, 120)
        self.compliance_tree.setColumnWidth(3, 100)
        main_layout.addWidget(self.compliance_tree)
        
        # Compliance table buttons
        compliance_btn_layout = QHBoxLayout()
        
        copy_btn = QPushButton("Copy Table")
        copy_btn.clicked.connect(self.copy_compliance_table)
        compliance_btn_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("Save as Image")
        save_btn.clicked.connect(self.save_compliance_image)
        compliance_btn_layout.addWidget(save_btn)
        
        compliance_btn_layout.addStretch()
        main_layout.addLayout(compliance_btn_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_plot_windows(self):
        """Create 4 separate plot windows."""
        plot_titles = [
            "Return Loss (Sxx)",
            "Thru Paths (Sxy)",
            "Branch-to-Branch Magnitude",
            "Branch-to-Branch Phase"
        ]
        
        # Position windows in a grid
        positions = [
            (100, 100),    # Top-left
            (950, 100),    # Top-right
            (100, 750),    # Bottom-left
            (950, 750)     # Bottom-right
        ]
        
        for i, title in enumerate(plot_titles):
            if title not in self.plot_windows:
                window = PlotWindow(title, self)
                x, y = positions[i]
                window.setGeometry(x, y, 800, 600)
                self.plot_windows[title] = window
                window.show()
    
    def select_files(self):
        """Open file dialog to select 9 S2P files."""
        filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select 9 S2P Files",
            "",
            "S2P files (*.s2p);;All files (*.*)"
        )
        
        if not filepaths:
            return
        
        if len(filepaths) != 9:
            QMessageBox.critical(
                self,
                "Error",
                f"Please select exactly 9 files. You selected {len(filepaths)} files."
            )
            return
        
        try:
            self.statusBar().showMessage("Loading files...")
            QApplication.processEvents()
            
            # Process files using backend (all processing happens here)
            result = self.processor.process_files(list(filepaths))
            
            if not result['success']:
                QMessageBox.critical(self, "Error", f"Error processing files: {result['error']}")
                self.statusBar().showMessage(f"Error: {result['error']}")
                return
            
            # Display results (GUI only displays, no processing)
            self.metadata_label.setText(result['metadata'])
            
            # Display file list
            file_list = result['file_list'][:3]
            file_list_text = "\n".join([f"- {f}" for f in file_list])
            if len(result['file_list']) > 3:
                file_list_text += f"\n... and {len(result['file_list']) - 3} more"
            self.file_list_label.setText(f"Files:\n{file_list_text}")
            
            # Create plot windows
            self.create_plot_windows()
            
            # Generate plots using backend
            self.update_plots()
            
            # Run compliance checks using backend
            self.run_compliance_checks()
            
            self.statusBar().showMessage("Files loaded successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
            self.statusBar().showMessage(f"Error: {str(e)}")
    
    def update_plots(self):
        """Update all plots - calls backend processor."""
        if not self.plot_windows:
            return
        
        try:
            # Get axis limits from GUI
            x_min = float(self.x_min_edit.text()) * 1e9  # Convert GHz to Hz
            x_max = float(self.x_max_edit.text()) * 1e9
            
            # Get plot data
            plot_data = self.processor.get_plot_data(x_min, x_max)
            
            if not plot_data['success']:
                QMessageBox.critical(self, "Error", plot_data['error'])
                return
            
            frequency = plot_data['frequency']
            s_params = plot_data['s_params']
            x_min = plot_data['x_min']
            x_max = plot_data['x_max']
            
            # Plot 1: Sxx Return Loss
            if "Return Loss (Sxx)" in self.plot_windows:
                window = self.plot_windows["Return Loss (Sxx)"]
                window.ax.clear()
                self.processor.plotter.plot_sxx_return_loss(
                    frequency, s_params, x_min, x_max, ax=window.ax, path_labels=self.processor.path_labels
                )
                window.canvas.draw()
            
            # Plot 2: Sxy Thru Paths
            if "Thru Paths (Sxy)" in self.plot_windows:
                window = self.plot_windows["Thru Paths (Sxy)"]
                window.ax.clear()
                self.processor.plotter.plot_sxy_thru_paths(
                    frequency, s_params, x_min, x_max, ax=window.ax, path_labels=self.processor.path_labels
                )
                window.canvas.draw()
            
            # Plot 3: Branch-to-Branch Magnitude
            if "Branch-to-Branch Magnitude" in self.plot_windows:
                window = self.plot_windows["Branch-to-Branch Magnitude"]
                window.ax.clear()
                self.processor.plotter.plot_branch_to_branch_magnitude(
                    frequency, s_params, x_min, x_max, ax=window.ax, path_labels=self.processor.path_labels
                )
                window.canvas.draw()
            
            # Plot 4: Branch-to-Branch Phase
            if "Branch-to-Branch Phase" in self.plot_windows:
                window = self.plot_windows["Branch-to-Branch Phase"]
                window.ax.clear()
                self.processor.plotter.plot_branch_to_branch_phase(
                    frequency, s_params, x_min, x_max, ax=window.ax, path_labels=self.processor.path_labels
                )
                window.canvas.draw()
            
            # Update compliance checks with new frequency range
            self.run_compliance_checks()
            
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Invalid axis values: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating plots: {str(e)}")
    
    def run_compliance_checks(self):
        """Run compliance checks - calls backend processor."""
        try:
            # Compliance checks use fixed frequency range (2.7-4.1 GHz)
            # Don't use the plot axis limits for compliance
            result = self.processor.run_compliance_checks()
            
            if not result['success']:
                QMessageBox.critical(self, "Error", result['error'])
                return
            
            # Update compliance table (GUI only displays)
            self.update_compliance_table(result['results'])
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error running compliance checks: {str(e)}")
    
    def update_compliance_table(self, compliance_results):
        """Update the compliance results table."""
        # Clear existing items
        self.compliance_tree.clear()
        
        if compliance_results is None:
            return
        
        # Define colors for pass/fail
        pass_color = "#00FF00"  # Bright green
        fail_color = "#FF0000"  # Bright red
        
        # Return Loss
        return_loss = compliance_results['return_loss']
        rl_parent = QTreeWidgetItem(self.compliance_tree)
        rl_parent.setText(0, "Return Loss")
        status_text = "✓ PASS" if return_loss['all_pass'] else "✗ FAIL"
        rl_parent.setText(1, status_text)
        rl_parent.setText(3, f"< {self.processor.compliance_checker.return_loss_threshold_db} dB")
        
        # Set color for parent item
        if return_loss['all_pass']:
            rl_parent.setForeground(1, QApplication.instance().palette().color(QApplication.instance().palette().Base))
            rl_parent.setBackground(1, QApplication.instance().palette().color(QApplication.instance().palette().Base))
        else:
            rl_parent.setForeground(1, QApplication.instance().palette().color(QApplication.instance().palette().Base))
            rl_parent.setBackground(1, QApplication.instance().palette().color(QApplication.instance().palette().Base))
        
        for port, result in return_loss['results'].items():
            item = QTreeWidgetItem(rl_parent)
            item.setText(0, port)
            status_text = "✓ PASS" if result['pass'] else "✗ FAIL"
            item.setText(1, status_text)
            item.setText(2, f"{result['worst_value_db']:.2f} dB")
            
            # Set background color for status column
            if result['pass']:
                item.setBackground(1, QColor(pass_color))
                item.setForeground(1, QColor("#000000"))  # Black text on green
            else:
                item.setBackground(1, QColor(fail_color))
                item.setForeground(1, QColor("#FFFFFF"))  # White text on red
        
        rl_parent.setExpanded(True)
        
        # Gain Flatness
        gain_flat = compliance_results['gain_flatness']
        gf_parent = QTreeWidgetItem(self.compliance_tree)
        gf_parent.setText(0, "Gain Flatness")
        status_text = "✓ PASS" if gain_flat['all_pass'] else "✗ FAIL"
        gf_parent.setText(1, status_text)
        gf_parent.setText(3, f"< {self.processor.compliance_checker.gain_flatness_threshold_db} dB")
        
        for branch, result in gain_flat['results'].items():
            item = QTreeWidgetItem(gf_parent)
            item.setText(0, branch)
            status_text = "✓ PASS" if result['pass'] else "✗ FAIL"
            item.setText(1, status_text)
            item.setText(2, f"{result['p2p_variation_db']:.3f} dB")
            
            # Set background color for status column
            if result['pass']:
                item.setBackground(1, QColor(pass_color))
                item.setForeground(1, QColor("#000000"))  # Black text on green
            else:
                item.setBackground(1, QColor(fail_color))
                item.setForeground(1, QColor("#FFFFFF"))  # White text on red
        
        gf_parent.setExpanded(True)
        
        # Max Gain Difference
        max_gain = compliance_results['max_gain_difference']
        max_gain_item = QTreeWidgetItem(self.compliance_tree)
        max_gain_item.setText(0, "Max Gain Difference")
        status_text = "✓ PASS" if max_gain['all_pass'] else "✗ FAIL"
        max_gain_item.setText(1, status_text)
        max_gain_item.setText(2, f"{max_gain['worst_difference_db']:.3f} dB")
        max_gain_item.setText(3, f"< {max_gain['threshold_db']} dB")
        
        # Set color for max gain difference
        if max_gain['all_pass']:
            max_gain_item.setBackground(1, QColor(pass_color))
            max_gain_item.setForeground(1, QColor("#000000"))
        else:
            max_gain_item.setBackground(1, QColor(fail_color))
            max_gain_item.setForeground(1, QColor("#FFFFFF"))
        
        # Max Phase Difference
        max_phase = compliance_results['max_phase_difference']
        max_phase_item = QTreeWidgetItem(self.compliance_tree)
        max_phase_item.setText(0, "Max Phase Difference")
        status_text = "✓ PASS" if max_phase['all_pass'] else "✗ FAIL"
        max_phase_item.setText(1, status_text)
        max_phase_item.setText(2, f"{max_phase['worst_difference_degrees']:.2f}°")
        max_phase_item.setText(3, f"< {max_phase['threshold_degrees']}°")
        
        # Set color for max phase difference
        if max_phase['all_pass']:
            max_phase_item.setBackground(1, QColor(pass_color))
            max_phase_item.setForeground(1, QColor("#000000"))
        else:
            max_phase_item.setBackground(1, QColor(fail_color))
            max_phase_item.setForeground(1, QColor("#FFFFFF"))
    
    def copy_compliance_table(self):
        """Copy compliance table to clipboard."""
        text = self.processor.format_compliance_for_copy()
        
        if "No compliance results" in text:
            QMessageBox.information(self, "Info", "No compliance results to copy")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Success", "Compliance results copied to clipboard")
    
    def save_compliance_image(self):
        """Save compliance table as image."""
        text = self.processor.format_compliance_for_image()
        
        if "No compliance results" in text:
            QMessageBox.information(self, "Info", "No compliance results to save")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Compliance Results",
            "",
            "PNG files (*.png);;All files (*.*)"
        )
        
        if not filename:
            return
        
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.axis('off')
            ax.text(0.1, 0.9, text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top', family='monospace')
            
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            QMessageBox.information(self, "Success", f"Compliance results saved to {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving image: {str(e)}")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = RFCombinerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
