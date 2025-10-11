FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY src /app/src
EXPOSE 8888
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8888"]

