import os
import sys
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import json

# Add parent dir to path so we can import core/detectors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detectors.website_phishing.feature_extractor import WebsiteFeatureExtractor

def train_model():
    dataset_path = 'data/phishing_dataset/dataset.csv'
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        print("Please place a CSV file with columns 'url' and 'label' at data/phishing_dataset/dataset.csv")
        print("Format: label 0 = legit, label 1 = phishing")
        return
        
    print(f"Loading dataset from {dataset_path}...")
    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        print(f"Failed to read CSV: {e}")
        return
        
    if 'url' not in df.columns or 'label' not in df.columns:
        print("Error: CSV must contain 'url' and 'label' columns.")
        return
        
    print(f"Extracting features for {len(df)} URLs...")
    extractor = WebsiteFeatureExtractor()
    
    X_raw = []
    y = []
    
    for idx, row in df.iterrows():
        url = row['url']
        label = row['label']
        if pd.isna(url) or pd.isna(label):
            continue
            
        try:
            features = extractor.get_feature_vector(url)[0]
            X_raw.append(features)
            y.append(int(label))
        except Exception as e:
            print(f"Failed to extract features for {url}: {e}")
            
    if len(X_raw) == 0:
        print("Error: No valid features extracted.")
        return
        
    X_train, X_test, y_train, y_test = train_test_split(X_raw, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Training RandomForest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    print("\n--- Evaluation Metrics ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"Confusion Matrix: {cm}")
    
    os.makedirs('weights', exist_ok=True)
    joblib.dump(model, 'weights/website_model.pkl')
    joblib.dump(scaler, 'weights/website_scaler.pkl')
    
    metadata = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm,
        "model_type": "RandomForestClassifier",
        "features_used": [
            'url_length', 'domain_length', 'number_of_dots', 'number_of_hyphens', 
            'number_of_digits', 'has_https', 'has_ip_address', 'has_at_symbol', 
            'suspicious_keywords_count', 'brand_impersonation_score', 'tld_risk', 
            'subdomain_depth', 'entropy_score', 'path_length', 'query_length', 'punycode_detected'
        ]
    }
    
    with open('weights/website_model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print("\nModels and metadata saved successfully to weights/.")

if __name__ == "__main__":
    train_model()
