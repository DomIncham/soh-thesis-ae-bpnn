clc; clear; close all;

% Define the target battery dataset names (NASA PCoE dataset)
battery_names = {'B0005', 'B0006', 'B0007', 'B0018'};
all_imp_data = []; % Initialize an empty array to store consolidated data

fprintf('--- Starting NASA EIS Data Extraction ---\n');

% Loop through each battery dataset file
for b = 1:length(battery_names)
    batt_name = battery_names{b};
    
    % Check if the .mat file exists in the current directory
    if isfile([batt_name, '.mat'])
        fprintf('Loading %s.mat...\n', batt_name);
        load([batt_name, '.mat']); 
        data_struct = eval(batt_name); 
        
        % Iterate through each cycle in the battery structure
        for i = 1:length(data_struct.cycle)
            % Check if the current cycle type is 'impedance'
            if strcmp(data_struct.cycle(i).type, 'impedance')
                
                % Extract the impedance array
                imp_data = data_struct.cycle(i).data.Rectified_Impedance;
                
                % Ensure data is strictly a Column Vector (Nx1)
                re = real(imp_data(:));       
                neg_im = -imag(imp_data(:));  
                
                % Create labels for Battery ID and Cycle Number
                batt_id = repmat(b, length(re), 1);
                cycle_num = repmat(i, length(re), 1);
                
                % Concatenate features: [Battery_ID, Cycle, Re_Z, Neg_Im_Z]
                temp_data = [batt_id, cycle_num, re, neg_im];
                
                % Append to the master dataset
                all_imp_data = [all_imp_data; temp_data];
            end
        end
        fprintf('Successfully extracted EIS data from %s\n', batt_name);
    else
        fprintf('Warning: File %s.mat not found. Skipping.\n', batt_name);
    end
end

% Check if data was collected before trying to save
if ~isempty(all_imp_data)
    csv_filename = 'NASA_Impedance_Data.csv';
    
    % [ERROR PREVENTION]: Check if the file is currently open and locked by another program (like Excel)
    fid = fopen(csv_filename, 'a');
    if fid == -1
        error('\n[PERMISSION DENIED] Cannot write to "%s".\n--> PLEASE CLOSE the file in Excel or any other program and run this script again.\n', csv_filename);
    else
        fclose(fid); % File is safe to write, close the test connection
    end
    
    % Create table and export
    fprintf('Writing data to %s...\n', csv_filename);
    T = array2table(all_imp_data, 'VariableNames', {'Battery_ID', 'Cycle', 'Re_Z', 'Neg_Im_Z'});
    writetable(T, csv_filename);
    
    fprintf('--- Data Export Completed Successfully! ---\n');
else
    fprintf('No impedance data was found in the provided .mat files.\n');
end