import sys
import os
import fitparse
import json

def fit_to_json(input_filepath):
    base_name = os.path.splitext(input_filepath)[0]
    output_filepath = f"{base_name}.json"

    try:
        # Load the .fit file
        fitfile = fitparse.FitFile(input_filepath)
        session_data = []

        # loop trough records
        for record in fitfile.get_messages():
            record_data = {field.name: field.value for field in record if field.value is not None}
            session_data.append({
                "type": record.name,
                "data": record_data
            })

        # return json file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent =4, default=str)
        
        print(f"Exito>> Convirtio '{input_filepath}' -> '{output_filepath}'")

    except Exception as e:
        print(f"Error procesando '{input_filepath}': {e}")
        
if __name__== "__main__":
    if len(sys.argv) != 2:
        print("Uso: p3 main.py <nombre archivo>")
        sys.exit(1)

    target_path = sys.argv[1]
    
    if os.path.isfile(target_path) and target_path.lower().endswith('.fit'):
        fit_to_json(target_path)
    elif os.path.isdir(target_path):
        for filename in os.listdir(target_path):
            if filename.lower().endswith('.fit'):
                fit_to_json(os.path.join(target_path, filename))
    else:
        print("Error: Provide a valid .fit file or a directory containing .fit files.")
