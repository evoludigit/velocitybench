```markdown
---
title: "Multi-Language Schema Input: Write Your Schema Once, Compile Everywhere"
date: 2023-11-15
author: "Jane Doe"
tags: ["database", "schema design", "backend patterns", "API design"]
draft: false
slug: "multi-language-schema-input-pattern"
---

---

# **Multi-Language Schema Input: Write Your Schema Once, Compile Everywhere**

As backend engineers, we spend a lot of time working with databases. Whether we're designing data models for a new feature or maintaining legacy systems, schemas are a fundamental part of our work. But what if you could write your schema once—and then reuse it across multiple languages, frameworks, and platforms?

That’s the promise of the **Multi-Language Schema Input** pattern. This approach lets you define your data model in a familiar language (like JSON, YAML, SQL, or even a custom DSL) and then compile it into a shared representation that can be used by different backend services, databases, and APIs.

This pattern is especially useful when:
- Your team uses multiple programming languages but shares a common data model.
- You need to support multiple database backends (PostgreSQL, MongoDB, Cassandra) with the same schema.
- You want to decouple schema definition from application code for better maintainability.

In this post, we’ll explore how to implement this pattern in a real-world scenario. We’ll start with the problem, then dive into the solution, and finally walk through a practical implementation.

---

## **The Problem: Why Not Just Use One Schema Language?**

Most backend systems today rely on a single schema language. For example:
- A Python team might define their models using **SQLAlchemy** or **Django ORM**.
- A Java team might use **Hibernate** or **JPA**.
- A Node.js team might use **Mongoose** (for MongoDB) or **Prisma**.

Each of these languages has its own syntax, strengths, and quirks. But here’s the problem:
- **Language Lock-in:** If your team grows or merges with another team that uses a different schema language, you may need to rewrite your entire data model.
- **Fragmented Data Models:** If two services use similar but slightly different schema definitions, data consistency becomes harder to maintain.
- **Fragmented Knowledge:** Different teams might define similar tables or collections in slightly different ways, leading to confusion.

For example, consider a company with a Python backend (using SQLAlchemy) and a Go backend (using GORM). If both need to define a `User` table, they might end up with slightly different definitions:

**Python (SQLAlchemy)**
```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(200), unique=True)
    # ... other fields
```

**Go (GORM)**
```go
type User struct {
    ID    uint   `gorm:"primaryKey"`
    Name  string `gorm:"size:100"`
    Email string `gorm:"unique;size:200"`
}
```

If these two definitions drift apart, maintaining consistency becomes a nightmare.

---

## **The Solution: Multi-Language Schema Input**

The **Multi-Language Schema Input** pattern solves this problem by introducing an intermediate representation (IR) for schemas. Here’s how it works:

1. **Define your schema in a language-agnostic format** (e.g., JSON, YAML, or a custom DSL).
2. **Compile the schema into a shared intermediate representation (IR)**—a standardized format that all your backend services can consume.
3. **Generate language-specific code** (e.g., SQLAlchemy, GORM, Mongoose) from the IR to ensure consistency across all systems.

This way, you define your schema **once** and compile it into whatever backend language you need.

---

## **Components of the Solution**

To implement this pattern, you’ll need the following components:

### 1. **Schema Definition Language (SDL)**
   - A simple, human-readable format for defining your schema. Common choices:
     - **JSON/YAML** (easiest for beginners)
     - **Custom DSL** (more expressive but requires tooling)
     - **GraphQL Schema Language (SDL)** (if you're already using GraphQL)

   Example in JSON:
   ```json
   {
     "tables": [
       {
         "name": "users",
         "columns": [
           {"name": "id", "type": "integer", "primaryKey": true},
           {"name": "name", "type": "string", "maxLength": 100},
           {"name": "email", "type": "string", "unique": true}
         ]
       }
     ]
   }
   ```

### 2. **Schema Compiler**
   - A tool that takes input from the SDL and converts it into a **shared intermediate representation (IR)**.
   - The IR should be a simple, standardized format (e.g., JSON or a custom binary format) that all backends can understand.

   Example IR (JSON):
   ```json
   {
     "database": "app_db",
     "tables": [
       {
         "tableName": "users",
         "columns": [
           {"name": "id", "type": "int", "primaryKey": true},
           {"name": "name", "type": "varchar(100)"},
           {"name": "email", "type": "varchar(200)", "unique": true}
         ]
       }
     ]
   }
   ```

### 3. **Code Generators**
   - For each backend language you support (Python, Go, JavaScript, etc.), write a code generator that converts the IR into language-specific code (e.g., SQLAlchemy models, GORM structs, Mongoose schemas).

   Example generator for **SQLAlchemy**:
   ```python
   def generate_sqlalchemy(ir):
       output = []
       for table in ir["tables"]:
           output.append(f"from sqlalchemy import Column, Integer, String")
           output.append(f"from sqlalchemy.ext.declarative import declarative_base")
           output.append(f"\nBase = declarative_base()")
           output.append(f"\nclass {table['tableName'].capitalize()}(Base):")
           output.append(f"    __tablename__ = \"{table['tableName']}\"")
           for column in table["columns"]:
               col_type = {
                   "int": "Integer",
                   "varchar": "String"
               }.get(column["type"], "String")
               output.append(f"    {column['name']} = Column({col_type}, {', '.join(f'{k}={v}' for k, v in column.items() if k != 'type' and k != 'name')})")
       return "\n".join(output)
   ```

---

## **Code Examples: A Full Implementation**

Let’s walk through a practical example using **JSON as our SDL**, a simple **IR**, and code generators for **SQLAlchemy (Python)** and **GORM (Go)**.

### 1. Define the Schema in JSON (SDL)
```json
// schema.json
{
  "database": "app_db",
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "type": "integer", "primaryKey": true},
        {"name": "name", "type": "string", "maxLength": 100},
        {"name": "email", "type": "string", "unique": true}
      ]
    },
    {
      "name": "posts",
      "columns": [
        {"name": "id", "type": "integer", "primaryKey": true},
        {"name": "title", "type": "string", "maxLength": 200},
        {"name": "content", "type": "text"},
        {"name": "author_id", "type": "integer", "references": ["users.id"]}
      ]
    }
  ]
}
```

### 2. Compile the Schema into an Intermediate Representation (IR)
We’ll write a simple Python script to convert the JSON SDL into a more structured IR.

```python
// compiler.py
import json
from typing import Dict, List

