FROM node:16-slim
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "serve", "--", "--port", "88", "--host", "0.0.0.0"]
