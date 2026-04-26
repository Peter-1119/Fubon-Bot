FROM python:3.10-slim
WORKDIR /app

# 1. 強迫 Python 即時輸出，絕不囤積！
ENV PYTHONUNBUFFERED=1

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# 2. 完美的 JSON 格式 CMD，並要求 Gunicorn 把所有訊息直接噴在螢幕上
CMD ["sh", "-c", "exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --access-logfile - --error-logfile - --capture-output --enable-stdio-inheritance main:app"]