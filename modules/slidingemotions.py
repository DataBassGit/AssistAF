import pandas as pd

class CSVModifier:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_and_modify_csv(self, **kwargs):
        # Load the CSV file
        try:
            df = pd.read_csv(self.file_path)
        except FileNotFoundError:
            df = pd.DataFrame()

        # Process each kwarg
        for key, value in kwargs.items():
            if key not in df.columns:
                # If the column doesn't exist, add it with half the kwarg's value
                df[key] = value / 2
            else:
                # If the column exists, modify its values
                df[key] = df[key].apply(lambda x: x + (value - x) / 2 if value > x else x - (x - value) / 2)

        # Subtract 1 from all other columns to a minimum of 0
        for col in df.columns:
            if col not in kwargs:
                df[col] = df[col].apply(lambda x: max(x - 1, 0))

        # Save the modified DataFrame back to CSV
        df.to_csv(self.file_path, index=False)

# Usage
csv_modifier = CSVModifier('path_to_your_file.csv')
csv_modifier.load_and_modify_csv(column1=5, column2=3)  # Example kwargs
