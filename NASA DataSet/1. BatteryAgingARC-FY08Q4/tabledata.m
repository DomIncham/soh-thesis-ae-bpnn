clc; clear; close all;

% 1. โหลดข้อมูล
load('B0005.mat'); 

% --- ส่วนที่ 1: ตาราง Impedance (EIS) ---
cycle_idx = 165; 
imp_data = B0005.cycle(cycle_idx).data.Rectified_Impedance;
re = real(imp_data);
neg_im = -imag(imp_data);

% สร้างตารางสำหรับแสดงผล
T_imp = table((1:length(re))', re, neg_im, 'VariableNames', {'Point', 'Re_Z', 'Neg_Im_Z'});

% แสดงตารางในหน้าต่างใหม่ (UI Table)
figure('Name', 'Impedance Data Table', 'Position', [100, 100, 300, 400]);
uitable('Data', table2cell(T_imp), 'ColumnName', T_imp.Properties.VariableNames, ...
        'Units', 'Normalized', 'Position', [0.05, 0.05, 0.9, 0.9]);

% --- ส่วนที่ 2: ตารางแนวโน้ม SOH (Capacity) ---
% ดึงข้อมูล Capacity ทุกรอบ
num_cycles = length(B0005.cycle);
cycles = (1:num_cycles)';
caps = zeros(num_cycles, 1);
for i = 1:num_cycles
    if isfield(B0005.cycle(i).data, 'Capacity')
        caps(i) = B0005.cycle(i).data.Capacity;
    end
end

% คำนวณ SOH (เปรียบเทียบกับรอบแรก)
soh = (caps / caps(1)) * 100;
T_soh = table(cycles, caps, soh, 'VariableNames', {'Cycle', 'Capacity_Ah', 'SOH_Percent'});

% แสดงตาราง SOH 10 รอบแรกใน Command Window
disp('--- ตารางแนวโน้ม SOH (10 รอบแรก) ---');
disp(head(T_soh, 10));

% --- ส่วนที่ 3: กราฟที่สรุปข้อมูล (สำหรับทำสไลด์) ---
figure('Name', 'SOH and Impedance Summary');

% กราฟ Capacity Fade
subplot(2,1,1);
plot(cycles, caps, 'b-', 'LineWidth', 2);
xlabel('Cycle Number'); ylabel('Capacity (Ah)');
title('Battery Capacity Degradation (SOH Trend)');
grid on;

% กราฟ Nyquist (EIS)
subplot(2,1,2);
plot(re, neg_im, 'ro-', 'LineWidth', 1);
xlabel('Re(Z) [\Omega]'); ylabel('-Im(Z) [\Omega]');
title('EIS Nyquist Plot');
grid on;