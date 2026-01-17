# **[Pattern] Object Type Mapping Reference Guide**

---

## **Overview**
The **Object Type Mapping** pattern defines a structured approach for transforming or adapting data between different object models or schemas in an application. This pattern is essential when working with heterogeneous data sources, microservices with incompatible interfaces, or APIs that return data in formats not directly consumable by client applications.

Key benefits include:
- **Decoupling**: Isolates downstream systems from changes in data structure.
- **Consistency**: Enforces standardized output regardless of input variations.
- **Reusability**: Centralizes mapping logic to avoid redundancy.
- **Extensibility**: Supports dynamic adaptation of schemas via configuration or runtime rules.

This pattern is typically implemented using:
- **Manual mapping** (e.g., hand-written mappers)
- **Automated tooling** (e.g., AutoMapper, MapStruct, or schema registries)
- **API gateways** or **mediation layers** that normalize responses

---

## **Core Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 | **Example**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Source Object**       | The original data structure (e.g., a database record, API response, or DTO from Service A).                                                                                                                   | `User` object from a legacy `LegacyUsersService`                                                |
| **Target Object**       | The desired output structure (e.g., a domain model, view model, or DTO for Service B).                                                                                                                      | `PublicUserProfile` for a frontend application                                                   |
| **Mapper**             | Logic or configuration that defines how source fields map to target fields. May include transformations (e.g., flattening nested objects, data type conversions).                                        | Rule: `source.userName → target.displayName`                                                     |
| **Field Mapping**       | A one-to-one or many-to-one relationship between source and target properties.                                                                                                                           | `source.id` → `target.userId` (direct), `source.address.city` → `target.location` (aggregation) |
| **Custom Rule**         | A function or expression applied during mapping (e.g., date formatting, filtering, or conditional logic).                                                                                                     | `source.createdAt → target.signupDate = formatDate(source.createdAt, 'YYYY-MM-DD')`             |
| **Type Adapter**        | A helper to handle incompatible data types (e.g., converting a JSON blob to a strongly-typed object).                                                                                                         | `JSON.parse(source.profileData) → target.profile`                                                |
| **Error Handling**      | Rules for managing missing fields, type mismatches, or validation failures.                                                                                                                               | Skip missing fields, throw errors, or default to placeholder values.                            |

---

