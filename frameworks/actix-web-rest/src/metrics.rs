use lazy_static::lazy_static;
use prometheus::{Counter, Encoder, Histogram, HistogramOpts, Registry, TextEncoder};

lazy_static! {
    pub static ref METRICS_REGISTRY: Registry = Registry::new();

    // HTTP request counter
    pub static ref HTTP_REQUESTS_TOTAL: Counter = Counter::new(
        "actix_web_rest_requests_total",
        "Total number of HTTP requests"
    ).expect("Failed to create HTTP_REQUESTS_TOTAL counter");

    // HTTP request duration histogram
    pub static ref HTTP_REQUEST_DURATION_SECONDS: Histogram = Histogram::with_opts(
        HistogramOpts::new(
            "actix_web_rest_request_duration_seconds",
            "HTTP request duration in seconds"
        )
    ).expect("Failed to create HTTP_REQUEST_DURATION_SECONDS histogram");

    // HTTP error counter
    pub static ref HTTP_REQUESTS_ERRORS_TOTAL: Counter = Counter::new(
        "actix_web_rest_requests_errors_total",
        "Total number of HTTP request errors"
    ).expect("Failed to create HTTP_REQUESTS_ERRORS_TOTAL counter");
}

pub fn init_metrics() -> Result<(), Box<dyn std::error::Error>> {
    // Register metrics with the registry
    METRICS_REGISTRY.register(Box::new(HTTP_REQUESTS_TOTAL.clone()))?;
    METRICS_REGISTRY.register(Box::new(HTTP_REQUEST_DURATION_SECONDS.clone()))?;
    METRICS_REGISTRY.register(Box::new(HTTP_REQUESTS_ERRORS_TOTAL.clone()))?;

    Ok(())
}

pub fn encode_metrics() -> Result<String, Box<dyn std::error::Error>> {
    let encoder = TextEncoder::new();
    let metric_families = METRICS_REGISTRY.gather();
    let mut buffer = Vec::new();
    encoder.encode(&metric_families, &mut buffer)?;
    Ok(String::from_utf8(buffer)?)
}

#[allow(dead_code)]
pub fn record_request(_endpoint: &str, _method: &str, status: u16, duration: f64) {
    // Increment total requests counter
    HTTP_REQUESTS_TOTAL.inc();

    // Record request duration
    HTTP_REQUEST_DURATION_SECONDS.observe(duration);

    // Record errors if status >= 400
    if status >= 400 {
        HTTP_REQUESTS_ERRORS_TOTAL.inc();
    }
}
