import pandas as pd
import matplotlib.pyplot as plt

def generate_jitter_proof():
    # โหลดข้อมูลจริง
    df = pd.read_csv('NASA_Capacity_Data.csv')
    
    # เลือกแบตเตอรี่ก้อนที่ 1 และซูมดูช่วง Cycle 300-400
    df_b1 = df[(df['Battery_ID'] == 1) & (df['Cycle'] >= 300) & (df['Cycle'] <= 400)]
    
    plt.figure(figsize=(10, 5))
    plt.plot(df_b1['Cycle'], df_b1['Capacity_Ah'], 'r-o', markersize=4, linewidth=1.5)
    
    plt.title('Proof of Temporal Jitter: Raw NASA Capacity Data (Cycles 300-400)')
    plt.xlabel('Cycle Number')
    plt.ylabel('Capacity (Ah)')
    plt.grid(True)
    
    # ใส่ Annotation ชี้ให้เห็นฟันปลา
    plt.annotate('High-Frequency Inter-cycle Jitter', 
                 xy=(320, df_b1[df_b1['Cycle']==320]['Capacity_Ah'].values[0]),
                 xytext=(330, 1.55),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 fontsize=10)
                 
    plt.savefig('Proof_Temporal_Jitter.png')
    print("Saved 'Proof_Temporal_Jitter.png'")

if __name__ == "__main__":
    generate_jitter_proof()