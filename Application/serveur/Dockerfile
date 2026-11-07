FROM python:3.13-slim
WORKDIR /app
COPY app.py /app/app.py
RUN useradd -r -u 10001 forgely && mkdir /data && chown forgely:forgely /data
USER forgely
ENV PYTHONDONTWRITEBYTECODE=1 FORGELY_BIND=0.0.0.0 FORGELY_DB=/data/forgely.sqlite3
EXPOSE 8080
CMD ["python", "app.py"]
