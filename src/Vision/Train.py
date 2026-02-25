import cv2
import numpy as np
import os
import joblib
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# ==========================================
# 1. Configuration Area
# ==========================================
# Root directory for preprocessed dataset
# Expected structure: origindataset/black, origindataset/empty, origindataset/white
DATASET_DIR = "origindataset"

# HOG Parameters (Must match preprocessing dimensions: 64x128)
WIN_SIZE = (64, 128)
BLOCK_SIZE = (16, 16)
BLOCK_STRIDE = (8, 8)
CELL_SIZE = (8, 8)
NBINS = 9

# Initialize HOG Descriptor
hog = cv2.HOGDescriptor(WIN_SIZE, BLOCK_SIZE, BLOCK_STRIDE, CELL_SIZE, NBINS)

# ==========================================
# 2. Feature Extraction Function
# ==========================================
def extract_hog_features(data_dir):
    features = []
    labels = []
    # Label mapping: empty=0, black=1, white=2
    label_map = {'empty': 0, 'black': 1, 'white': 2}

    print("Starting HOG feature extraction from folders...")

    for category, label_id in label_map.items():
        cat_path = os.path.join(data_dir, category)
        if not os.path.exists(cat_path):
            print(f"Warning: Folder {cat_path} not found. Skipping category.")
            continue

        print(f"  Processing category: {category} (ID: {label_id})")

        for img_name in os.listdir(cat_path):
            if img_name.lower().endswith(('.jpg', '.png', '.jpeg')):
                img_path = os.path.join(cat_path, img_name)

                # Read image as grayscale
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue

                # Force resize check to ensure 64x128 consistency
                if img.shape[1] != WIN_SIZE[0] or img.shape[0] != WIN_SIZE[1]:
                    img = cv2.resize(img, WIN_SIZE)

                # Compute HOG descriptor
                descriptor = hog.compute(img)
                if descriptor is not None:
                    features.append(descriptor.flatten())
                    labels.append(label_id)

    return np.array(features), np.array(labels), label_map

# ==========================================
# 3. Main Training Routine
# ==========================================
def main():
    # 1. Load data and extract features
    X, y, label_map = extract_hog_features(DATASET_DIR)

    if len(X) == 0:
        print("Error: No valid features extracted. Please check dataset path and images.")
        return

    # 2. Split into training and testing sets (80% Train, 20% Test)
    # Stratify=y ensures proportional representation of classes in both sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nFeature extraction complete. Total samples: {len(X)}")
    print(f"Training set size: {len(X_train)}, Testing set size: {len(X_test)}")

    # 3. Train Linear SVM
    # C=1.0 is the penalty parameter
    # probability=True allows us to get confidence scores during inference
    # class_weight='balanced' addresses the imbalance (1000 empty vs 100 piece samples)
    print("\nInitializing SVM Training (Linear Kernel)...")
    clf = SVC(kernel='linear', C=1.0, probability=True, class_weight='balanced', random_state=42)
    clf.fit(X_train, y_train)

    # 4. Evaluate Model
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("\n--- Training Finished ---")
    print(f"Model Overall Accuracy: {acc:.2%}")
    print("\nDetailed Classification Report:")
    target_names = [name for name, _ in sorted(label_map.items(), key=lambda x: x[1])]
    print(classification_report(y_test, y_pred, target_names=target_names))

    # 5. Save Model Data
    # We save the model, the label mapping, and HOG parameters for easy inference later
    model_data = {
        'svm_model': clf,
        'label_map': {v: k for k, v in label_map.items()}, # Reverse map ID -> Category Name
        'hog_params': {
            'winSize': WIN_SIZE,
            'blockSize': BLOCK_SIZE,
            'blockStride': BLOCK_STRIDE,
            'cellSize': CELL_SIZE,
            'nbins': NBINS
        }
    }

    save_path = "chess_model.pkl"
    joblib.dump(model_data, save_path)
    print(f"\nModel successfully saved to: {save_path}")

if __name__ == "__main__":
    main()
