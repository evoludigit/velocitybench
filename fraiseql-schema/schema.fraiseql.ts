/**
 * FraiseQL Schema Definition - TypeScript Implementation
 *
 * Equivalent to Python schema.fraiseql.py
 * Exports identical schema.json when compiled
 */

interface FieldDefinition {
  type: string;
  required: boolean;
}

interface ObjectType {
  name: string;
  fields: Record<string, FieldDefinition>;
}

interface RootQuery {
  [key: string]: {
    type: string;
    arguments: Record<string, any>;
  };
}

interface RootMutation {
  [key: string]: {
    type: string;
    arguments: Record<string, any>;
  };
}

interface SchemaDefinition {
  types: Record<string, ObjectType>;
  query: RootQuery;
  mutation: RootMutation;
}

function createObjectType(name: string): ObjectType {
  return {
    name,
    fields: {},
  };
}

function addField(
  objectType: ObjectType,
  name: string,
  fieldType: string,
  required: boolean = false
): void {
  objectType.fields[name] = {
    type: fieldType,
    required,
  };
}

function buildSchema(): SchemaDefinition {
  const schema: SchemaDefinition = {
    types: {},
    query: {},
    mutation: {},
  };

  // User type: represents a user in the system
  const userType = createObjectType("User");
  addField(userType, "id", "ID", true);
  addField(userType, "name", "String", true);
  addField(userType, "email", "String", true);
  addField(userType, "created_at", "DateTime", false);
  addField(userType, "is_active", "Boolean", false);
  schema.types["User"] = userType;

  // Post type: represents a blog post
  const postType = createObjectType("Post");
  addField(postType, "id", "ID", true);
  addField(postType, "title", "String", true);
  addField(postType, "content", "String", true);
  addField(postType, "author_id", "ID", true);
  addField(postType, "published", "Boolean", false);
  addField(postType, "created_at", "DateTime", false);
  schema.types["Post"] = postType;

  // Comment type: represents a comment on a post
  const commentType = createObjectType("Comment");
  addField(commentType, "id", "ID", true);
  addField(commentType, "content", "String", true);
  addField(commentType, "post_id", "ID", true);
  addField(commentType, "author_id", "ID", true);
  addField(commentType, "created_at", "DateTime", false);
  schema.types["Comment"] = commentType;

  // Query root: defines all available queries
  schema.query.users = {
    type: "[User]",
    arguments: {},
  };
  schema.query.posts = {
    type: "[Post]",
    arguments: {},
  };

  // Mutation root: defines all available mutations
  schema.mutation.create_user = {
    type: "User",
    arguments: {
      name: "String!",
      email: "String!",
    },
  };

  return schema;
}

// Export schema as JSON (for compilation/testing)
const schema = buildSchema();
console.log(JSON.stringify(schema, null, 2));
