clc;clear;
load 'B0005.mat';
time=B0005.cycle(180).data.Time;  
Vol=B0005.cycle(180).data.Voltage_measured;  
Current=B0005.cycle(180).data.Current_measured; 
figure(1)
plot(time,Vol);hold on;
plot(time,Current);
capacity=sum(Current);

impedence=B0005.cycle(165).data.Rectified_Impedance    ;
re=real(impedence);
im=imag(impedence);
figure(2)
plot(re,-im);
