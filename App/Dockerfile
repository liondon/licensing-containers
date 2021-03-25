FROM python:3.8-slim

# establish working folder
WORKDIR /app

# add user and give ownership to workdir
RUN useradd -r -s /bin/bash worker
RUN chown -R worker:worker /app

USER worker

# set home & current env
ENV HOME /app
ENV PATH="/app/.local/bin:${PATH}"

RUN pip install Flask requests

# Copy the application contents
COPY . .

ENV AUTH_SERVER http://172.17.0.1:5000

CMD [ "python", "./app.py" ]
