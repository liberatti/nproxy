FROM php:8.2-fpm
COPY index.php /var/www/html/
COPY www.conf /usr/local/etc/php-fpm.d/
EXPOSE 9000

ENTRYPOINT [ "php-fpm" ]