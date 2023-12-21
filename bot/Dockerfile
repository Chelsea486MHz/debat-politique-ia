FROM node:18

# Configure app directory
RUN mkdir -p /home/node/app/node_modules && \
    chown -R node:node /home/node/app

WORKDIR /home/node/app
EXPOSE 8080

# Install dependencies
COPY package*.json ./
RUN npm install

COPY --chown=node:node app.js /home/node/app/app.js

# Run it
USER node
CMD [ "node", "app.js" ]