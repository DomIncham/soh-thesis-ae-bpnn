import pandas as pd
import numpy as np

def analyze_cycle_gaps():
    print("1. Loading Datasets for EDA...")
    # Load raw CSV data
    df_eis = pd.read_csv('NASA_Impedance_Data.csv')
    df_cap = pd.read_csv('NASA_Capacity_Data.csv')
    
    # Get unique cycle numbers for each battery
    eis_cycles = df_eis.groupby('Battery_ID')['Cycle'].unique().reset_index()
    cap_cycles = df_cap.groupby('Battery_ID')['Cycle'].unique().reset_index()
    
    results = []
    
    print("2. Calculating Cycle Gaps (Impedance vs Discharge)...")
    # Loop through each battery to find the true gap
    for b_id in df_eis['Battery_ID'].unique():
        e_cycles = np.sort(eis_cycles[eis_cycles['Battery_ID'] == b_id]['Cycle'].values[0])
        c_cycles = np.sort(cap_cycles[cap_cycles['Battery_ID'] == b_id]['Cycle'].values[0])
        
        gaps = []
        # Find the absolute distance to the nearest Capacity cycle for each EIS cycle
        for ec in e_cycles:
            nearest_cc = c_cycles[np.argmin(np.abs(c_cycles - ec))]
            gaps.append(np.abs(nearest_cc - ec))
            
        max_gap = np.max(gaps)
        mean_gap = np.mean(gaps)
        p95_gap = np.percentile(gaps, 95) # 95th Percentile (Standard for research limits)
        
        results.append({
            'Battery_ID': b_id, 
            'Max_Gap': max_gap, 
            'Mean_Gap': round(mean_gap, 2), 
            '95th_Percentile': p95_gap
        })
        
    df_results = pd.DataFrame(results)
    print("\n=== EDA Results: Cycle Gap Analysis ===")
    print(df_results.to_string(index=False))
    print("=======================================")
    print("\n[Research Conclusion]: Use the 'Max_Gap' or '95th_Percentile' as your tolerance parameter in pd.merge_asof().")
    print("This proves to the defense committee that your parameter is data-driven, not guessed.")

if __name__ == "__main__":
    analyze_cycle_gaps()