FROM python:3.10-slim

WORKDIR /app

# Install minimal deps for light_api (no torch!)
RUN pip install --no-cache-dir flask flask-cors requests

# Copy the API
COPY light_api.py /app/light_api.py

# HuggingFace Spaces requires port 7860
ENV PORT=7860
ENV HOST=0.0.0.0

EXPOSE 7860

# Run as non-root user
RUN useradd -m evo
USER evo

CMD ["python", "light_api.py"]
