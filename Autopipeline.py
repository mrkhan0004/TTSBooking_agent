import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

# Step 1: Load Data (replace with your own)
# Example assumes: InvoiceDate, CustomerID, InvoiceNo, Amount
df = pd.read_csv(r"C:/Users/LENOVO/Desktop/Shopkeeper/rfm_clustered_segments.csv", parse_dates=['InvoiceDate'])

# Step 2: Calculate RFM
snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
rfm = df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
    'InvoiceNo': 'nunique',
    'Amount': 'sum'
}).reset_index()
rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']

# Step 3: Log transformation (optional but recommended)
rfm_log = rfm.copy()
rfm_log[['Recency', 'Frequency', 'Monetary']] = np.log1p(rfm_log[['Recency', 'Frequency', 'Monetary']])

# Step 4: Scaling
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm_log[['Recency', 'Frequency', 'Monetary']])

# Step 5: Apply KMeans
kmeans = KMeans(n_clusters=4, random_state=42)
rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)

# Step 6: Map Cluster to Segment
cluster_map = {
    0: "New Customers",
    1: "Low Value / At Risk",
    2: "Potential Loyalists",
    3: "Champions"
}

# You may need to adjust labels after checking means
cluster_avg = rfm.groupby('Cluster')[['Recency', 'Frequency', 'Monetary']].mean()
sorted_clusters = cluster_avg.sort_values(['Recency', 'Frequency', 'Monetary'], ascending=[True, False, False])
sorted_map = {cluster: label for cluster, label in zip(sorted_clusters.index, cluster_map.values())}
rfm['Segment'] = rfm['Cluster'].map(sorted_map)

# Step 7: Export Final Output
rfm.to_csv("rfm_segmented_customers.csv", index=False)

# Step 8: Plot Segments
plt.figure(figsize=(10,6))
sns.scatterplot(data=rfm, x='Recency', y='Monetary', hue='Segment', palette='Set2')
plt.title('Customer Segments by RFM Clustering')
plt.savefig("rfm_segment_plot.png")
plt.show()

