import pandas as pd

def process_dataframe(df):
    # Replace dot notation with bracket notation for column access
    filtered_df = df[df['column_name'] > 0]  # Example filtering operation
    return filtered_df

if __name__ == '__main__':
    data = {'column_name': [1, 2, -1, 4]}
    df = pd.DataFrame(data)
    result = process_dataframe(df)
    print(result)