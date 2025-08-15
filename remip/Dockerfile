# Builder image
FROM python:3.11 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config

# Set working directory
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install app and dependencies into the system site-packages
RUN pip install --no-cache-dir .


# Production image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the necessary installed packages and application code from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /app /app


# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application via python -m so we don't rely on entrypoint scripts
CMD ["python", "-m", "uvicorn", "remip.main:app", "--host", "0.0.0.0", "--port", "8000"]
