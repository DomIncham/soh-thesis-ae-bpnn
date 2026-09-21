import torch
import numpy as np
import matplotlib.pyplot as plt
import os

def inspect_all_interpolations():
    print("--- Verifying Generated .pt Files and Visualizing Curves ---")
    
    grid_types = ['linear_grid', 'log_grid']
    methods = ['linear', 'cubic', 'pchip']
    
    plt.figure(figsize=(15, 6))
    
    for idx, g_name in enumerate(grid_types, 1):
        plt.subplot(1, 2, idx)
        
        for m_name in methods:
            filename = f'Interpolated_EIS_{g_name}_{m_name}.pt'
            if not os.path.exists(filename):
                print(f"[ERROR] '{filename}' not found. Please run data_interpolation.py first.")
                return
                
            data = torch.load(filename, weights_only=True)
            X = data['features'] # Shape: (Samples, 256)
            y = data['labels']   # Shape: (Samples, 2)
            
            # Extract the first sample cycle (Cycle 41, Battery 1)
            sample_vector = X[0].numpy()
            re_z = sample_vector[:128]
            neg_im_z = sample_vector[128:]
            
            style = ':' if m_name == 'linear' else ('--' if m_name == 'cubic' else '-')
            color = 'gray' if m_name == 'linear' else ('red' if m_name == 'cubic' else 'blue')
            alpha = 0.6 if m_name == 'linear' else (0.8 if m_name == 'cubic' else 1.0)
            
            plt.plot(re_z, neg_im_z, label=f'{m_name.upper()}', linestyle=style, color=color, alpha=alpha, linewidth=1.8)
            
        grid_label = 'Linear Frequency Grid' if g_name == 'linear_grid' else 'Logarithmic Frequency Grid'
        plt.title(f'Assumption: {grid_label} (Cycle 41, B0005)')
        plt.xlabel('Re_Z ($\Omega$)')
        plt.ylabel('-Im_Z ($\Omega$)')
        plt.legend()
        plt.grid(True)
        
    plt.tight_layout()
    output_png = 'Proof_Interpolation_Ablation.png'
    plt.savefig(output_png)
    print(f"[SUCCESS] Visual validation plot saved as '{output_png}'.")
    plt.show()

if __name__ == "__main__":
    inspect_all_interpolations()