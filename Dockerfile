# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install dependencies using uv
RUN pip install uv
RUN uv pip install --system .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
CMD ["uvicorn", "remip.main:app", "--host", "0.0.0.0", "--port", "8000"]
