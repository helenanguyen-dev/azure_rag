FROM python:3.13-slim
RUN useradd -m app
WORKDIR /home/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py mcp_client.py ./
USER app
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--proxy-headers", "--forwarded-allow-ips", "*"]
