FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DOCUGRAPH_DATA=/app/demo_data
WORKDIR /app
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"
COPY src ./src
COPY demo_data ./demo_data
RUN useradd --create-home app && chown -R app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn docugraph.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]