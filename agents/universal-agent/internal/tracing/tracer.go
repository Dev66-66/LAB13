package tracing

import (
	"context"
	"fmt"
	"net/url"
	"os"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

// InitTracer инициализирует OpenTelemetry TracerProvider с OTLP HTTP-экспортёром
// для отправки трейсов в Jaeger. Вызывающий обязан вызвать defer tp.Shutdown(ctx).
func InitTracer(serviceName string) (*sdktrace.TracerProvider, error) {
	ctx := context.Background()

	exporter, err := otlptracehttp.New(ctx,
		otlptracehttp.WithEndpoint(resolveEndpoint(os.Getenv("JAEGER_ENDPOINT"))),
		otlptracehttp.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("не удалось создать OTLP-экспортёр: %w", err)
	}

	res, err := resource.New(ctx,
		resource.WithAttributes(
			attribute.String("service.name", serviceName),
			attribute.String("service.version", "1.0.0"),
		),
	)
	if err != nil {
		_ = exporter.Shutdown(ctx)
		return nil, fmt.Errorf("не удалось создать resource: %w", err)
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
	)
	return tp, nil
}

// resolveEndpoint извлекает host:port из URL-строки, либо возвращает дефолтный адрес.
func resolveEndpoint(raw string) string {
	if raw == "" {
		return "jaeger:4318"
	}
	u, err := url.Parse(raw)
	if err != nil || u.Host == "" {
		return raw
	}
	return u.Host
}
