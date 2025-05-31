FROM php:8.2-fpm
COPY index.php /var/www/html/


# Ensure no other configs are overriding our port
RUN sed -i 's/listen = 9000/listen = 5010/g' /usr/local/etc/php-fpm.conf && \
    sed -i 's/listen = 9000/listen = 5010/g' /usr/local/etc/php-fpm.d/*.conf

EXPOSE 5010

# Force PHP-FPM to use port 5010
CMD ["php-fpm", "--nodaemonize"]