FROM nginx:1.27.4-alpine

COPY jjj_food_chain/docker/sysctl/nginx.conf /etc/nginx/nginx.conf
COPY jjj_food_chain/docker/nginx/* /etc/nginx/conf.d/
COPY jjj_food_chain/public/ /var/www/public/
WORKDIR /var/www/
RUN chown -R nginx:nginx /var/www/public/
EXPOSE 80
CMD [ "nginx", "-g", "daemon off;" ]