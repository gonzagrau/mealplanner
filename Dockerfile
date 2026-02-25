FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Default: run the CLI help
ENTRYPOINT ["python", "main.py"]
CMD ["generate", "--days", "7", "--seed", "42"]

# To run the Streamlit UI instead, override the command:
#   docker run -p 8501:8501 mealplanner streamlit run app/streamlit_app.py --server.address=0.0.0.0

