<?php

namespace VelocityBench\HealthCheck;

/**
 * Individual health check result.
 */
class HealthCheck implements \JsonSerializable
{
    public function __construct(
        public HealthStatus $status,
        public ?float $responseTimeMs = null,
        public ?string $error = null,
        public ?string $warning = null,
        public ?string $info = null,
        public array $additionalData = []
    ) {
    }

    public function withResponseTime(float $ms): self
    {
        $this->responseTimeMs = $ms;
        return $this;
    }

    public function withError(string $error): self
    {
        $this->error = $error;
        return $this;
    }

    public function withWarning(string $warning): self
    {
        $this->warning = $warning;
        return $this;
    }

    public function withInfo(string $info): self
    {
        $this->info = $info;
        return $this;
    }

    public function withData(string $key, mixed $value): self
    {
        $this->additionalData[$key] = $value;
        return $this;
    }

    public function jsonSerialize(): array
    {
        $data = ['status' => $this->status->value];

        if ($this->responseTimeMs !== null) {
            $data['response_time_ms'] = $this->responseTimeMs;
        }
        if ($this->error !== null) {
            $data['error'] = $this->error;
        }
        if ($this->warning !== null) {
            $data['warning'] = $this->warning;
        }
        if ($this->info !== null) {
            $data['info'] = $this->info;
        }

        return array_merge($data, $this->additionalData);
    }
}
