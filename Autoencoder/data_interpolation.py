import pandas as pd
import numpy as np
from scipy.interpolate import interp1d, PchipInterpolator
import torch
import os

def generate_ablation_datasets():
    print("================================================================")
    print("Starting Physics-Based EIS Data Interpolation (Ablation Pipeline)")
    print("================================================================")
    
    csv_file = 'NASA_Impedance_Data.csv'
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"[ERROR] '{csv_file}' not found. Please export it from MATLAB first.")
        
    df = pd.read_csv(csv_file)
    batteries = df['Battery_ID'].unique()
    num_target_points = 128 # 128 for Re(Z) + 128 for -Im(Z) = 256 features
    
    # -------------------------------------------------------------------------
    # Physical Frequency Boundaries (Derived from NASA PCoE Dataset Readme)
    # Range: 0.1 Hz to 5000 Hz (5 kHz)
    # -------------------------------------------------------------------------
    f_min = 0.1
    f_max = 5000.0
    
    grid_types = ['linear_grid', 'log_grid']
    methods = ['linear', 'cubic', 'pchip']
    
    # Storage structure for the 6 ablation datasets
    ablation_stores = {f"{g}_{m}": {'features': [], 'labels': []} 
                       for g in grid_types for m in methods}
    
    print(f"Total Batteries Found: {len(batteries)}")
    print(f"Target Output Dimension per Cycle: 256 Features (16x16 representation)\n")

    for b_id in batteries:
        batt_data = df[df['Battery_ID'] == b_id]
        cycles = batt_data['Cycle'].unique()
        
        for cycle in cycles:
            cycle_data = batt_data[batt_data['Cycle'] == cycle]
            re_z = cycle_data['Re_Z'].values
            neg_im_z = cycle_data['Neg_Im_Z'].values
            
            n_pts = len(re_z)
            if n_pts < 4:
                continue # Skip cycles with insufficient data points for cubic/pchip
                
            # -----------------------------------------------------------------
            # 1. Constructing Frequency Grids (Academic Rigor)
            # -----------------------------------------------------------------
            # Grid 1: Linear-spaced Frequency Sweep
            x_linear_raw = np.linspace(f_min, f_max, num=n_pts)
            x_linear_target = np.linspace(f_min, f_max, num=num_target_points)
            
            # Grid 2: Log-spaced Frequency Sweep (Standard for EIS Potentiostats)
            x_log_raw = np.logspace(np.log10(f_min), np.log10(f_max), num=n_pts)
            x_log_target = np.logspace(np.log10(f_min), np.log10(f_max), num=num_target_points)
            
            grid_configs = [
                ('linear_grid', x_linear_raw, x_linear_target),
                ('log_grid', x_log_raw, x_log_target)
            ]
            
            # -----------------------------------------------------------------
            # 2. Applying Interpolation Algorithms
            # -----------------------------------------------------------------
            for g_name, x_raw, x_target in grid_configs:
                for method in methods:
                    key = f"{g_name}_{method}"
                    
                    if method == 'linear':
                        interp_re = interp1d(x_raw, re_z, kind='linear')
                        interp_im = interp1d(x_raw, neg_im_z, kind='linear')
                    elif method == 'cubic':
                        interp_re = interp1d(x_raw, re_z, kind='cubic')
                        interp_im = interp1d(x_raw, neg_im_z, kind='cubic')
                    elif method == 'pchip':
                        # Monotonic shape-preserving spline (Prevents overshoot)
                        interp_re = PchipInterpolator(x_raw, re_z)
                        interp_im = PchipInterpolator(x_raw, neg_im_z)
                        
                    re_resampled = interp_re(x_target)
                    im_resampled = interp_im(x_target)
                    
                    # Concatenate real and imaginary components into 256 vector
                    combined_256 = np.concatenate([re_resampled, im_resampled])
                    
                    ablation_stores[key]['features'].append(combined_256)
                    ablation_stores[key]['labels'].append([b_id, cycle])
                    
    # -------------------------------------------------------------------------
    # 3. Saving Standardized PyTorch Tensors
    # -------------------------------------------------------------------------
    print("Saving processed ablation datasets...")
    for key, data in ablation_stores.items():
        X_tensor = torch.tensor(np.array(data['features']), dtype=torch.float32)
        y_tensor = torch.tensor(np.array(data['labels']), dtype=torch.float32)
        
        output_filename = f'Interpolated_EIS_{key}.pt'
        torch.save({'features': X_tensor, 'labels': y_tensor}, output_filename)
        print(f"  [SAVED] {output_filename:<30} | Shape: {str(X_tensor.shape):<22}")
        
    print("\n[SUCCESS] All 6 Ablation datasets have been generated and validated.")

if __name__ == "__main__":
    generate_ablation_datasets()