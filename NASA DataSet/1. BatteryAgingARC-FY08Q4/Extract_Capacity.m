clc; clear; close all;

% Define the target battery dataset names
battery_names = {'B0005', 'B0006', 'B0007', 'B0018'};
capacity_data = []; % Initialize empty array

fprintf('Extracting Capacity data for BPNN Labels...\n');

% Loop through each battery dataset file
for b = 1:length(battery_names)
    batt_name = battery_names{b};
    
    if isfile([batt_name, '.mat'])
        load([batt_name, '.mat']);
        data_struct = eval(batt_name);
        
        % Iterate through each cycle
        for i = 1:length(data_struct.cycle)
            % Check if the current cycle type is 'discharge'
            if strcmp(data_struct.cycle(i).type, 'discharge')
                
                % Extract Capacity (Ah)
                cap = data_struct.cycle(i).data.Capacity;
                
                % Some cycles might have empty capacity data, skip if empty
                if ~isempty(cap)
                    % Create a temporary array: [Battery_ID, Cycle, Capacity]
                    temp_data = [b, i, cap];
                    capacity_data = [capacity_data; temp_data];
                end
            end
        end
        fprintf('Successfully extracted Capacity from %s\n', batt_name);
    else
        fprintf('Warning: File %s.mat not found.\n', batt_name);
    end
end

% Export to CSV
if ~isempty(capacity_data)
    T = array2table(capacity_data, 'VariableNames', {'Battery_ID', 'Cycle', 'Capacity_Ah'});
    csv_filename = 'NASA_Capacity_Data.csv';
    writetable(T, csv_filename);
    
    fprintf('--- Data Export Completed! ---\n');
    fprintf('Labels successfully saved as: %s\n', csv_filename);
end