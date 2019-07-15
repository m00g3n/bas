FROM python:alpine3.7

COPY start.py bas.sh requirements.txt ./app/
ADD bas ./app/bas/

ENV KUBECONFIG=/app/config

WORKDIR /app
RUN pip install -r requirements.txt
CMD [ "sh","/app/bas.sh" ]