---
# **[Pattern] Transfer Learning Patterns – Reference Guide**

---

## **Overview**
Transfer Learning Patterns enable pre-trained models or learned representations to accelerate training, improve performance, or adapt to new tasks with minimal data. This pattern is particularly valuable in scenarios where labeled data is scarce, computational resources are limited, or domain-specific datasets require fine-tuning. By leveraging existing models trained on large-scale datasets (e.g., ImageNet, BERT), you can achieve higher accuracy faster than training from scratch. This guide covers core concepts, implementation strategies, and practical use cases for transfer learning in machine learning (ML) and deep learning (DL) workflows.

---

## **Core Concepts**
### **1. Key Terminology**
| Term                     | Definition                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| **Pre-trained Model**    | A model trained on a large dataset (e.g., VGG16, ResNet, BERT) and reused for another task. |
| **Feature Extraction**   | Using pre-trained layers (e.g., convolutional layers in CNNs) as fixed feature extractors for a new task. |
| **Fine-Tuning**          | Adjusting pre-trained weights (via backpropagation) to adapt to a new dataset. |
| **Frozen Layers**        | Layers whose weights are not updated during training (e.g., early CNN layers). |
| **Representation Learning** | Learning generic features (e.g., edges, text embeddings) that generalize across tasks. |

---

## **Schema Reference**
### **Transfer Learning Workflow**
| Step               | Inputs                                      | Outputs                                      | Tools/Libraries               |
|--------------------|---------------------------------------------|----------------------------------------------|-------------------------------|
| **Select Model**   | Task type (vision, NLP, tabular), dataset size | Pre-trained model (e.g., ResNet50, BERT)     | Hugging Face, TensorFlow Hub   |
| **Preprocess Data**| Raw data (images, text, etc.)               | Standardized inputs (e.g., resized images)   | OpenCV, NLTK, PyTorch         |
| **Feature Extraction** | Pre-trained model, new dataset             | Extracted features (e.g., embeddings)       | Keras, PyTorch                |
| **Train New Head**  | Extracted features + task-specific labels   | Custom classifier/regressor (e.g., Dense layer)| TensorFlow, PyTorch           |
| **Fine-Tuning**     | Model with frozen/unfrozen layers          | Adjusted weights for domain-specific data    | Adam, SGD optimizers          |
| **Evaluate**        | Test data                                   | Metrics (accuracy, F1, loss)                | Scikit-learn, MLflow          |

---

## **Implementation Patterns**
### **1. Feature Extraction**
**Purpose**: Reuse pre-trained layers as fixed feature extractors.
**Steps**:
1. Load a pre-trained model (e.g., `ResNet50.weights_imagenet`).
2. Freeze all layers (`model.trainable = False`).
3. Add a custom classification head (e.g., `Dense(1024, activation='relu')`).
4. Train only the new layers.

**Example (Keras)**:
```python
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model

# Load pre-trained model (weights frozen)
base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Add new head
x = GlobalAveragePooling2D()(base_model.output)
predictions = Dense(10, activation='softmax')(x)
model = Model(inputs=base_model.input, outputs=predictions)

# Freeze base layers
base_model.trainable = False
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
```

---

### **2. Partial Fine-Tuning**
**Purpose**: Unfreeze and fine-tune some layers (e.g., last *N* layers) for domain adaptation.
**Steps**:
1. Start with a feature-extraction model.
2. Unfreeze specific layers (e.g., `base_model.trainable = True`).
3. Use a lower learning rate (e.g., `1e-5`) to avoid catastrophic forgetting.

**Example (PyTorch)**:
```python
import torch
from torchvision import models

model = models.resnet50(pretrained=True)
for param in model.parameters():
    param.requires_grad = False  # Freeze all

# Unfreeze last 3 blocks
for param in model.layer4.parameters():
    param.requires_grad = True

# Optimizer with low LR for fine-tuning
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)
```

---

### **3. Full Fine-Tuning**
**Purpose**: Adjust all layers for a new task with sufficient data.
**Steps**:
1. Load the pre-trained model.
2. Retrain all layers from scratch (or continue from a checkpoint).
3. Use a higher learning rate (e.g., `1e-3`).

