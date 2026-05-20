FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o agent .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates tzdata
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
COPY --from=builder /app/agent .
COPY --from=builder /app/configs ./configs
USER appuser
ENTRYPOINT ["./agent"]
