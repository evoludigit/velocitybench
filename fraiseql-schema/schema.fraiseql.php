<?php
/**
 * FraiseQL Schema Definition - PHP Implementation
 *
 * Equivalent to Python schema.fraiseql.py
 * Exports identical schema.json when executed
 */

/**
 * FieldDefinition represents a GraphQL field with type information
 */
class FieldDefinition {
    public $type;
    public $required;

    public function __construct($type, $required = false) {
        $this->type = $type;
        $this->required = $required;
    }

    public function toArray() {
        return [
            'type' => $this->type,
            'required' => $this->required,
        ];
    }
}

/**
 * ObjectType represents a GraphQL object type (e.g., User, Post)
 */
class ObjectType {
    public $name;
    public $fields;

    public function __construct($name) {
        $this->name = $name;
        $this->fields = [];
    }

    public function addField($fieldName, $fieldType, $required = false) {
        $this->fields[$fieldName] = new FieldDefinition($fieldType, $required);
    }

    public function toArray() {
        $fieldsArray = [];
        foreach ($this->fields as $name => $field) {
            $fieldsArray[$name] = $field->toArray();
        }
        return [
            'name' => $this->name,
            'fields' => $fieldsArray,
        ];
    }
}

/**
 * SchemaDefinition is the root schema container
 */
class SchemaDefinition {
    public $types;
    public $query;
    public $mutation;

    public function __construct() {
        $this->types = [];
        $this->query = [];
        $this->mutation = [];
    }

    public function addType($objectType) {
        $this->types[$objectType->name] = $objectType;
    }

    public function addQuery($name, $returnType) {
        $this->query[$name] = [
            'type' => $returnType,
            'arguments' => [],
        ];
    }

    public function addMutation($name, $returnType, $args = []) {
        $this->mutation[$name] = [
            'type' => $returnType,
            'arguments' => $args,
        ];
    }

    public function toArray() {
        $typesArray = [];
        foreach ($this->types as $name => $type) {
            $typesArray[$name] = $type->toArray();
        }
        return [
            'types' => $typesArray,
            'query' => $this->query,
            'mutation' => $this->mutation,
        ];
    }
}

/**
 * BuildSchema builds and returns the FraiseQL schema definition
 */
function buildSchema() {
    $schema = new SchemaDefinition();

    // User type: represents a user in the system
    $userType = new ObjectType('User');
    $userType->addField('id', 'ID', true);
    $userType->addField('name', 'String', true);
    $userType->addField('email', 'String', true);
    $userType->addField('created_at', 'DateTime', false);
    $userType->addField('is_active', 'Boolean', false);
    $schema->addType($userType);

    // Post type: represents a blog post
    $postType = new ObjectType('Post');
    $postType->addField('id', 'ID', true);
    $postType->addField('title', 'String', true);
    $postType->addField('content', 'String', true);
    $postType->addField('author_id', 'ID', true);
    $postType->addField('published', 'Boolean', false);
    $postType->addField('created_at', 'DateTime', false);
    $schema->addType($postType);

    // Comment type: represents a comment on a post
    $commentType = new ObjectType('Comment');
    $commentType->addField('id', 'ID', true);
    $commentType->addField('content', 'String', true);
    $commentType->addField('post_id', 'ID', true);
    $commentType->addField('author_id', 'ID', true);
    $commentType->addField('created_at', 'DateTime', false);
    $schema->addType($commentType);

    // Query root: defines all available queries
    $schema->addQuery('users', '[User]');
    $schema->addQuery('posts', '[Post]');

    // Mutation root: defines all available mutations
    $schema->addMutation('create_user', 'User', [
        'name' => 'String!',
        'email' => 'String!',
    ]);

    return $schema;
}

// Execute and output
$schema = buildSchema();
echo json_encode($schema->toArray(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
?>
