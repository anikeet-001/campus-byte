FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/backend
RUN useradd --system --uid 10001 app && mkdir /data && chown app /data
USER app
ENV DB_PATH=/data/campus.sqlite
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
