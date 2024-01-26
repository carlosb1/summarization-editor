FROM rust:1.75 as base
RUN rustup target add wasm32-unknown-unknown
RUN cargo install trunk


FROM base as builder
WORKDIR /app
# Copy and build the frontend
COPY . .
RUN cargo build --target wasm32-unknown-unknown --release
RUN trunk build --release

# Use Nginx to serve the built frontend
FROM nginx:1.21
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