**Example (TensorFlow)**:
```python
model = ResNet50(weights='imagenet')
model.trainable = True  # Unfreeze all layers
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(train_data, epochs=10)
```

---

### **4. Domain-Specific Adaptation**
**Purpose**: Adapt pre-trained models to a new domain (e.g., medical imaging).
**Strategies**:
- **Layer-wise Learning Rate Decay**: Gradually unfreeze layers.
- **Data Augmentation**: Use synthetic samples (e.g., rotations, flips) to mitigate domain shift.
- **Progressive Resizing**: Start with larger images, then resize for efficiency.

---

## **Query Examples**
### **1. How do I select a pre-trained model for my task?**
- **Vision**: Use CNNs like `ResNet`, `EfficientNet`, or `MobileNet` for images.
- **NLP**: Use `BERT`, `RoBERTa`, or `DistilBERT` for text.
- **Tabular**: Use tabular-specific models like `TabNet` or feature embeddings from pre-trained transformers.
- **Guideline**: Larger models (e.g., BERT-large) generalize better but require more data.

### **2. When should I use feature extraction vs. fine-tuning?**
| Scenario                          | Recommended Approach       |
|-----------------------------------|----------------------------|
| Small dataset (<1,000 samples)    | Feature extraction         |
| Medium dataset (1K–10K samples)   | Partial fine-tuning        |
| Large dataset (>10K samples)      | Full fine-tuning           |
| Domain shift (e.g., medical → natural) | Progressive unfreezing |

### **3. How do I handle class imbalance in transfer learning?**
- Use **class weights** in the loss function:
  ```python
  class_weights = {0: 1., 1: 2., 2: 3.}  # Adjust based on class frequencies
  model.fit(train_data, class_weight=class_weights)
  ```
- Apply **oversampling/undersampling** for minority/majority classes.

### **4. What’s the impact of freezing vs. unfreezing layers?**
| Action               | Pros                                      | Cons                                  |
|----------------------|-------------------------------------------|---------------------------------------|
| **Freeze all layers** | Fast training, avoids overfitting        | Limited adaptability                 |
| **Unfreeze some**    | Better domain adaptation                 | Risk of overfitting                   |
| **Unfreeze all**     | Full model customization                 | Computationally expensive, needs data |

---

## **Best Practices**
1. **Start with Feature Extraction**: Validate performance before fine-tuning.
2. **Monitor Overfitting**: Use validation sets and early stopping.
3. **Leverage Low-Rank Adapters**: Add small linear layers (e.g., `AdapterTransformers`) for efficient fine-tuning.
4. **Leverage Mixed Precision**: Use `FP16` training (e.g., `torch.cuda.amp`) to speed up fine-tuning.
5. **Document Hyperparameters**: Track learning rates, batch sizes, and unfreezing schedules.

---

## **Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **[Fine-Tuning] Hyperparameter Optimization** | Tune learning rates, batch sizes, and unfreezing schedules for transfer learning. |
| **[Data Augmentation]**     | Generate synthetic data to improve generalization when fine-tuning.       |
| **[Model Distillation]**    | Train a smaller model to mimic a pre-trained one (e.g., distilling BERT). |
| **[Ensemble Methods]**      | Combine multiple pre-trained models (e.g., bagging or boosting).         |
| **[Quantization]**          | Reduce model size post-fine-tuning for deployment efficiency.              |

---

## **Tools & Resources**
| Tool/Library          | Purpose                                      |
|-----------------------|-----------------------------------------------|
| TensorFlow Hub        | Access to pre-trained models (e.g., `keras_cv`). |
| Hugging Face          | Pre-trained NLP models (e.g., `transformers`). |
| PyTorch TorchVision   | Pre-trained CNNs and utilities.                |
| Weights & Biases      | Track experiments with transfer learning.      |
| FastAI                 | High-level APIs for transfer learning.         |

---
**Note**: Adjust learning rates and unfreezing strategies based on your dataset size and task complexity. For cutting-edge approaches, explore **Vision Transformers (ViT)** or **Multimodal Transfer Learning** (e.g., CLIP).