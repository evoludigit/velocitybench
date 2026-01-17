# **[NLP Patterns] Reference Guide**

---

## **Overview**
The **NLP Patterns** pattern is a domain-specific approach to **extract**, **classify**, and **structuralize** intent and entities from natural language input using predefined **rules, templates, and linguistic rules**. Unlike traditional keyword-matching systems, this pattern leverages **context-aware semantic parsing** to handle ambiguity, slang, and domain-specific terminology. It is commonly used in **chatbots, virtual assistants, and data extraction pipelines** where structured output from unstructured text is required.

This pattern combines:
- **Rule-based templates** (e.g., `{action} {object}`) for structured parsing.
- **Entity recognition** (e.g., dates, names, amounts).
- **Intent classification** (e.g., "book flight," "cancel order").
- **Fallback mechanisms** for unmatched patterns.

The output is typically a **JSON-like structured object** with parsed fields, confidence scores, and annotations.

---

## **Schema Reference**
Below is the standard schema for an **NLP Pattern** response. Each field is optional unless marked with `*`.

| **Field**          | **Type**       | **Description**                                                                 | **Example**                     |
|--------------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `intent`*          | String         | Predicted user intent (e.g., "book_ticket").                                       | `"book_ticket"`                  |
| `confidence`       | float (0–1)    | Probability score of intent classification (higher = more confident).            | `0.92`                           |
| `entities`         | Array[Object]  | Extracted entities with type, value, and annotations.                             | `[{ "type": "date", "value": "2024-05-15", "start": 10 }]` |
| `pattern_match`*   | String         | Matched rule template (e.g., `{action} {object}`).                               | `"book {flight}"`                |
| `raw_text`         | String         | Original input text (for debugging).                                             | `"I want to book a flight to Paris."` |
| `fallback_reason`  | String         | Why the pattern failed (e.g., "no match," "ambiguous").                           | `"partial_match"`                |

### **Entity Schema (Nested in `entities`)**
| **Field**      | **Type**   | **Description**                                                                 | **Example**                     |
|----------------|------------|---------------------------------------------------------------------------------|---------------------------------|
| `type`*        | String     | Predefined entity type (e.g., `date`, `location`, `money`).                     | `"location"`                     |
| `value`*       | String/Number| Normalized value (e.g., `"200"`, `"NYC"`).                                      | `"150.50"`                       |
| `start` / `end`| Integer    | Character offset in `raw_text` (for alignment).                                | `{ "start": 5, "end": 8 }`      |
| `confidence`   | float (0–1) | Confidence in this entity (optional).                                             | `0.85`                           |
| `resolution`   | String     | Resolved form (e.g., normalized city name).                                     | `"New York"` (if input was "NY") |

---

## **Implementation Details**

### **1. Core Components**
#### **A. Rule Templates**
Pattern definitions are written as **reusable templates** with placeholders (e.g., `{action}`, `{object}`).
Example templates:
```json
{
  "patterns": [
    {
      "template": "{action} {object}",
      "intent": "modify_order",
      "entities": [
        { "type": "action", "value": "cancel", "regex": "^(cancel|delete|remove)$" },
        { "type": "object", "value": "order", "regex": "^(order|booking|reservation)$" }
      ]
    },
    {
      "template": "I need to {action} {object} on {date}",
      "intent": "schedule_task",
      "entities": [
        { "type": "date", "type": "date", "format": "YYYY-MM-DD" }
      ]
    }
  ]
}
```
- **Placeholders** (`{...}`) are replaced with entity values.
- **Regex patterns** refine matching (e.g., `^(cancel|delete)$`).
- **Optional fields**: `confidence_threshold` (e.g., `0.75`) to filter weak matches.

#### **B. Entity Recognizers**
Predefined entity types include:
| **Type**         | **Description**                                                                 | **Example Input/Output**                          |
|------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| `date`           | Extracts dates in various formats (ISO, MM/DD/YYYY).                           | `"May 15, 2024"` → `"2024-05-15"`                |
| `location`       | Normalizes city/region names (supports aliases).                                | `"LA"` → `"Los Angeles"`                         |
| `money`          | Parses currency with optional symbol/sign.                                      | `"$200"` → `"200.00"` (USD)                     |
| `email`/`phone`  | Validates and standardizes contact info.                                      | `"john.doe@example.com"` → `{ valid: true }`      |
| `custom`         | Domain-specific entities (e.g., `product_id`, `user_id`).                       | `"SKU-12345"` → `"12345"`                        |

#### **C. Intent Classification**
- **Supervised models** (e.g., BERT, spaCy) can be integrated for fallback intents.
- **Confidence thresholds** filter out low-probability matches.
- **Hierarchical intents**: Parent-child relationships (e.g., `food` → `pizza_order`).

