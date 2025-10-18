FROM alpine:3.20
RUN apk add --no-cache curl unzip python3 py3-requests
WORKDIR /pb
RUN curl -L https://github.com/pocketbase/pocketbase/releases/download/v0.22.14/pocketbase_0.22.14_linux_amd64.zip -o pb.zip \
 && unzip pb.zip && rm pb.zip
COPY init_collections.py /pb/init_collections.py
COPY products.json /pb/products.json
COPY variants.json /pb/variants.json
COPY inventory.json /pb/inventory.json
COPY movements.json /pb/movements.json
EXPOSE 8090
