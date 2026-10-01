FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY riil_analysis ./riil_analysis
RUN pip install --no-cache-dir .
EXPOSE 8001
CMD ["uvicorn", "riil_analysis.main:app", "--host", "0.0.0.0", "--port", "8001"]
