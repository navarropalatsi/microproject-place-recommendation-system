# BASE IMAGE
FROM python:3.11-slim

# METADATA
LABEL org.opencontainers.image.title="Place Recommendation System"
LABEL org.opencontainers.image.authors="joannavarropalatsi@gmail.com"
LABEL org.opencontainers.image.url="https://github.com/navarropalatsi/microproject-place-recommendation-system"
LABEL org.opencontainers.image.source="https://github.com/navarropalatsi/microproject-place-recommendation-system"
LABEL org.opencontainers.image.vendor="Joan Navarro Palatsi"

# AVOID .pyc FILES AND ENABLE REAL TIME LOGGING
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# SETUP ENVIRONMENT
WORKDIR /code
COPY "./requirements.txt" "/code/requirements.txt"
COPY "./neo4j_setup" "/code/neo4j_setup"

# INSTALL DEPENDENCIES
RUN pip install --no-cache-dir -r /code/requirements.txt

# MOVE SOURCE CODE
COPY ./app /code/app

# EXPOSE PORTS
EXPOSE 80

# RUN
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]