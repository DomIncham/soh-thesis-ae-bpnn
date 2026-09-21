import pandas as pd
import numpy as np
import torch
import os

def build_mapped_datasets():
    print("="*75)
    print("Building Formally Mapped Datasets (EIS Features -> SOH Labels)")
    print("Mapping Rule: Causal Backward Matching (Tolerance = 3 Cycles)")
    print("="*75)

    cap_file = 'NASA_Capacity_Data.csv'
    if not os.path.exists(cap_file):
        print(f"[ERROR] '{cap_file}' not found.")
        return

    # 1. โหลดข้อมูล Capacity
    df_cap = pd.read_csv(cap_file)
    df_cap['Battery_ID'] = df_cap['Battery_ID'].astype(int)
    df_cap['Cycle'] = df_cap['Cycle'].astype(int)

    grid_types = ['linear_grid', 'log_grid']
    methods = ['linear', 'cubic', 'pchip']
    
    mapping_stats = []

    for g_name in grid_types:
        for m_name in methods:
            input_pt = f'Interpolated_EIS_{g_name}_{m_name}.pt'
            output_pt = f'Mapped_EIS_SOH_{g_name}_{m_name}.pt'

            if not os.path.exists(input_pt):
                print(f"[WARNING] Skipping {input_pt} (File not found)")
                continue

            # 2. โหลดไฟล์ EIS
            eis_data = torch.load(input_pt, weights_only=True)
            X_raw = eis_data['features'].numpy()
            labels_raw = eis_data['labels'].numpy()

            df_eis = pd.DataFrame(labels_raw, columns=['Battery_ID', 'Cycle'])
            df_eis['Battery_ID'] = df_eis['Battery_ID'].astype(int)
            df_eis['Cycle'] = df_eis['Cycle'].astype(int)
            df_eis['Original_Idx'] = np.arange(len(df_eis))

            # 3. ดำเนินการ Causal Backward Merge (Tolerance = 3)
            merged_list = []
            for b_id in [1, 2, 3, 4]:
                b_eis = df_eis[df_eis['Battery_ID'] == b_id].sort_values('Cycle')
                b_cap = df_cap[df_cap['Battery_ID'] == b_id].sort_values('Cycle')

                b_merged = pd.merge_asof(
                    b_eis,
                    b_cap[['Cycle', 'Capacity_Ah']],
                    on='Cycle',
                    direction='backward', # ป้องกัน Future-data leakage
                    tolerance=3
                )
                merged_list.append(b_merged)

            full_df = pd.concat(merged_list).sort_values('Original_Idx')
            
            # กรองแถวที่ไม่มีข้อมูล Capacity ในอดีต (1 แถวจาก B0018 Cycle 2)
            valid_mask = full_df['Capacity_Ah'].notna()
            matched_df = full_df[valid_mask].copy()
            valid_indices = matched_df['Original_Idx'].values

            X_mapped = X_raw[valid_indices]
            
            # y_mapped เก็บ [Battery_ID, Cycle, Capacity_Ah]
            y_mapped = matched_df[['Battery_ID', 'Cycle', 'Capacity_Ah']].values

            # 4. บันทึกเป็นไฟล์ PyTorch Dataset (.pt)
            torch.save({
                'features': torch.tensor(X_mapped, dtype=torch.float32),
                'labels': torch.tensor(y_mapped, dtype=torch.float32)
            }, output_pt)

            total_samples = len(X_raw)
            retained_samples = len(X_mapped)
            dropped_samples = total_samples - retained_samples

            print(f"Processed: {input_pt:<36} -> Saved: {output_pt}")
            print(f"  Total: {total_samples} | Retained: {retained_samples} ({retained_samples/total_samples*100:.2f}%) | Dropped: {dropped_samples}")

            mapping_stats.append({
                'Dataset': f"{g_name}_{m_name}",
                'Original_EIS': total_samples,
                'Mapped_Samples': retained_samples,
                'Dropped_Samples': dropped_samples,
                'Retention_Rate': f"{retained_samples/total_samples*100:.2f}%"
            })

    print("\n" + "="*75)
    print("Mapping Process Completed Successfully (Priority 2 Finalized)")
    print("="*75)
    df_summary = pd.DataFrame(mapping_stats)
    print(df_summary.to_markdown(index=False))

if __name__ == "__main__":
    build_mapped_datasets()