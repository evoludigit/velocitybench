package com.velocitybench.controller;

import io.agroal.api.AgroalDataSource;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.sql.Connection;
import java.util.Map;

@Path("/")
public class HealthResource {

    @Inject
    AgroalDataSource dataSource;

    @GET
    @Path("/health")
    @Produces(MediaType.APPLICATION_JSON)
    public Response health() {
        boolean healthy = checkDatabase();
        Map<String, String> response = Map.of(
            "status", healthy ? "healthy" : "unhealthy",
            "framework", "quarkus-graphql"
        );
        return healthy
            ? Response.ok(response).build()
            : Response.serverError().entity(response).build();
    }

    @GET
    @Path("/metrics")
    @Produces(MediaType.TEXT_PLAIN)
    public String metrics() {
        return """
            # HELP quarkus_requests_total Total number of GraphQL requests
            # TYPE quarkus_requests_total counter
            quarkus_requests_total 0
            # HELP quarkus_db_pool_size Database connection pool size
            # TYPE quarkus_db_pool_size gauge
            quarkus_db_pool_size 50
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
