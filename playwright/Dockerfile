FROM mcr.microsoft.com/playwright:v1.56.1-jammy

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .

CMD ["npx", "playwright", "test", "--reporter=line", "tests"]
