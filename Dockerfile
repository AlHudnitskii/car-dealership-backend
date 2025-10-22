FROM python:3.11-slim as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libgdal-dev \
    && pip install pipenv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY Pipfile Pipfile.lock /usr/src/app/

RUN pipenv install --system --ignore-pipfile --dev


FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        libgdal-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

COPY . /usr/src/app/
ENV DJANGO_SETTINGS_MODULE=config.settings.local
ENV PYTHONUNBUFFERED 1

RUN groupadd -r django_group && \
    useradd -r -g django_group -s /bin/false django_user
USER django_user

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

ENTRYPOINT ["python"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]