## **Implementation Strategies**
### **1. Manual Mapping (Code-Based)**
Write explicit mapping logic in your application code (e.g., Java, C#, or JavaScript).

#### **Example (Java - Direct Mapping)**
```java
public ProfileDto mapLegacyUserToProfile(LegacyUser user) {
    ProfileDto profile = new ProfileDto();
    profile.setId(user.getId()); // Simple field copy
    profile.setFullName(user.getFirstName() + " " + user.getLastName()); // Transformation
    profile.setEmail(user.getContact().getEmail()); // Nested property
    if (user.getPreferences() != null) {
        profile.setTheme(user.getPreferences().getTheme()); // Conditional
    }
    return profile;
}
```

#### **Pros:**
- Full control over logic.
- No external dependencies.

#### **Cons:**
- Prone to errors in large schemas.
- Harder to maintain.

---

### **2. Library-Based Mapping (AutoMapper/MapStruct)**
Use libraries to automate mapping with declarative syntax.

#### **Example (AutoMapper - C#)**
```csharp
public class UserMappingProfile : Profile {
    public UserMappingProfile() {
        CreateMap<LegacyUser, UserDto>()
            .ForMember(dest => dest.Name, opt => opt.MapFrom(src => $"{src.FirstName} {src.LastName}"))
            .ForMember(dest => dest.Email, opt => opt.MapFrom(src => src.Contact.Email))
            .ForAllOtherMembers(opt => opt.Ignore()); // Skip unmapped fields
    }
}
```

#### **Example (MapStruct - Java)**
```java
@Mapper
public interface LegacyUserMapper {
    @Mapping(source = "firstName", target = "firstName")
    @Mapping(source = "lastName", target = "lastName")
    @Mapping(target = "fullName", expression = "java(src.getFirstName() + ' ' + src.getLastName())")
    UserDto legacyUserToUserDto(LegacyUser legacyUser);
}
```

#### **Pros:**
- Reduces boilerplate.
- Strongly typed and IDE-friendly.

#### **Cons:**
- Requires library integration.
- Less flexible for complex custom logic.

---

### **3. Configuration-Based (JSON/YAML)**
Define mappings externally in a serializable format.

#### **Example (JSON Schema Mapping)**
```json
{
  "source": "legacyUser",
  "target": "userDto",
  "mappings": [
    { "from": "id", "to": "id" },
    { "from": "firstName", "to": "firstName" },
    { "from": "lastName", "to": "lastName" },
    { "from": "contact.email", "to": "email" },
    { "from": "preferences.theme", "to": "theme", "transform": "uppercase" }
  ]
}
```

#### **Pros:**
- Decouples mapping logic from code.
- Easy to update without redeploying.

#### **Cons:**
- Less type safety.
- Requires validation for complex rules.

---

### **4. API Gateway/Service Mesh**
Centralize mapping at the edge of your architecture (e.g., using Kong, Apigee, or Kubernetes-based gateways).

#### **Example (Kong API Gateway - Request/Response Transformation)**
```yaml
plugins:
  - name: request-transformer
    config:
      rules:
        - operation: add
          path: /users/{id}
          headers:
            "X-Mapping-Version": "v2"
```

---

## **Schema Reference**
| **Category**       | **Field**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|--------------------|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Source Fields**  | `sourcePath`            | The path to the source field (supports dot notation for nested objects).                                                                                                                                    | `user.address.street`                                                                           |
| **Target Fields**  | `targetPath`            | The path to the target field.                                                                                                                                                                          | `profile.address.street`                                                                            |
| **Mapping Type**   | `type`                  | Defines the mapping rule (`copy`, `transform`, `flatten`, `custom`).                                                                                                                                       | `transform` (e.g., for date formatting)                                                            |
| **Transform**      | `transformFn`           | A function or expression to apply during mapping (e.g., `uppercase`, `trim`, or a custom JavaScript function).                                                                                          | `transformFn: "source.toUpperCase()"`                                                             |
| **Validation**     | `required`              | Boolean indicating if the target field is required. If `true`, the source field must exist; otherwise, the target field may omit the value.                                                                     | `required: true`                                                                            |
| **Error Handling** | `fallback`              | Default value to use if the source field is missing or invalid.                                                                                                                                               | `fallback: "N/A"`                                                                               |
| **Type Adapter**   | `adapter`               | Specifies a custom adapter (e.g., `jsonParser`, `dateConverter`) to handle type mismatches.                                                                                                                 | `adapter: "dateConverter"` (converts `YYYY-MM-DD` to `DD/MM/YYYY`)                                |
| **Conditional**    | `condition`             | A condition to apply before mapping (e.g., `source.isActive === true`).                                                                                                                                         | `condition: "source.isAdmin"`                                                                   |

---

## **Query Examples**
### **1. Simple Field Mapping (AutoMapper - C#)**
```csharp
// Map a source object to a target object with direct field mapping.
var userDto = Mapper.Map<LegacyUser, UserDto>(legacyUser);
```

### **2. Nested Object Mapping (MapStruct - Java)**
```java
// Map a nested object with custom logic for transformations.
UserDto result = mapper.legacyUserToUserDto(legacyUser);
```

### **3. Dynamic Mapping via Configuration (Node.js)**
```javascript
const mapper = new ObjectMapper({
  mappings: [
    { from: "user.id", to: "profile.id" },
    { from: "user.email", to: "profile.contact.email" },
    { from: "user.preferences.theme", to: "profile.theme", transform: (val) => val.toLowerCase() }
  ],
  errorHandling: { fallback: null }
});

const profile = mapper.map(sourceUser, "profile");
```

### **4. Error Handling (Skip Missing Fields)**
```csharp
// Configure AutoMapper to ignore unmapped properties.
CreateMap<LegacyUser, UserDto>()
    .ForAllOtherMembers(opt => opt.Ignore());
```

### **5. Custom Type Adapter (JSON -> Object)**
```java
// Use MapStruct with a custom adapter for JSON fields.
@Mapper
public interface UserMapper {
    @Mapping(target = "tags", source = "tags", qualifiedBy = JsonToStringList.class)
    UserDto legacyUserToUserDto(LegacyUser legacyUser);
}

public class JsonToStringList implements ValueMapper<String[], List<String>> {
    @Override
    public List<String> map(String[] source) {
        return Arrays.asList(source);
    }
}
```

---

## **Common Pitfalls & Solutions**
| **Pitfall**                              | **Solution**                                                                                                                                                                                                 |
|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Inconsistent schemas**                 | Use a schema registry (e.g., Avro, Protocol Buffers) to enforce consistency.                                                                                                                        |
| **Performance bottlenecks**              | Cache mapped objects or batch-process mappings for bulk operations.                                                                                                                                    |
| **Tight coupling**                       | Decouple mapping logic from business logic (e.g., use dependency injection for mappers).                                                                                                             |
| **Hard-to-debug mappings**               | Log intermediate transformations or use tracing tools (e.g., OpenTelemetry).                                                                                                                          |
| **Dynamic schemas**                      | Implement a flexible mapping engine (e.g., runtime schema introspection) or use a schema-as-code approach (e.g., OpenAPI/Swagger).                                                                   |

---

## **Related Patterns**
| **Pattern**                     | **Relationship**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Adapter Pattern](#)**         | Object Type Mapping often relies on adapters to convert between incompatible interfaces.                                                                                                                 | When integrating with legacy systems or third-party APIs.                                           |
| **[Repository Pattern](#)**      | Mappings can be part of the repository layer to normalize data before exposing it to the application.                                                                                                         | For data access layers that need to abstract persistence details.                                      |
| **[View Model Pattern](#)**      | Mappings create view models optimized for specific use cases (e.g., frontend vs. admin panels).                                                                                                               | To decouple business logic from presentation layers.                                                   |
| **[Message Adapter](#)**         | Similar to Object Type Mapping but focused on message interchange (e.g., between microservices).                                                                                                         | In event-driven architectures or RPC systems.                                                          |
| **[Schema Registry](#)**         | Works alongside Object Type Mapping to manage evolving schemas across services.                                                                                                                              | For large-scale systems with frequent schema changes.                                                 |
| **[DTO (Data Transfer Object)](#)**| Mappings often produce DTOs to encapsulate data for transfer between layers.                                                                                                                           | To enforce data contracts between services or components.                                             |

---
## **Further Reading**
- **AutoMapper Documentation**: [https://automapper.org/](https://automapper.org/)
- **MapStruct**: [https://mapstruct.org/](https://mapstruct.org/)
- **Schema Registry (Confluent)**: [https://www.confluent.io/product/schema-registry/](https://www.confluent.io/product/schema-registry/)
- **Adapter Pattern (GoF)**: [https://refactoring.guru/design-patterns/adapter](https://refactoring.guru/design-patterns/adapter)