"""
Master Execution Pipeline for Netflix Movies & TV Shows Data Analysis.

Executes the entire end-to-end workflow:
  1. Data Cleaning & Feature Engineering (src.data_cleaning)
  2. Exploratory Data Analysis & Statistical Profiling (src.exploratory_analysis)
  3. Visualizations Generation (src.visualization)
"""

import os
import sys
import time

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_cleaning import clean_netflix_pipeline
from src.exploratory_analysis import run_full_eda
from src.visualization import generate_all_visualizations


def main():
    print("\n" + "#" * 70)
    print("  NETFLIX MOVIES & TV SHOWS DATA ANALYSIS - END-TO-END PIPELINE")
    print("#" * 70 + "\n")
    
    start_time = time.time()
    
    # 1. Clean Data
    print(">>> STEP 1: EXECUTING DATA CLEANING PIPELINE...")
    cleaned_df = clean_netflix_pipeline(
        raw_path="data/netflix_titles.csv",
        output_path="data/netflix_cleaned.csv"
    )
    
    # 2. Run EDA
    print("\n>>> STEP 2: RUNNING EXPLORATORY DATA ANALYSIS (EDA)...")
    eda_results = run_full_eda(data_path="data/netflix_cleaned.csv")
    
    # 3. Generate Visualizations
    print("\n>>> STEP 3: GENERATING PUBLICATION-QUALITY CHARTS...")
    generate_all_visualizations(
        data_path="data/netflix_cleaned.csv",
        output_dir="visualizations"
    )
    
    elapsed = time.time() - start_time
    print("\n" + "#" * 70)
    print(f"  PIPELINE EXECUTION COMPLETE IN {elapsed:.2f} SECONDS!")
    print(f"  Cleaned Dataset: data/netflix_cleaned.csv ({len(cleaned_df):,} records)")
    print(f"  Visualizations:  visualizations/ (12 PNG charts generated)")
    print(f"  Business Report: reports/insights.md")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    main()
