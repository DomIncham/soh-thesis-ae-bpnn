import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d, PchipInterpolator

def test_parametric_interpolation():
    print("Loading data for diagnostic...")
    # Load raw CSV
    df = pd.read_csv('NASA_Impedance_Data.csv')
    
    # Extract just one cycle to test (Battery 1, Cycle 41)
    sample = df[(df['Battery_ID'] == 1) & (df['Cycle'] == 41)].copy()
    
    re_z = sample['Re_Z'].values
    neg_im_z = sample['Neg_Im_Z'].values
    n_raw_points = len(re_z)
    
    # ---------------------------------------------------------
    # PARAMETRIC INTERPOLATION (The correct way for arcs/curves)
    # Instead of guessing frequency, we use normalized distance 't'
    # ---------------------------------------------------------
    # Create a normalized distance vector 't' from 0.0 to 1.0 based on index
    t_raw = np.linspace(0, 1, num=n_raw_points)
    
    # Create the target high-resolution 't' vector (128 points)
    t_target = np.linspace(0, 1, num=128)
    
    # Interpolate Re_Z and Neg_Im_Z independently against 't'
    # 1. Cubic Spline
    re_cubic = interp1d(t_raw, re_z, kind='cubic')(t_target)
    im_cubic = interp1d(t_raw, neg_im_z, kind='cubic')(t_target)
    
    # 2. PCHIP (Monotonic, prevents overshoot)
    re_pchip = PchipInterpolator(t_raw, re_z)(t_target)
    im_pchip = PchipInterpolator(t_raw, neg_im_z)(t_target)
    
    # 3. Linear (Baseline)
    re_linear = interp1d(t_raw, re_z, kind='linear')(t_target)
    im_linear = interp1d(t_raw, neg_im_z, kind='linear')(t_target)
    
    # ---------------------------------------------------------
    # PLOTTING
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    
    # Plot original 39 points
    plt.plot(re_z, neg_im_z, 'ko', markersize=6, label=f'Raw Data ({n_raw_points} pts)')
    
    # Plot interpolated curves
    plt.plot(re_linear, im_linear, ':', color='gray', label='Linear', alpha=0.7)
    plt.plot(re_cubic, im_cubic, '--', color='red', label='Cubic Spline', linewidth=1.5)
    plt.plot(re_pchip, im_pchip, '-', color='blue', label='PCHIP', linewidth=1.5)
    
    plt.title('Corrected Interpolation: Parametric Nyquist Arc (Battery 1, Cycle 41)')
    plt.xlabel('Re_Z ($\Omega$)')
    plt.ylabel('-Im_Z ($\Omega$)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig('Parametric_Diagnostic.png')
    print("Success! Please review 'Parametric_Diagnostic.png'")

if __name__ == "__main__":
    test_parametric_interpolation()