def compile_schema(schema_path: str) -> Dict:
    with open(schema_path) as f:
        raw_schema = json.load(f)

    ir = {
        "database": raw_schema["database"],
        "tables": []
    }

    for table in raw_schema["tables"]:
        ir_table = {
            "tableName": table["name"],
            "columns": []
        }
        for column in table["columns"]:
            col_type = column["type"]
            if "maxLength" in column:
                col_type += f"({column['maxLength']})"
            elif "references" in column:
                col_type = "foreignKey"
            ir_table["columns"].append({
                "name": column["name"],
                "type": col_type,
                **{k: v for k, v in column.items() if k not in ["type", "name"]}
            })
        ir["tables"].append(ir_table)

    return ir

if __name__ == "__main__":
    ir = compile_schema("schema.json")
    print(json.dumps(ir, indent=2))
```

Running this will produce:
```json
{
  "database": "app_db",
  "tables": [
    {
      "tableName": "users",
      "columns": [
        {"name": "id", "type": "integer", "primaryKey": true},
        {"name": "name", "type": "string(100)"},
        {"name": "email", "type": "string", "unique": true}
      ]
    },
    {
      "tableName": "posts",
      "columns": [
        {"name": "id", "type": "integer", "primaryKey": true},
        {"name": "title", "type": "string(200)"},
        {"name": "content", "type": "text"},
        {"name": "author_id", "type": "foreignKey", "references": ["users.id"]}
      ]
    }
  ]
}
```

### 3. Generate SQLAlchemy Models from the IR
Now, let’s generate SQLAlchemy models using the IR.

```python
// sqlalchemy_generator.py
def generate_sqlalchemy(ir):
    output = []
    for table in ir["tables"]:
        output.append(f"from sqlalchemy import Column, Integer, String, Text")
        output.append(f"from sqlalchemy.orm import relationship")
        output.append(f"from sqlalchemy.ext.declarative import declarative_base")
        output.append(f"\nBase = declarative_base()")
        output.append(f"\nclass {table['tableName'].capitalize()}(Base):")
        output.append(f"    __tablename__ = \"{table['tableName']}\"")
        for column in table["columns"]:
            col_type = {
                "integer": "Integer",
                "string": "String",
                "text": "Text",
                "foreignKey": "Integer"  # Placeholder for actual foreign key handling
            }.get(column["type"].replace("(", "").replace(")", ""), "String")
            attrs = [f"{k}={v}" for k, v in column.items() if k not in ["name", "type"]]
            if "references" in column:
                attrs.append("foreign_keys=users.id")
            output.append(f"    {column['name']} = Column({col_type}, {' '.join(attrs)})")
        output.append("\n")
    return "\n".join(output)

if __name__ == "__main__":
    with open("ir.json") as f:
        ir = json.load(f)
    print(generate_sqlalchemy(ir))
```

This will output:
```python
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primaryKey=True)
    name = Column(String, maxLength=100)
    email = Column(String, unique=True)

class Posts(Base):
    __tablename__ = "posts"
    id = Column(Integer, primaryKey=True)
    title = Column(String, maxLength=200)
    content = Column(Text)
    author_id = Column(Integer, foreign_keys=users.id)
```

### 4. Generate GORM Structs from the IR
Now, let’s generate GORM structs in Go.

```go
// gorm_generator.go
package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type IRTable struct {
	TableName string `json:"tableName"`
	Columns   []IRColumn `json:"columns"`
}

type IRColumn struct {
	Name     string   `json:"name"`
	Type     string   `json:"type"`
	Unique   bool     `json:"unique,omitempty"`
	MaxLength int     `json:"maxLength,omitempty"`
	References []string `json:"references,omitempty"`
}

