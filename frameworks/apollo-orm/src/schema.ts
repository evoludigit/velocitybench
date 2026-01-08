export const typeDefs = `#graphql
  type User {
    id: ID!
    username: String!
    fullName: String
    bio: String
    posts(limit: Int = 50): [Post!]!
  }

  type Post {
    id: ID!
    title: String!
    content: String
    author: User!
    comments(limit: Int = 50): [Comment!]!
  }

  type Comment {
    id: ID!
    content: String!
    author: User!
    post: Post!
  }

  type Query {
    ping: String!
    user(id: ID!): User
    users(limit: Int = 10): [User!]!
    post(id: ID!): Post
    posts(limit: Int = 10): [Post!]!
    comment(id: ID!): Comment
    comments(limit: Int = 10): [Comment!]!
  }

  type Mutation {
    updateUser(id: ID!, fullName: String, bio: String): User
  }
`;
