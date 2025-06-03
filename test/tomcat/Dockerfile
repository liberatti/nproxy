FROM tomcat:9.0-jdk11-openjdk

# Remove default webapps
RUN rm -rf /usr/local/tomcat/webapps/*

# Copy our web application
COPY webapp/ /usr/local/tomcat/webapps/ROOT/

# Change Tomcat port to 5011
RUN sed -i 's/port="8080"/port="5011"/' /usr/local/tomcat/conf/server.xml

# Expose port 5011
EXPOSE 5011

# Start Tomcat
CMD ["catalina.sh", "run"] 