import streamlit as st
import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# Load your trained model and scaler
kmeans = joblib.load("kmeans_rfm_model.pkl")
scaler = joblib.load("rfm_scaler.pkl")

# Dummy product embeddings (for demo)
# Replace this with your actual product-user matrix or embeddings
product_embeddings = pd.read_csv("product_embeddings.csv", index_col=0)  # Should contain product names

# Cluster Labels
cluster_map = {
    0: "High-Value",
    1: "Regular",
    2: "Occasional",
    3: "At-Risk"
}

# Sidebar navigation
st.sidebar.title("🏠 Navigation")
page = st.sidebar.radio("Go to", ["Clustering", "Recommendation"])

# ---------------------------- #
#        Clustering Page       #
# ---------------------------- #
if page == "Clustering":
    st.title("🧠 Customer Segmentation")

    recency = st.number_input("Recency (days since last purchase)", min_value=0, step=1)
    frequency = st.number_input("Frequency (number of purchases)", min_value=0, step=1)
    monetary = st.number_input("Monetary (total spend)", min_value=0.0, step=10.0, format="%.2f")

    if st.button("Predict Segment", type="primary"):
        input_data = pd.DataFrame([[recency, frequency, monetary]], columns=["Recency", "Frequency", "Monetary"])
        scaled_input = scaler.transform(input_data)
        cluster = kmeans.predict(scaled_input)[0]
        segment = cluster_map.get(cluster, "Unknown")

        st.markdown(f"### 🏷️ Predicted Cluster: `{cluster}`")
        st.success(f"This customer belongs to: **{segment}**")

# ---------------------------- #
#      Recommendation Page     #
# ---------------------------- #
elif page == "Recommendation":
    st.title("🛍️ Product Recommender")

    product_name = st.text_input("Enter Product Name")

    if st.button("Recommend", type="primary"):
        if product_name in product_embeddings.index:
            similarity_matrix = cosine_similarity(
                [product_embeddings.loc[product_name]],
                product_embeddings
            )
            similar_indices = similarity_matrix[0].argsort()[-6:][::-1]  # Top 5 excluding itself
            recommended = product_embeddings.index[similar_indices]

            st.markdown("### 🔄 Recommended Products:")
            for prod in recommended:
                if prod != product_name:
                    st.markdown(f"- {prod}")
        else:
            st.warning("⚠️ Product not found in database. Try another.")

# ---------------------------- #
#         Footer Style         #
# ---------------------------- #
st.markdown("---")
st.caption("🔧 Built with Streamlit | 📊 By Your Name")
