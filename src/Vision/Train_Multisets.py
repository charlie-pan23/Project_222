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
# Root directory for dataset
# Ensure your folder structure is: dataset/black, dataset/empty_black, etc.
DATASET_DIR = "dataset"

# HOG Parameters (Standard for 64x128 input)
# These must remain consistent between Training and Inference
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

    # Updated Label Map: 8 Distinct Classes
    # We keep them separate during training to allow the SVM to find
    # the best hyperplane for each specific texture/lighting condition.
    label_map = {
        # Black Piece Faction
        'black': 0,
        'black_corner': 1,

        # White Piece Faction
        'white': 2,
        'white_corner': 3,
        'white_shadow': 4,

        # Empty Square Faction (The new additions)
        'empty_black': 5,
        'empty_white': 6,
        'empty_corner': 7
    }

    print(f"Starting HOG feature extraction from {data_dir}...")
    print(f"Target Classes: {list(label_map.keys())}")

    for category, label_id in label_map.items():
        cat_path = os.path.join(data_dir, category)

        # Safety check if folder exists
        if not os.path.exists(cat_path):
            print(f"Warning: Folder '{category}' not found. Skipping.")
            continue

        files = [f for f in os.listdir(cat_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        count = len(files)
        print(f"  Processing {category:<15} (ID: {label_id}): Found {count} images.")

        for img_name in files:
            img_path = os.path.join(cat_path, img_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

            if img is None:
                continue

            # Resize to fixed dimensions (Critical for HOG)
            if img.shape[1] != WIN_SIZE[0] or img.shape[0] != WIN_SIZE[1]:
                img = cv2.resize(img, WIN_SIZE)

            # Compute HOG features
            descriptor = hog.compute(img)

            if descriptor is not None:
                features.append(descriptor.flatten())
                labels.append(label_id)

    return np.array(features), np.array(labels), label_map

# ==========================================
# 3. Main Training Routine
# ==========================================
def main():
    # 1. Extract Features
    X, y, label_map = extract_hog_features(DATASET_DIR)

    if len(X) == 0:
        print("Error: No features extracted. Please check your dataset structure.")
        return

    # 2. Split Data (90% Train, 10% Test)
    # stratify=y ensures we have a balanced representation of all 8 classes in the test set
    print("\nSplitting data into Training and Testing sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )

    print(f"Training Samples: {len(X_train)} | Testing Samples: {len(X_test)}")

    # 3. Train SVM
    # probability=True is ESSENTIAL for the 'summation' logic later
    # class_weight='balanced' automatically handles if you have 500 empty squares but only 100 pieces
    print("\nTraining Multi-class SVM (Linear Kernel)... this may take a moment.")
    clf = SVC(kernel='linear', C=1.0, probability=True, class_weight='balanced', random_state=42)
    clf.fit(X_train, y_train)

    # 4. Evaluate
    print("\nEvaluating Model...")
    y_pred = clf.predict(X_test)

    # Generate names for report
    target_names = [name for name, _ in sorted(label_map.items(), key=lambda x: x[1])]

    print("\n--- 8-Class Classification Report ---")
    print(classification_report(y_test, y_pred, target_names=target_names))

    # 5. Save Model
    save_path = "chess_8sets_model.pkl"
    model_data = {
        'svm_model': clf,
        'label_map': {v: k for k, v in label_map.items()}, # Invert map (ID -> Name) for inference
        'hog_params': {
            'winSize': WIN_SIZE,
            'blockSize': BLOCK_SIZE,
            'blockStride': BLOCK_STRIDE,
            'cellSize': CELL_SIZE,
            'nbins': NBINS
        }
    }

    joblib.dump(model_data, save_path)
    print(f"\nModel successfully saved to: {save_path}")
    print("-" * 50)
    print("INFERENCE TIP: The model now outputs 8 probabilities.")
    print("When predicting, sum the probabilities into 3 factions:")
    print("  Score_Black = P(black) + P(black_corner)")
    print("  Score_White = P(white) + P(white_corner) + P(white_shadow)")
    print("  Score_Empty = P(empty_black) + P(empty_white) + P(empty_corner)")
    print("Then choose the faction with the highest score.")
    print("-" * 50)

if __name__ == "__main__":
    main()
