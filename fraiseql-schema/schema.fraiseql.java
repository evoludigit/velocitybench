import java.util.*;
import com.google.gson.*;

/**
 * FraiseQL Schema Definition - Java Implementation
 *
 * Equivalent to Python schema.fraiseql.py
 * Exports identical schema.json when compiled and run
 */
public class SchemaDef {

    static class FieldDefinition {
        public String type;
        public boolean required;

        public FieldDefinition(String type, boolean required) {
            this.type = type;
            this.required = required;
        }
    }

    static class ObjectType {
        public String name;
        public Map<String, FieldDefinition> fields;

        public ObjectType(String name) {
            this.name = name;
            this.fields = new LinkedHashMap<>();
        }

        public void addField(String fieldName, String fieldType, boolean required) {
            this.fields.put(fieldName, new FieldDefinition(fieldType, required));
        }
    }

    static class SchemaDefinition {
        public Map<String, ObjectType> types;
        public Map<String, Map<String, Object>> query;
        public Map<String, Map<String, Object>> mutation;

        public SchemaDefinition() {
            this.types = new LinkedHashMap<>();
            this.query = new LinkedHashMap<>();
            this.mutation = new LinkedHashMap<>();
        }
    }

    static SchemaDefinition buildSchema() {
        SchemaDefinition schema = new SchemaDefinition();

        // User type: represents a user in the system
        ObjectType userType = new ObjectType("User");
        userType.addField("id", "ID", true);
        userType.addField("name", "String", true);
        userType.addField("email", "String", true);
        userType.addField("created_at", "DateTime", false);
        userType.addField("is_active", "Boolean", false);
        schema.types.put("User", userType);

        // Post type: represents a blog post
        ObjectType postType = new ObjectType("Post");
        postType.addField("id", "ID", true);
        postType.addField("title", "String", true);
        postType.addField("content", "String", true);
        postType.addField("author_id", "ID", true);
        postType.addField("published", "Boolean", false);
        postType.addField("created_at", "DateTime", false);
        schema.types.put("Post", postType);

        // Comment type: represents a comment on a post
        ObjectType commentType = new ObjectType("Comment");
        commentType.addField("id", "ID", true);
        commentType.addField("content", "String", true);
        commentType.addField("post_id", "ID", true);
        commentType.addField("author_id", "ID", true);
        commentType.addField("created_at", "DateTime", false);
        schema.types.put("Comment", commentType);

        // Query root: defines all available queries
        Map<String, Object> usersQuery = new LinkedHashMap<>();
        usersQuery.put("type", "[User]");
        usersQuery.put("arguments", new LinkedHashMap<>());
        schema.query.put("users", usersQuery);

        Map<String, Object> postsQuery = new LinkedHashMap<>();
        postsQuery.put("type", "[Post]");
        postsQuery.put("arguments", new LinkedHashMap<>());
        schema.query.put("posts", postsQuery);

        // Mutation root: defines all available mutations
        Map<String, Object> createUserMutation = new LinkedHashMap<>();
        createUserMutation.put("type", "User");
        Map<String, String> createUserArgs = new LinkedHashMap<>();
        createUserArgs.put("name", "String!");
        createUserArgs.put("email", "String!");
        createUserMutation.put("arguments", createUserArgs);
        schema.mutation.put("create_user", createUserMutation);

        return schema;
    }

    public static void main(String[] args) {
        SchemaDefinition schema = buildSchema();
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(schema);
        System.out.println(json);
    }
}
