
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

# Load your data
rfm = pd.read_csv("your_rfm_data.csv")  # Change this to your actual file name

# Select only numeric RFM columns
rfm_numeric = rfm[['Recency', 'Frequency', 'Monetary']]

# Standardize the data
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm_numeric)

# Apply KMeans clustering
kmeans = KMeans(n_clusters=4, random_state=42)
rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)

# Optional: RFM score if needed
rfm['RFM_Score'] = rfm['Recency'] * 0.15 + rfm['Frequency'] * 0.28 + rfm['Monetary'] * 0.57

# Map clusters to labels (based on analysis)
cluster_map = {
    0: "New Customers",
    1: "Low Value / At Risk",
    2: "Potential Loyalists",
    3: "Champions"
}

rfm['Segment'] = rfm['Cluster'].map(cluster_map)

# Save clustered data
rfm.to_csv("rfm_segmented.csv", index=False)

# Plotting the clusters
plt.figure(figsize=(10, 6))
sns.scatterplot(data=rfm, x='Recency', y='Monetary', hue='Segment', palette='Set2')
plt.title('Customer Segments by RFM Clustering')
plt.legend(title='Segment')
plt.tight_layout()
plt.savefig("rfm_cluster_plot.png")
plt.show()
