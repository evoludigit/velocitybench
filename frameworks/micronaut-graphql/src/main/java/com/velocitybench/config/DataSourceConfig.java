package com.velocitybench.config;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import io.micronaut.context.annotation.Bean;
import io.micronaut.context.annotation.Factory;
import io.micronaut.context.annotation.Primary;
import jakarta.inject.Singleton;

import javax.sql.DataSource;

@Factory
public class DataSourceConfig {

    @Bean
    @Singleton
    @Primary
    public DataSource dataSource() {
        String host = System.getenv().getOrDefault("DB_HOST", "localhost");
        String port = System.getenv().getOrDefault("DB_PORT", "5432");
        String name = System.getenv().getOrDefault("DB_NAME", "velocitybench_benchmark");
        String user = System.getenv().getOrDefault("DB_USER", "benchmark");
        String pass = System.getenv().getOrDefault("DB_PASSWORD", "benchmark123");

        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:postgresql://" + host + ":" + port + "/" + name);
        config.setUsername(user);
        config.setPassword(pass);
        config.setDriverClassName("org.postgresql.Driver");
        config.setConnectionInitSql("SET search_path TO benchmark, public");
        config.setMinimumIdle(10);
        config.setMaximumPoolSize(50);

        return new HikariDataSource(config);
    }
}
