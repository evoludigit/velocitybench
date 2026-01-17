# **[Pattern] Feature Engineering Patterns – Reference Guide**

---

## **Overview**
Feature Engineering Patterns standardize techniques to transform raw data into meaningful input variables (features) that improve predictive model performance. This guide covers **14 proven patterns** (e.g., binning, categorization, encoding, transformation) with implementation details, use cases, and anti-patterns. Patterns are categorized by **data type** (numeric, categorical, text) and **purpose** (scaling, normalization, dimensionality reduction). Use this reference to systematically apply feature engineering in machine learning workflows.

---

## **1. Pattern Schema Reference**

| **Pattern Name**               | **Data Type**       | **Purpose**                          | **Key Parameters**                          | **Output Type**       | **Common Libraries**          |
|--------------------------------|---------------------|---------------------------------------|---------------------------------------------|-----------------------|--------------------------------|
| **Binning**                    | Numeric             | Discretize continuous data            | `n_bins`, `method` (equal-width/equal-freq) | Categorical            | `pandas.cut`, `sklearn.preprocessing.KBinsDiscretizer` |
| **Categorical Encoding**       | Categorical         | Convert labels to numerical values    | `encoding_type` (one-hot, label, target)    | Numeric/Categorical    | `sklearn.preprocessing.OneHotEncoder`, `scikit-learn.LabelEncoder` |
| **Sparse Encoding**            | Categorical         | Handle high-cardinality features      | `handle_unknown='ignore'`                   | Sparse Matrix         | `sklearn.feature_extraction.DictVectorizer` |
| **Polynomial Features**        | Numeric             | Capture non-linear relationships      | `degree=2`, `include_bias=True`             | Numeric               | `sklearn.preprocessing.PolynomialFeatures` |
| **Interaction Features**       | Numeric             | Model feature combinations            | `degree=2`, `interaction_only=True`         | Numeric               | Manual (feature-crossing)     |
| **Scaling (Standardization)**  | Numeric             | Normalize to zero mean, unit variance | N/A                                       | Numeric               | `sklearn.preprocessing.StandardScaler` |
| **Scaling (Min-Max)**          | Numeric             | Constrain to [0, 1] or [-1, 1]        | `feature_range=(0, 1)`                     | Numeric               | `sklearn.preprocessing.MinMaxScaler` |
| **Log/Exponential Transformation** | Numeric | Handle skewness/outliers            | `base=10`, `clip=True`                     | Numeric               | `numpy.log1p`, `sklearn.preprocessing.PowerTransformer` |
| **Outlier Handling**           | Numeric             | Remove/impute extreme values          | `strategy` ('clip', 'winzorize', 'remove')  | Numeric               | `sklearn.preprocessing.RobustScaler` |
| **Text Vectorization**         | Text                | Convert text to numerical features    | `ngram_range=(1, 2)`, `min_df=5`            | Sparse Matrix         | `sklearn.feature_extraction.TfidfVectorizer` |
| **Text Embeddings**            | Text                | Represent text in dense vectors       | `model='sentence-transformers'`            | Dense Vector          | `sentence-transformers`, `gensim` |
| **Dimensionality Reduction**   | Mixed               | Reduce feature space complexity        | `n_components=10`, `method='PCA'`           | Numeric               | `sklearn.decomposition.PCA`, `UMAP` |
| **Feature Selection**          | Mixed               | Select top-relevant features          | `selection_type` ('variance', 'correlation') | Subset of Features    | `sklearn.feature_selection.SelectKBest` |
| **Feature Aggregation**        | Mixed               | Combine multiple features             | `func='mean'`, `columns=['col1', 'col2']`  | Single Feature         | `pandas.groupby().agg()`      |
| **Time-Based Feature Engineering** | Numeric/Temporal | Extract temporal patterns           | `time_window='hourly'`, `lag=1`             | Numeric/Categorical   | `pandas.dt.accessors`         |

---

## **2. Implementation Details**

### **2.1 Common Parameters Across Patterns**
- **`handle_unknown`**: How to treat unseen categories (e.g., `'ignore'`, `'error'`).
- **`drop='first'`**: For categorical encoding to avoid multicollinearity.
- **`random_state`**: For reproducibility in transformations like PCA.

### **2.2 Anti-Patterns to Avoid**
- **Overfitting**: Avoid excessive binning (e.g., >10 bins) without validation.
- **Data Leakage**: Never use target data (e.g., `y`) to create features (e.g., `Log(y)`).
- **Ignoring Distributions**: Assume all numeric features need scaling equally (e.g., age vs. GDP).

---

## **3. Query Examples**

### **3.1 Binning Example (Discretize Age)**
```python
import pandas as pd

# Raw data
df['age'] = pd.cut(df['age'],
                   bins=[0, 18, 35, 60, 100],
                   labels=['child', 'adult', 'senior', 'elderly'])
```

### **3.2 Polynomial Features (Capture Non-Linearity)**
```python
from sklearn.preprocessing import PolynomialFeatures

poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(df[['feature1', 'feature2']])
```

### **3.3 Text Vectorization (TF-IDF)**
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=5)
X_tfidf = vectorizer.fit_transform(df['text_column'])
```

### **3.4 Time-Based Aggregation (Daily Sales)**
```python
df.set_index('date').resample('D').sum().reset_index()
```

---

## **4. Related Patterns**
- **[Data Cleaning Patterns]**: Preprocessing (missing values, duplicates) before feature engineering.
- **[Model Evaluation Patterns]**: Assess impact of feature engineering on model metrics (e.g., AUC, RMSE).
- **[Pipeline Integration]**: Combine feature engineering with training (e.g., `ColumnTransformer`, `Pipeline`).
- **[Feature Store Patterns]**: Reuse engineered features across projects (e.g., Feast, Tecton).
- **[Model Interpretability]**: Use SHAP/LIME to validate feature importance post-engineering.

---

## **5. Best Practices**
1. **Document Justifications**: Record why a pattern was chosen (e.g., "Used log transform due to skewness in `revenue`").
2. **Version Control**: Track feature definitions in code (e.g., `feature_definitions.json`).
3. **Monitor Drift**: Retrain features if distribution shifts (e.g., `Kolmogorov-Smirnov test`).
4. **Collaborate**: Share feature taxonomies with cross-functional teams (e.g., SQL tables → ML features).

---
**Length**: ~1,000 words | **Last Updated**: [Insert Date]