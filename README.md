# NProxy 


[This project](https://nproxy.app.br) aims to create a secure and efficient environment for API exposure, essential for organizations looking to
deliver reliable services in the digital age.

- **Efficient Reverse Proxy:** Utilizes **OpenResty** as a reverse proxy to manage incoming and outgoing API traffic,
  ensuring high performance and scalability.
- **Advanced Security:** Incorporates **ModSecurity** for detection and prevention of common threats at the application
  layer, including SQL injections, cross-site scripting (XSS), and other common attacks.
- **Detailed Logging:** Maintains detailed logs of all transactions, facilitating audit and event analysis for proactive
  identification of potential threats or anomalous behavior.
- **Load Balancing:** Offers load balancing capabilities to evenly distribute requests among backend servers, improving
  resilience and operational efficiency.
- **Operational Simplicity:** Uses **OpenResty** to provide a lightweight, easily configurable, and maintainable
  solution, reducing operational overhead.
- **Scalability:** The modular architecture facilitates horizontal scalability, allowing expansion as demand for
  services increases.

## NProxy Distribution Formats

### Container Image

Pull the NProxy container image from the registry and run it in your containerized environment.

> Docker environment

```docker
docker run -it \
 -e MONGO_HOST="<mongo ipaddr>"\
 -e MONGO_PORT=27017\
 -e MONGO_DB="nproxy"\
 -e MONGO_USER="nproxy_usr"\
 -e MONGO_PASS="xxxxxxxxxxxxxxxxxxx"\
 -e NODE_KEY="xxxxxxxxxxxxxxxxxxx"\
 -e NODE_ROLE="main"\
 -e SERVERID="nproxy-node01"\
 -p 5000:5000 \
 -p 80:80 
 -p 443:443 \
liberatti/nproxy:latest
```

> Docker Compose Minimal

```docker
volumes:
  mongo-data:
    driver: local

services:
  proxy:
    depends_on:
      - db
    image: liberatti/nproxy:v1.0.2-rc
    environment:
      MONGO_HOST: db
      MONGO_PORT: 27017
      MONGO_DB: nproxy
      MONGO_USER: nproxy_usr
      MONGO_PASS: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      SERVERID: "srv-001"
      NODE_ROLE: main
      NODE_KEY: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ports:
      - "80:80"
      - "443:443"
      - "5000:5000"
    extra_hosts:
      - "host.docker.internal:host-gateway"

  db:
    image: mongodb/mongodb-community-server:7.0.1-ubuntu2204
    environment:
      MONGO_INITDB_ROOT_USERNAME: nproxy_usr
      MONGO_INITDB_ROOT_PASSWORD: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    command: --quiet
    logging:
      driver: "none"
    volumes:
      - mongo-data:/data/db
    ports:
      - "27017:27017"
``` 


**Managment interface: ** [http://localhost:5000](http://localhost:5000)

**Default Account:** admin@local **Password:** admin

## Test security

### Gotestwaf

GoTestWAF is a tool for API and OWASP attack simulation that supports a wide range of API protocols including REST,
GraphQL, gRPC, SOAP, XMLRPC, and others.
[Know more](https://github.com/wallarm/gotestwaf)

```docker
docker run --rm -v ${PWD}/reports:/app/reports \
    wallarm/gotestwaf --url=https://<PUBLIC_ENDPOINT> --noEmailReport
```

## ID Reservations

- 1-99,999; reserved for local (internal) use. Use as you see fit but do not use this range for rules that are
  distributed to others.
    - 10 - Sensor config
    - 12 - Method is not allowed by route
    - 50 - ModSecurity internal error
    - 51 - Multipart parser detected a possible unmatched boundary
    - 52 - requestBodyProcessor=XML
    - 53 - requestBodyProcessor=JSON
    - 55 - Failed to parse request body. JSON
- 100,000–199,999; reserved for rules published by Oracle.
- 200,000–299,999; reserved for rules published Comodo.
- 300,000-399,999; reserved for rules published at gotroot.com.
- 400,000–419,999; unused (available for reservation).
- 420,000-429,999; reserved for ScallyWhack .
- 430,000–439,999: reserved for rules published by Flameeyes
- 440,000-599,999; unused (available for reservation).
- 600,000-699,999; reserved for use by Akamai http://www.akamai.com/html/solutions/waf.html
- 700,000-799,999; reserved for Ivan Ristic.
- 900,000-999,999; reserved for the OWASP ModSecurity Core Rule Set project.
- 1,000,000-1,009,999; reserved for rules published by Redhat Security Team
- 1,010,000-1,999,999; unused (available for reservation)
- 2,000,000-2,999,999; reserved for rules from Trustwave's SpiderLabs Research team
- 3,000,000-3,999,999; reserved for use by Akamai
- 4,000,000-4,099,999; reserved in use by AviNetworks
- 4,100,000-4,199,999; reserved in use by Fastly
- 4,200,000 and above; unused (available for reservation)

## Telemetry Notice

To enhance our services, we have implemented telemetry that tracks the total traffic over the last 24 hours of usage. We
want to assure you that no sensitive or personal data is collected during this process. The data gathered helps us
identify areas for improvement and deliver a better experience for our users.

## License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Related Projects

### OpenResty

OpenResty® is a full-fledged web platform that integrates our enhanced version of the Nginx core, our enhanced version
of LuaJIT, many carefully written Lua libraries, lots of high quality 3rd-party Nginx modules, and most of their
external dependencies. It is designed to help developers easily build scalable web applications, web services, and
dynamic web gateways.
[Know more](https://openresty.org/en/)

### ModSecurity

ModSecurity is an open-source web application firewall (WAF) that operates as a module for the Apache, Nginx, and IIS
web servers. It provides protection against various web security threats and attacks. Learn more about the
[Know more](https://www.modsecurity.org/).