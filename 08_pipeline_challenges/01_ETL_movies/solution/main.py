import pandas as pd
import boto3
import os
from io import StringIO
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename='pipeline.log',
    filemode='w'
)

# Load environment variables
load_dotenv()
dataset_path = os.getenv('DATASET_PATH', 'datasets/movies.csv')
bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
s3_file_name = os.getenv('S3_FILE_NAME', 'cleaned_movies.csv')
local_cleaned_file = 'datasets/cleaned_movies.csv'

# Function to load the dataset
def load_dataset(file_path):
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Dataset loaded successfully. Rows: {len(df)}, Columns: {len(df.columns)}")
        return df
    except FileNotFoundError:
        logging.error(f"File '{file_path}' not found.")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while loading dataset: {e}")
        raise

# Standardize column names
def standardize_columns(df):
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    return df

# Clean text columns
def clean_text_columns(df, text_cols):
    for col in text_cols:
        df[col] = (
            df[col]
            .str.replace('\n', ' ', regex=True)
            .str.replace('Director:', '', regex=True)
            .str.replace('Stars:', '', regex=True)
            .str.replace(r'\|', '', regex=True)
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )
    return df

# Clean 'year' column
def clean_year_column(df):
    df['year'] = df['year'].str.extract(r'(\d{4})').astype('Int64')
    return df

# Clean 'votes' column
def clean_votes_column(df):
    df['votes'] = df['votes'].str.replace(',', '', regex=True).astype('Int64')
    return df

# Drop unnecessary columns
def drop_unnecessary_columns(df, columns_to_drop):
    return df.drop(columns=columns_to_drop)

# Convert column types
def convert_column_types(df):
    df['rating'] = df['rating'].astype('float')
    df['runtime'] = df['runtime'].astype('float')
    return df

# Drop duplicate rows
def drop_duplicates(df):
    duplicates = df.duplicated().sum()
    df = df.drop_duplicates()
    logging.info(f"Removed {duplicates} duplicate rows.")
    return df

# Save DataFrame locally as CSV
def save_to_local(df, file_path):
    df.to_csv(file_path, index=False)
    logging.info(f"Cleaned dataset saved locally as: {file_path}")

# Upload DataFrame to S3
def load_to_s3(df, bucket_name, file_name):
    s3_client = boto3.client('s3')
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())
    logging.info(f"File successfully uploaded to S3: {bucket_name}/{file_name}")

# Pipeline Execution
if __name__ == "__main__":
    logging.info("Starting the Movies Data Pipeline...")

    # Define variables
    text_columns = ['movies', 'genre', 'stars', 'one-line']

    # Load data
    logging.info("Loading the dataset...")
    movies_df = load_dataset(dataset_path)

    # Start cleaning and processing
    logging.info("Starting data cleaning and processing...")
    movies_df = standardize_columns(movies_df)
    movies_df = clean_text_columns(movies_df, text_columns)
    movies_df = clean_year_column(movies_df)
    movies_df = clean_votes_column(movies_df)
    movies_df = drop_unnecessary_columns(movies_df, ['gross'])
    movies_df = convert_column_types(movies_df)

    # Drop duplicates and log removed count
    logging.info("Checking for duplicate rows...")
    movies_df = drop_duplicates(movies_df)

    # Save cleaned data locally
    logging.info(f"Saving cleaned data locally to '{local_cleaned_file}'...")
    save_to_local(movies_df, local_cleaned_file)

    # Upload cleaned data to S3
    logging.info(f"Uploading cleaned data to S3 bucket '{bucket_name}' as '{s3_file_name}'...")
    load_to_s3(movies_df, bucket_name, s3_file_name)

    # Final confirmation
    logging.info("Pipeline completed successfully. Sample of cleaned data:")
    print(movies_df.head(10))
