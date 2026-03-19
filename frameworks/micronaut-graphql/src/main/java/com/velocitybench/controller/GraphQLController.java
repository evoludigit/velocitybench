package com.velocitybench.controller;

import com.velocitybench.graphql.DataLoaderRegistry;
import graphql.ExecutionInput;
import graphql.ExecutionResult;
import graphql.GraphQL;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.annotation.Consumes;
import io.micronaut.http.annotation.Produces;
import jakarta.inject.Singleton;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Controller("/graphql")
@Singleton
public class GraphQLController {

    private final GraphQL graphQL;
    private final DataLoaderRegistry dataLoaderRegistry;

    public GraphQLController(GraphQL graphQL, DataLoaderRegistry dataLoaderRegistry) {
        this.graphQL = graphQL;
        this.dataLoaderRegistry = dataLoaderRegistry;
    }

    @Post
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Map<String, Object> execute(@Body Map<String, Object> body) {
        String query = (String) body.get("query");
        @SuppressWarnings("unchecked")
        Map<String, Object> variables = (Map<String, Object>) body.getOrDefault("variables", Map.of());
        String operationName = (String) body.get("operationName");

        ExecutionInput input = ExecutionInput.newExecutionInput()
            .query(query)
            .variables(variables)
            .operationName(operationName)
            .dataLoaderRegistry(dataLoaderRegistry.create())
            .build();

        ExecutionResult result = graphQL.execute(input);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("data", result.getData());
        if (!result.getErrors().isEmpty()) {
            List<Map<String, Object>> errors = result.getErrors().stream()
                .map(e -> {
                    Map<String, Object> err = new LinkedHashMap<>();
                    err.put("message", e.getMessage());
                    return err;
                })
                .collect(Collectors.toList());
            response.put("errors", errors);
        }
        return response;
    }
}
