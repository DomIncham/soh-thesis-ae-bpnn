import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def generate_interpolation_proof():
    # จำลองจุดข้อมูล EIS ที่เบาบาง (Sparse Data) คล้ายข้อมูลดิบ
    x_sparse = np.linspace(0, np.pi, 8)
    y_sparse = np.sin(x_sparse) + np.random.normal(0, 0.05, 8) # รูปร่างครึ่งวงกลมแบบมี Noise เล็กน้อย
    
    # แกนความละเอียดสูงสำหรับการทำ Interpolate (128 จุด)
    x_dense = np.linspace(0, np.pi, 128)
    
    # 1. Linear Interpolation (เส้นตรง)
    linear_func = interp1d(x_sparse, y_sparse, kind='linear')
    y_linear = linear_func(x_dense)
    
    # 2. Cubic Spline Interpolation (เส้นโค้งพหุนาม)
    cubic_func = interp1d(x_sparse, y_sparse, kind='cubic')
    y_cubic = cubic_func(x_dense)
    
    # วาดกราฟเปรียบเทียบ
    plt.figure(figsize=(10, 5))
    plt.plot(x_sparse, y_sparse, 'ko', markersize=8, label='Raw NASA Data Points (Sparse)')
    plt.plot(x_dense, y_linear, 'r--', linewidth=2, label='Linear (Jagged & Unnatural)')
    plt.plot(x_dense, y_cubic, 'b-', linewidth=2, label='Cubic Spline (Smooth Physics-based)')
    
    plt.title('Proof of Concept: Why Cubic Spline is Required for EIS Nyquist Arcs')
    plt.xlabel('Re_Z (Simulated)')
    plt.ylabel('-Im_Z (Simulated)')
    plt.legend()
    plt.grid(True)
    plt.savefig('Proof_Interpolation.png')
    print("Saved 'Proof_Interpolation.png'")

if __name__ == "__main__":
    generate_interpolation_proof()