**[Pattern] Reference Guide: Schema Authoring with Python SDK**

---
### **Overview**
The Python SDK for GraphQL schema authoring leverages **decorators, type hints, and validation mechanisms** to define GraphQL schemas declaratively within Python classes. This approach eliminates the need for separate schema definition files (e.g., `.graphql` or SDL) while ensuring type safety and tooling integration. Developers can annotate Python classes, methods, and fields with GraphQL directives, automatically generating a compliant schema during runtime. The pattern supports common GraphQL constructs like **scalar types, objects, interfaces, unions, and custom directives**, while enforcing validation via static type checking (e.g., `mypy`, `pyright`) and runtime validation.

Ideal for:
- **Backend services** integrating GraphQL (e.g., FastAPI, Django, Flask).
- **Monorepos** where schema and business logic coexist.
- **Teams** prioritizing developer experience (DX) with minimal boilerplate.

---

---

### **Core Concepts & Schema Reference**
The Python SDK uses the following meta-decorators and annotations to define GraphQL types:

| **Component**               | **Decorator/Annotation**          | **Purpose**                                                                                     | **Example Usage**                                                                                     |
|-----------------------------|------------------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **GraphQL Object Type**     | `@graphql_object_type`             | Declares a root type (e.g., `User`, `Product`).                                               | `@graphql_object_type`                                                                               |
| **GraphQL Field**           | `@graphql_field`                   | Defines a field with input/output type, arguments, and directives.                            | `@graphql_field(description="User's email", type=String)`                                            |
| **GraphQL Input Type**      | `@graphql_input_type`              | Specifies input types for mutations/resolvers.                                                 | `@graphql_input_type`                                                                               |
| **GraphQL Scalar**          | `@graphql_scalar_type`             | Custom scalars (e.g., `Date`, `JSON`) with validation logic.                                   | `@graphql_scalar_type(description="ISO-formatted date")`                                             |
| **GraphQL Argument**        | `arg: Type = DefaultValue`         | Adds arguments to fields/mutations (type-hinted).                                              | `def create_user(self, arg: str = "default"): ...`                                                    |
| **GraphQL Directive**       | `@graphql_directive`               | Custom directives (e.g., `@auth`, `@deprecated`).                                             | `@graphql_directive(description="Enforce role-based access")`                                         |
| **GraphQL Interface/Union** | `@graphql_interface_type`/`@union` | Defines reusable contracts (e.g., `Node`, `SearchResult`).                                     | `@graphql_interface_type(resolvers={"__resolveType": resolve_interface_type})`                      |
| **Validation**              | `@validator`                       | Runtime validation for fields/arguments (e.g., regex, length).                                | `@validator(regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")`                          |
| **Default Resolver**        | `resolver` keyword                 | Overrides default field resolution logic.                                                     | `resolver=lambda obj: obj.name.upper()`                                                             |

---

---

### **Schema Definition Patterns**
#### **1. Basic Object Type**
```python
from typing import Optional
from graphene import String, Int, ObjectType, Field

class User(ObjectType):
    @graphql_object_type
    class Meta:
        description = "A registered user in the system."

    id = Field(Int, required=True)
    name = Field(String, required=True)
    email = Field(String, required=True)

    @graphql_field(description="Full name in uppercase")
    def full_name(self) -> str:
        return self.name.upper()
```

#### **2. Input Type for Mutations**
```python
class CreateUserInput(ObjectType):
    @graphql_input_type
    class Meta:
        description = "Input for creating a new user."

    name = String(required=True)
    email = String(required=True, validator=validate_email)  # Custom validator
```

#### **3. Union/Interface Example**
```python
class Node(ObjectType):
    @graphql_interface_type(resolvers={"__resolveType": resolve_node_type})
    class Meta:
        description = "Base node interface."

class Post(Node):
    @inherit_graphql_object_type
    title = String()

class Comment(Node):
    @inherit_graphql_object_type
    text = String()
```

#### **4. Custom Scalar with Validation**
```python
class DateScalar(graphene.Scalar):
    @graphql_scalar_type
    class Meta:
        description = "ISO 8601 date string."

    @staticmethod
    def serialize(date_obj: datetime.date) -> str:
        return date_obj.isoformat()

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, StringValue):
            return datetime.datetime.strptime(ast.value, "%Y-%m-%d").date()

    @staticmethod
    def parse_value(value: str) -> datetime.date:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
```

#### **5. Directives**
```python
@graphql_directive(
    name="auth",
    locations=[DIRECTIVE_LOCATION_FIELD_DEFINITION],
    args={"role": String()}
)
def auth_directive(**_):
    """Enforces role-based access on fields."""
    pass
```

