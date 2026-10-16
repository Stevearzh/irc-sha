From python:3.12-slim

ADD . /irc-sha

WORKDIR /irc-sha

RUN pip install --no-cache-dir -e '.[dev]'

CMD ["python"]
