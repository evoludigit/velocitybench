---

# **[Sentiment Analysis Patterns] Reference Guide**

---

## **Overview**
Sentiment Analysis Patterns are structured approaches to classifying, analyzing, and extracting **polarity (positive/negative/neutral)** and **sentiment intensity** from text data (e.g., customer reviews, social media, feedback forms). This pattern enables organizations to automate emotion-driven decision-making, such as improving product development, detecting public opinion trends, or optimizing customer service responses.

Key applications include:
- **NLP pipelines** (e.g., pre-processing text before classification)
- **Real-time monitoring** (e.g., social media sentiment tracking)
- **Automated sentiment scoring** (e.g., assigning star ratings to reviews)
- **Aspect-based sentiment analysis** (e.g., extracting sentiment for specific product features).

This guide covers foundational concepts, implementation schemas, example queries, and related patterns for building scalable sentiment analysis systems.

---

## **Implementation Details**

### **1. Core Components**
| **Component**               | **Description**                                                                                     | **Tools/Techniques**                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Text Preprocessing**       | Cleaning and normalizing text (tokenization, stopword removal, lemmatization) to improve accuracy.  | NLTK, spaCy, TextBlob                                                               |
| **Sentiment Lexicons**       | Dictionaries mapping words/phrases to sentiment scores (e.g., VADER, AFINN, SentiWordNet).         | Custom lexicons or open-source libraries                                            |
| **Machine Learning Models**  | Supervised (e.g., Naive Bayes, SVM) or unsupervised (e.g., Word2Vec, BERT) models trained on labeled data. | Hugging Face Transformers, scikit-learn, TensorFlow/PyTorch                          |
| **Aspect Extraction**        | Identifying key entities/features (e.g., "battery life" in a phone review) for granular analysis.   | Rule-based (regex) or ML-based (e.g., BERTopic)                                     |
| **Aggregation & Visualization** | Consolidating sentiment scores and generating dashboards/alerts for stakeholders.               | Pandas, Matplotlib/Seaborn, Tableau/Power BI                                         |
| **Real-Time Processing**     | Streaming sentiment analysis for live data (e.g., Twitter feeds, chat logs).                     | Apache Kafka, Spark Streaming, AWS Lambda                                          |

---

### **2. Schema Reference**
The following table outlines the primary data structures used in sentiment analysis systems.

| **Schema**               | **Fields**                                                                                     | **Data Type**       | **Description**                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|---------------------|-----------------------------------------------------------------------------------------------------|
| **Text Input**           | `id` (string), `content` (text), `source` (string), `timestamp` (datetime)                   | UUID, str, str,     | Unique identifier, raw text, source platform (e.g., "Amazon"), and submission time.               |
| **Sentiment Output**     | `id` (string), `raw_text` (text), `sentiment` (enum: "POSITIVE/NEUTRAL/NEGATIVE"), `score` (float), `aspects` (list) | UUID, str, enum,    | Processed text, polarity label, confidence score (e.g., -1.0 to 1.0), and extracted aspects (e.g., `[{"feature": "price", "sentiment": "NEGATIVE"}]`). |
| **Aspect Sentiment**     | `id` (string), `feature` (string), `sentiment` (enum), `score` (float)                       | UUID, str, enum,    | Focused sentiment for a specific product/feature (e.g., "camera quality" → "POSITIVE").          |
| **Aggregated Metrics**   | `time_period` (datetime), `total_reviews` (int), `pos_count` (int), `neg_count` (int), `avg_score` (float) | datetime, int, int, | Macroscopic trends (e.g., daily/weekly sentiment summaries).                                       |
| **Model Metadata**       | `model_name` (string), `version` (str), `training_data_size` (int), `accuracy` (float)       | str, str, int, float| Track performance of deployed models for retraining.                                              |

**Example JSON Payload (Input):**
```json
{
  "id": "rev_12345",
  "content": "The product arrived broken, but the customer service was amazing!",
  "source": "ecommerce",
  "timestamp": "2023-10-15T14:30:00Z"
}
```

**Example JSON Payload (Output):**
```json
{
  "id": "rev_12345",
  "raw_text": "The product arrived broken, but the customer service was amazing!",
  "sentiment": "NEUTRAL",
  "score": 0.1,
  "aspects": [
    {"feature": "delivery", "sentiment": "NEGATIVE", "score": -0.8},
    {"feature": "customer_service", "sentiment": "POSITIVE", "score": 0.9}
  ]
}
```

---

## **Query Examples**
Below are SQL-like queries for common analytical tasks (adaptable to APIs or NoSQL databases).

