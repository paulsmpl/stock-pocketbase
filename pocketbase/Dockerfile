FROM alpine:3.20

RUN apk add --no-cache curl unzip python3 py3-requests bash

WORKDIR /pb

# Télécharger PocketBase
RUN curl -L https://github.com/pocketbase/pocketbase/releases/download/v0.22.20/pocketbase_0.22.20_linux_amd64.zip -o pb.zip \
 && unzip pb.zip \
 && rm pb.zip \
 && chmod +x /pb/pocketbase

# Copier les fichiers d'initialisation
COPY init_collections.py /pb/init_collections.py
COPY products.json /pb/products.json
COPY variants.json /pb/variants.json
COPY inventory.json /pb/inventory.json
COPY movements.json /pb/movements.json

# Note: stock_initial.csv et cost_mapping.csv seront montés via volumes dans docker-compose.yml

EXPOSE 8090

# Commande par défaut (override par docker-compose)
CMD ["/pb/pocketbase", "serve", "--http=0.0.0.0:8090"]