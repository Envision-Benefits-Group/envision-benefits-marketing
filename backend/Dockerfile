# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory to /app
WORKDIR /app

# Install curl to download uv
RUN apt-get update && apt-get install -y curl

# Download and install uv
ADD --chmod=755 https://astral.sh/uv/0.6.10/install.sh /install.sh
RUN /install.sh && rm /install.sh

# Ensure the uv binary is on the PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the dependencies using uv
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose port 8000 for the application
EXPOSE 8000

# Set the default command to run the driver.py file
CMD ["python", "driver.py"]