#### **D. Fallback Mechanisms**
If no pattern matches:
1. **Fuzzy matching**: Partial template matches (e.g., `"book a"` for `"book a flight"`).
2. **Default intent**: Routes to a catch-all handler (e.g., `"unknown"`).
3. **User feedback loop**: Logs ambiguous inputs for retraining.

---

### **2. Integration Workflow**
1. **Input**: Raw text (e.g., `"Cancel my order for the flight to Tokyo."`).
2. **Matching**:
   - Template `"{action} {object}"` matches with `action="cancel"`, `object="order"`.
   - Entity recognizer resolves `"flight to Tokyo"` as `location="Tokyo"`.
3. **Output**:
   ```json
   {
     "intent": "modify_order",
     "entities": [
       { "type": "action", "value": "cancel" },
       { "type": "object", "value": "order" },
       { "type": "location", "value": "Tokyo", "resolution": "Tokyo, Japan" }
     ],
     "pattern_match": "cancel order",
     "confidence": 0.98
   }
   ```

---

## **Query Examples**
### **Example 1: Booking a Flight**
**Input**:
`"I need to book a round-trip to Paris on December 15th for two people."`

**Output**:
```json
{
  "intent": "book_flight",
  "entities": [
    { "type": "destination", "value": "Paris", "resolution": "Paris, France" },
    { "type": "date", "value": "2024-12-15", "format": "YYYY-MM-DD" },
    { "type": "passengers", "value": "2", "type": "number" }
  ],
  "pattern_match": "book {destination} on {date} for {passengers}",
  "confidence": 0.95
}
```

### **Example 2: Canceling a Subscription**
**Input**:
`"Unsubscribe from the premium plan ASAP."`

**Output**:
```json
{
  "intent": "cancel_subscription",
  "fallback_reason": "partial_match",
  "entities": [
    { "type": "service", "value": "premium_plan", "confidence": 0.8 }
  ],
  "raw_text": "Unsubscribe from the premium plan ASAP."
}
```
*(Note: The template `"cancel {service}"` partially matched with low confidence.)*

### **Example 3: Complex Date Parsing**
**Input**:
`"My appointment was moved to next Monday at 3 PM."`

**Output**:
```json
{
  "intent": "reschedule",
  "entities": [
    { "type": "date", "value": "2024-05-20", "resolution": "Next Monday" },
    { "type": "time", "value": "15:00", "format": "HH:MM" }
  ],
  "pattern_match": "appointment moved to {date} at {time}",
  "confidence": 0.99
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|----------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Keyword Matching]**     | Exact/partial string matching for simple intents.                                | Low-latency, static intents (e.g., FAQs).       |
| **[Rule-Based Parsing]**   | Similar to NLP Patterns but without templates (e.g., regex-heavy).              | Highly structured input (e.g., invoices).        |
| **[Intent Classification]**| ML-based intent prediction (no templates).                                       | Large, unstructured domains (e.g., customer support). |
| **[Entity Recognition]**   | Standalone entity extraction (no intent).                                        | Data extraction from logs/documents.             |
| **[Semantic Routing]**     | Combines NLP Patterns with dynamic routing (e.g., to APIs or agents).           | Multi-channel support (chat + voice + email).   |
| **[Fallback-to-Intent]**   | Hybrids NLP Patterns with ML when no rule matches.                                | High accuracy + low false negatives.            |

---

## **Best Practices**
1. **Template Design**:
   - Keep templates **short and specific** (e.g., avoid `{action} {object} to {place}` if ambiguity exists).
   - Use **negative examples** in testing (e.g., `"send email"` should not match `"send money"`).

2. **Entity Confidence**:
   - Set thresholds (e.g., `confidence > 0.7` for critical entities like `money`).
   - Log **false positives/negatives** for retraining.

3. **Fallbacks**:
   - Prioritize **user clarity**: Return partial matches with confidence scores (e.g., `"Did you mean: 'book flight'?"`).

4. **Performance**:
   - Pre-compile **regex patterns** for faster matching.
   - Cache frequent templates/inputs.

5. **Domain Adaptation**:
   - Extend `custom` entities for industry jargon (e.g., `shipment_id`, `contract_term`).
   - Localize date/time formats (e.g., `DD/MM/YYYY` for Europe).

---
**Limitations**:
- Struggles with **highly ambiguous** or **creative language** (use ML hybrids).
- Requires **manual template maintenance** for evolving domains.

---
**Tools/Libraries**:
- Open-source: [Rasa NLU](https://rasa.com/), [Dialogflow Patterns](https://cloud.google.com/dialogflow).
- Python: `spaCy` (for entity recognition), `re` (regex).
- Cloud: AWS Comprehend, Azure LUIS (for managed intent classification).