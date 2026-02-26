package com.velocitybench.graphql;

import io.micronaut.configuration.graphql.GraphQLExecutionInputCustomizer;
import graphql.ExecutionInput;
import jakarta.inject.Singleton;
import org.reactivestreams.Publisher;
import reactor.core.publisher.Mono;

@Singleton
public class GraphQLDataLoaderPreparer implements GraphQLExecutionInputCustomizer {

    private final DataLoaderRegistry dataLoaderRegistry;

    public GraphQLDataLoaderPreparer(DataLoaderRegistry dataLoaderRegistry) {
        this.dataLoaderRegistry = dataLoaderRegistry;
    }

    @Override
    public Publisher<ExecutionInput> customize(ExecutionInput executionInput, io.micronaut.http.HttpRequest httpRequest, io.micronaut.http.MutableHttpResponse<String> httpResponse) {
        return Mono.just(executionInput.transform(builder ->
            builder.dataLoaderRegistry(dataLoaderRegistry.create())
        ));
    }
}
