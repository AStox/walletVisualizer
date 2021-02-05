FROM node:latest as build

ENV PORT=80

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY package.json /usr/src/app

RUN yarn install --production

COPY . /usr/src/app

RUN ls public/

RUN yarn build

FROM nginx:alpine
COPY --from=build /usr/src/app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD sed -i -e 's/${PORT}/'"$PORT"'/g' /etc/nginx/nginx.conf && nginx -g 'daemon off;'