---

---

### **Query Examples**
#### **1. Querying a Schema**
```python
# Generates the schema from decorators (auto-discovered)
schema = create_schema(queries=[Query])

# Example query (resolved via Python resolver)
query = """
    query GetUser($id: Int!) {
        user(id: $id) {
            id
            fullName
        }
    }
"""

result = schema.execute(query, variables={"id": 1})
```

#### **2. Mutation with Input Type**
```python
mutation = """
    mutation CreateUser($input: CreateUserInput!) {
        createUser(input: $input) {
            user {
                id
                email
            }
        }
    }
"""

variables = {"input": {"name": "Alice", "email": "alice@example.com"}}
result = schema.execute(mutation, variables=variables)
```

#### **3. Using Directives**
```python
query = """
    query {
        user(id: 1) @auth(role: "admin") {
            email
        }
    }
"""
```

---

---

### **Advanced Features**
#### **1. Dynamic Fields**
```python
class DynamicUser(User):
    @graphql_field(dynamic=True)  # Fields resolved dynamically
    def metadata(self):
        return {"tags": ["premium"]}
```

#### **2. Batch Resolvers**
```python
@graphql_field(resolver=batch_resolver)
def posts(self) -> List["Post"]:
    return Post.objects.filter(author=self)
```

#### **3. Legacy Schema Merge**
```python
from graphene import Schema as GraphQLSchema

# Merge with existing SDL (if needed)
schema = GraphQLSchema(
    types=[User, Query],
    auto_camelcase=False,
    merge_existing_schemas=["legacy_schema.graphql"]
)
```

---

---

### **Validation & Error Handling**
| **Validation Type**       | **Tool/Annotation**                     | **Example**                                                                                     |
|---------------------------|------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Static Type Checking**  | `mypy`/`pyright`                        | `mypy --python-version 3.9 schema.py`                                                          |
| **Runtime Validation**    | `@validator`, `@graphql_input_type`      | `@validator(lambda x: len(x) > 3, error="Name too short")`                                     |
| **Directive Validation**  | `@graphql_directive`                    | Ensure `@auth` directives are on allowed locations.                                              |
| **Field-Level Errors**    | `graphene.errors`                       | `raise ValidationError("Invalid email")` in a resolver.                                          |

---

---

### **Related Patterns**
1. **GraphQL Schema Stitching**
   - Combine schemas from multiple services (e.g., using `graphene-relay` or `Apollo Federation`).
   - *Example*: `@graphql_object_type(resolver=lambda obj: obj.to_federated_type())`

2. **GraphQL Subscriptions**
   - Add real-time updates via `graphene.types.ObjectType` with async resolvers.
   - *Example*:
     ```python
     @graphql_subscription
     async def on_comment_created(self, info):
         return Comment.objects.filter(published=True).latest()
     ```

3. **Type Generation from Database Models**
   - Auto-generate GraphQL types from ORM models (e.g., Django, SQLAlchemy).
   - *Example*: `@type_from_model(model=User, exclude=["password"])`

4. **Performance Optimization**
   - **DataLoader**: Batch/resolve N+1 queries.
     ```python
     class UserLoader(DataLoader):
         async def load(self, user_ids):
             return await User.objects.filter(id__in=user_ids). ValuesListQuerySet("id", "name")
     ```
   - **Persisted Queries**: Cache query strings via `graphene.persisted_queries`.

5. **Testing**
   - **Unit Tests**: Mock resolvers with `unittest.mock`.
   - **Integration Tests**: Use `graphene.test.SchemaTestCase`.
     ```python
     class UserTest(SchemaTestCase):
         def test_query_user(self):
             result = self.execute("""
                 query { user(id: 1) { name } }
             """)
             assert result["data"]["user"]["name"] == "Alice"
     ```

6. **Custom Persisted Queries**
   - Store queries in a database and reference by ID.
   - *Example*:
     ```python
     @graphql_persisted_query(hash="abc123")
     def persisted_query():
         return """
             query { user(id: 1) { name } }
         """
     ```

---

---
**Notes:**
- **Compatibility**: Requires Python 3.7+ and `graphene-python` ≥ 3.0.
- **Tooling**: Integrates with VS Code (`pylance`), `black`, and `pre-commit`.
- **Alternatives**:
  - **SDL-first**: Define schema in `.graphql` files (e.g., with `graphene` or `strawberry`).
  - **Codegen**: Generate types from existing Python classes (e.g., `graphene-codegen`).

---
**Feedback**: Open an issue in the [Python SDK repo](LINK_TO_REPO) for schema authoring enhancements.