# Shopkeeper - Customer Segmentation and Recommendation System

## Overview
This project implements a comprehensive customer segmentation and recommendation system using RFM (Recency, Frequency, Monetary) analysis and K-means clustering. The system analyzes customer behavior patterns and provides personalized recommendations for e-commerce businesses.

## Features
- **RFM Analysis**: Customer segmentation based on Recency, Frequency, and Monetary values
- **K-means Clustering**: Automated customer grouping using machine learning
- **Streamlit Web App**: Interactive web interface for data analysis and visualization
- **Automated Pipeline**: End-to-end data processing and modeling pipeline
- **Model Persistence**: Saved models for quick deployment and reuse

## Files Description

### Core Python Files
- `shop_streamlit.py` - Main Streamlit web application
- `rfm_pipeline.py` - RFM analysis and segmentation pipeline
- `Autopipeline.py` - Automated data processing pipeline

### Jupyter Notebooks
- `Final_Shpkeeper.ipynb` - Complete project analysis and implementation
- `Untitled.ipynb` - Additional analysis notebook

### Data Files
- `online_retail.csv` - Raw customer transaction data
- `rfm_segmented.csv` - RFM analysis results
- `rfm_clustered_segments.csv` - Final customer segments with clustering

### Model Files
- `kmeans_model.pkl` - Trained K-means clustering model
- `kmeans_rfm_model.pkl` - RFM-specific clustering model
- `rfm_scaler.pkl` - Data scaling parameters

### Documentation
- `Shopper Spectrum_ Segmentation and Recommendations.docx` - Project documentation

## Installation and Usage

### Prerequisites
```bash
pip install streamlit pandas numpy scikit-learn matplotlib seaborn plotly
```

### Running the Streamlit App
```bash
streamlit run shop_streamlit.py
```

### Running the RFM Pipeline
```bash
python rfm_pipeline.py
```

## Project Structure
```
Alproject/
├── README.md
├── shop_streamlit.py          # Main web application
├── rfm_pipeline.py            # RFM analysis pipeline
├── Autopipeline.py            # Automated pipeline
├── Final_Shpkeeper.ipynb      # Main analysis notebook
├── Untitled.ipynb             # Additional analysis
├── online_retail.csv          # Raw data
├── rfm_segmented.csv          # RFM results
├── rfm_clustered_segments.csv # Final segments
├── kmeans_model.pkl           # Clustering model
├── kmeans_rfm_model.pkl       # RFM model
├── rfm_scaler.pkl             # Scaler
└── Shopper Spectrum_ Segmentation and Recommendations.docx
```

## Methodology

### RFM Analysis
1. **Recency**: How recently a customer made a purchase
2. **Frequency**: How often a customer makes purchases
3. **Monetary**: How much money a customer spends

### Clustering
- K-means clustering applied to RFM scores
- Optimal number of clusters determined using elbow method
- Customer segments created based on behavioral patterns

## Results
The system identifies distinct customer segments:
- High-value customers requiring premium attention
- Medium-value customers for targeted marketing
- Low-value customers for re-engagement campaigns

## Contributing
This project is part of the Alproject repository. Feel free to contribute improvements and enhancements.

## License
This project is open source and available under the MIT License.
