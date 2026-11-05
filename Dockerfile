FROM python:3.11-slim

WORKDIR /app

# Install dependencies from your requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn

# Copy all your code into the container
COPY . .

# Tell Fly.io which port to listen on
EXPOSE 8080

# Start the app using uvicorn
# NOTE: If your main file is named main.py and is in the root folder, use "main:app"
# If your main file is inside the 'app' folder (app/main.py), use "app.main:app"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