### **1. Basic Sentiment Distribution**
```sql
SELECT
    sentiment,
    COUNT(*) AS review_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sentiment_output), 2) AS percentage
FROM sentiment_output
GROUP BY sentiment
ORDER BY review_count DESC;
```

### **2. Aspect-Based Sentiment by Product**
```sql
SELECT
    aspect.feature,
    aspect.sentiment,
    COUNT(*) AS count,
    AVG(aspect.score) AS avg_score
FROM sentiment_output
JOIN UNNEST(aspects) AS aspect
GROUP BY aspect.feature, aspect.sentiment
ORDER BY avg_score DESC;
```

### **3. Time-Series Sentiment Trend**
```sql
SELECT
    DATE(timestamp) AS day,
    COUNT(*) AS daily_reviews,
    SUM(CASE WHEN sentiment = 'POSITIVE' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) AS negative_count
FROM sentiment_output
WHERE timestamp BETWEEN '2023-09-01' AND '2023-10-15'
GROUP BY day
ORDER BY day;
```

### **4. Model Performance Comparison**
```sql
SELECT
    model_metadata.model_name,
    model_metadata.version,
    COUNT(*) AS reviews_analyzed,
    ROUND(AVG(score_accuracy), 2) AS avg_accuracy
FROM sentiment_output
JOIN model_metadata ON [joining criteria, e.g., model_id]
GROUP BY model_name, version;
```

---

## **Related Patterns**
To extend or integrate sentiment analysis, consider the following complementary patterns:

1. **Text Classification**
   - *Purpose*: Categorize text into predefined classes (e.g., spam, support tickets).
   - *Use Case*: Route sentiment analysis results to specific workflows (e.g., flag negative reviews for escalation).
   - *Tools*: Scikit-learn, spaCy’s `TextCategorizer`.

2. **Topic Modeling**
   - *Purpose*: Discover latent topics in text (e.g., "battery issues," "design flaws").
   - *Use Case*: Combine with sentiment to prioritize feature development.
   - *Tools*: LDA, BERTopic, Non-negative Matrix Factorization (NMF).

3. **Emotion Detection**
   - *Purpose*: Distinguish between sentiment (e.g., "happy," "angry," "sad").
   - *Use Case*: Tailor responses to emotional context (e.g., offer apologies for angry reviews).
   - *Tools*: Emotion lexicons (e.g., NRC Emotion Lexicon), fine-tuned transformers.

4. **Real-Time Analytics**
   - *Purpose*: Process streaming data with low latency.
   - *Use Case*: Monitor social media trends or chatbot interactions in real time.
   - *Tools*: Apache Flink, AWS Kinesis, Spark Structured Streaming.

5. **Explainable AI (XAI)**
   - *Purpose*: Provide transparency into model decisions (e.g., "Why was this review labeled negative?").
   - *Use Case*: Build trust with stakeholders or improve model debuggability.
   - *Tools*: SHAP values, LIME, Captum (PyTorch).

6. **Feedback Loop for Model Improvement**
   - *Purpose*: Continuously retrain models using user corrections (e.g., annotated misclassified reviews).
   - *Use Case*: Maintain high accuracy over time.
   - *Tools*: Active learning frameworks (e.g., Prodigy), MLflow.

---

## **Best Practices**
1. **Data Quality**:
   - Sanitize input text (remove HTML tags, emojis, or non-alphabetic characters if irrelevant).
   - Handle sarcasm and negations (e.g., "not bad" → positive) using rule-based adjustments.

2. **Model Selection**:
   - Start with **rule-based** (lexicon) or **lightweight ML** (e.g., VADER) for prototyping.
   - Use **transformers** (e.g., BERT, RoBERTa) for high-accuracy, domain-specific tasks.

3. **Bias Mitigation**:
   - Audit lexicons/models for gender/racial bias (e.g., "black" vs. "white" in reviews).
   - Diversify training data to represent all demographics.

4. **Scalability**:
   - Deploy models as **microservices** (e.g., FastAPI, Flask) for horizontal scaling.
   - Use **batch processing** (e.g., Airflow) for historical data and **streaming** (e.g., Kafka) for real-time.

5. **Monitoring**:
   - Track **drift** in sentiment patterns (e.g., sudden spikes in negativity).
   - Log **false positives/negatives** for model retraining.

---
**See also**:
- [NLP Pipelines Pattern](link) for end-to-end text processing workflows.
- [Data Versioning Pattern](link) to manage evolving sentiment datasets.