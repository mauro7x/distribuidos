FROM ubuntu
RUN apt-get update && apt-get install -y netcat
COPY . .
RUN chmod +x /run.sh
CMD ["/run.sh"]