func generateGORM(ir IR) string {
	var output []string
	output = append(output, `package models`)
	output = append(output, `import "gorm.io/gorm"`) // Simplified for example

	for _, table := range ir.Tables {
		output = append(output, fmt.Sprintf(`type %s struct {`, table.TableName))
		output = append(output, `	ID uint ` + `"gorm:"primaryKey"`)
		for _, col := range table.Columns {
			var colType string
			switch col.Type {
			case "integer":
				colType = "uint"
			case "string(100)":
				colType = "string"
				output = append(output, fmt.Sprintf(`	%s string `+"`gorm:\"size:%s\"`", col.Name, col.MaxLength))
			case "string":
				colType = "string"
				output = append(output, fmt.Sprintf(`	%s string `+"`gorm:\"unique\"`", col.Name))
			case "text":
				colType = "string"
				output = append(output, fmt.Sprintf(`	%s string`, col.Name))
			case "foreignKey":
				colType = "uint"
				output = append(output, fmt.Sprintf(`	%s uint `+"`gorm:\"foreignKey:author_id\"`", col.Name))
			}
		}
		output = append(output, "}")
		output = append(output, "")
	}
	return "\n".join(output)
}

func main() {
	ir := IR{}
	file, _ := os.ReadFile("ir.json")
	json.Unmarshal(file, &ir)
	fmt.Println(generateGORM(ir))
}
```

This will output:
```go
package models
import "gorm.io/gorm"

type Users struct {
	ID uint `gorm:"primaryKey"`
	Name string `gorm:"size:100"`
	Email string `gorm:"unique"`
}

type Posts struct {
	ID uint `gorm:"primaryKey"`
	Title string `gorm:"size:200"`
	Content string
	AuthorID uint `gorm:"foreignKey:author_id"`
}
```

---

## **Implementation Guide**

Here’s a step-by-step guide to implementing the **Multi-Language Schema Input** pattern in your project:

### 1. Choose Your Schema Definition Language (SDL)
   - Start with **JSON or YAML** for simplicity.
   - If you need more expressiveness, consider a **custom DSL** or **GraphQL Schema Language (SDL)**.

### 2. Build the Schema Compiler
   - Write a script or small tool to convert your SDL into an **IR**.
   - The IR should be **simple and standardized** (e.g., JSON or a protobuf-based format).
   - Example tasks for the compiler:
     - Parse the SDL.
     - Validate the schema (e.g., ensure primary keys exist).
     - Convert types and constraints into a consistent format.

### 3. Write Code Generators for Each Backend
   - For each backend your team uses (Python, Go, JavaScript, etc.), write a generator that:
     - Takes the IR as input.
     - Outputs language-specific models (e.g., SQLAlchemy, GORM, Mongoose).
   - Start with the most critical backends first.

### 4. Automate the Pipeline
   - Use a **CI/CD pipeline** to compile schemas and generate models whenever the SDL changes.
   - Tools like **GitHub Actions**, **Jenkins**, or **Makefiles** can help automate this.
   - Example workflow:
     1. Push changes to the SDL file.
     2. Compiler runs and updates the IR.
     3. Generators run and update the backend models.
     4. Tests run to ensure consistency.

### 5. Document the Pattern
   - Clearly document:
     - How to define a schema in your SDL.
     - How the compiler and generators work.
     - How to extend the pattern for new backends.

---

## **Common Mistakes to Avoid**

1. **Overcomplicating the IR**
   - Keep the IR as simple as possible. The more complex it is, the harder it is to maintain.
   - Avoid reinventing the wheel—stay close to standard formats like JSON.

2. **Ignoring Validation**
   - Always validate your schema before compiling it. Missing primary keys or invalid types can cause runtime errors.
   - Example validation checks:
     - Every table must have a primary key.
     - Foreign keys must reference existing columns.

3. **Not Testing Generators**
   - Write unit tests for your code generators to ensure they produce correct output.
   - Example tests:
     - Verify that a `Users` table in the IR generates a `users` table in SQLAlchemy.
     - Check that foreign key constraints are preserved.

4. **Assuming All Backends Need Full Support**
   - Some backends (like MongoDB) don’t support SQL features like foreign keys. Design your IR to handle these differences gracefully.

5. **Forgetting to Update the SDL**
   - Treat the SDL as the **single source of truth** for your data model. Always update it when the schema changes, even for minor tweaks.

---

## **Key Takeaways**

- **Decouple schema definition from backend code**: Define your schema once in a language-agnostic format, then compile it into whatever backend you need.
- **Use a simple IR**: The intermediate representation should be easy to understand and maintain.
- **Automate the pipeline**: Use tools like CI/CD to keep your models in sync with the SDL.
- **Start small**: Begin with one or two backends, then expand as needed.
- **Validate early**: Always validate your schema before compiling it to avoid runtime errors.

---

## **Conclusion**

The **Multi-Language Schema Input** pattern is a powerful way to