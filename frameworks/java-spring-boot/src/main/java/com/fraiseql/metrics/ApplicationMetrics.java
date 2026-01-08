package com.fraiseql.metrics;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Component;

@Component
public class ApplicationMetrics {

    private final Counter graphqlQueriesTotal;
    private final Counter restRequestsTotal;
    private final Counter databaseErrorsTotal;
    private final MeterRegistry meterRegistry;

    public ApplicationMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
        this.graphqlQueriesTotal = Counter.builder("graphql.queries.total")
                .description("Total number of GraphQL queries executed")
                .register(meterRegistry);

        this.restRequestsTotal = Counter.builder("rest.requests.total")
                .description("Total number of REST API requests")
                .register(meterRegistry);

        this.databaseErrorsTotal = Counter.builder("database.errors.total")
                .description("Total number of database errors")
                .register(meterRegistry);
    }

    public void incrementGraphQLQueries() {
        graphqlQueriesTotal.increment();
    }

    public void incrementRestRequests() {
        restRequestsTotal.increment();
    }

    public void incrementDatabaseErrors() {
        databaseErrorsTotal.increment();
    }

    // Additional metrics for GraphQL operations
    public void recordGraphQLOperation(String operationType, String operationName) {
        Counter.builder("graphql.operations")
                .tag("type", operationType)
                .tag("name", operationName)
                .description("GraphQL operations by type and name")
                .register(meterRegistry)
                .increment();
    }
}