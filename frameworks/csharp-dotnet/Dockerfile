# Build stage
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build

# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up
ENV TMPDIR=/data/tmp
RUN mkdir -p /data/tmp
WORKDIR /src

# Copy csproj and restore dependencies
COPY ["FraiseQL.Benchmark/FraiseQL.Benchmark.csproj", "."]
RUN dotnet restore "FraiseQL.Benchmark.csproj"

# Copy everything else and build
COPY . .
RUN dotnet build "FraiseQL.Benchmark/FraiseQL.Benchmark.csproj" -c Release -o /app/build

# Publish
FROM build AS publish
RUN dotnet publish "FraiseQL.Benchmark/FraiseQL.Benchmark.csproj" -c Release -o /app/publish --no-restore

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
ENTRYPOINT ["dotnet", "FraiseQL.Benchmark.dll"]