package com.velocitybench.graphql;

import graphql.GraphQL;
import graphql.schema.GraphQLSchema;
import graphql.schema.idl.RuntimeWiring;
import graphql.schema.idl.SchemaGenerator;
import graphql.schema.idl.SchemaParser;
import graphql.schema.idl.TypeDefinitionRegistry;
import io.micronaut.context.annotation.Bean;
import io.micronaut.context.annotation.Factory;
import io.micronaut.core.io.ResourceResolver;
import jakarta.inject.Singleton;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.stream.Collectors;

import static graphql.schema.idl.TypeRuntimeWiring.newTypeWiring;

@Factory
public class GraphQLFactory {

    @Bean
    @Singleton
    public GraphQL graphQL(ResourceResolver resourceResolver, QueryResolver queryResolver,
                          MutationResolver mutationResolver, TypeResolvers typeResolvers) {

        // Load schema
        SchemaParser schemaParser = new SchemaParser();
        String schemaString = resourceResolver.getResourceAsStream("classpath:schema.graphqls")
            .map(is -> new BufferedReader(new InputStreamReader(is)).lines().collect(Collectors.joining("\n")))
            .orElseThrow(() -> new RuntimeException("Schema not found"));

        TypeDefinitionRegistry typeRegistry = schemaParser.parse(schemaString);

        // Build runtime wiring
        RuntimeWiring runtimeWiring = RuntimeWiring.newRuntimeWiring()
            .type(newTypeWiring("Query")
                .dataFetcher("ping", queryResolver.ping())
                .dataFetcher("user", queryResolver.user())
                .dataFetcher("users", queryResolver.users())
                .dataFetcher("post", queryResolver.post())
                .dataFetcher("posts", queryResolver.posts()))
            .type(newTypeWiring("Mutation")
                .dataFetcher("updateUser", mutationResolver.updateUser())
                .dataFetcher("updatePost", mutationResolver.updatePost()))
            .type(newTypeWiring("User")
                .dataFetcher("posts", typeResolvers.userPosts())
                .dataFetcher("followers", typeResolvers.userFollowers())
                .dataFetcher("following", typeResolvers.userFollowing()))
            .type(newTypeWiring("Post")
                .dataFetcher("author", typeResolvers.postAuthor())
                .dataFetcher("comments", typeResolvers.postComments()))
            .type(newTypeWiring("Comment")
                .dataFetcher("author", typeResolvers.commentAuthor())
                .dataFetcher("post", typeResolvers.commentPost()))
            .build();

        // Build schema
        SchemaGenerator schemaGenerator = new SchemaGenerator();
        GraphQLSchema graphQLSchema = schemaGenerator.makeExecutableSchema(typeRegistry, runtimeWiring);

        return GraphQL.newGraphQL(graphQLSchema).build();
    }
}
