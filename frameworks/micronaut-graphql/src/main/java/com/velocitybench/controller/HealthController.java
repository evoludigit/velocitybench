package com.velocitybench.controller;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Produces;

import javax.sql.DataSource;
import java.sql.Connection;
import java.util.Map;

@Controller
public class HealthController {

    private final DataSource dataSource;

    public HealthController(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Get("/health")
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, String>> health() {
        boolean healthy = checkDatabase();
        Map<String, String> response = Map.of(
            "status", healthy ? "healthy" : "unhealthy",
            "framework", "micronaut-graphql"
        );
        return healthy ? HttpResponse.ok(response) : HttpResponse.serverError(response);
    }

    @Get("/metrics")
    @Produces(MediaType.TEXT_PLAIN)
    public String metrics() {
        return """
            # HELP micronaut_requests_total Total number of GraphQL requests
            # TYPE micronaut_requests_total counter
            micronaut_requests_total 0
            # HELP micronaut_db_pool_size Database connection pool size
            # TYPE micronaut_db_pool_size gauge
            micronaut_db_pool_size 50
            """;
    }

    private boolean checkDatabase() {
        try (Connection conn = dataSource.getConnection()) {
            return conn.isValid(5);
        } catch (Exception e) {
            return false;
        }
    }
}
