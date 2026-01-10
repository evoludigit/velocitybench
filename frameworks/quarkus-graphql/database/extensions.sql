-- Quarkus GraphQL Framework Extensions
-- Trinity Pattern schema from schema-template.sql is sufficient

SET search_path TO benchmark, public;

-- No framework-specific extensions required
-- Quarkus GraphQL uses Trinity Pattern tables directly
-- from the schema template

-- Quarkus handles entity class mapping separately via JPA annotations

-- Future: Add Quarkus GraphQL-specific views, functions, or configurations here
