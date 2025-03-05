# NProxy

![NProxy design](https://nproxy.tooka.com.br/design-v1.png)

## Features

This project aims to create a secure and efficient environment for API exposure, essential for organizations looking to deliver reliable services in the digital age.

- **Efficient Reverse Proxy:** Utilizes **OpenResty** as a reverse proxy to manage incoming and outgoing API traffic, ensuring high performance and scalability.
- **Advanced Security:** Incorporates **ModSecurity** for detection and prevention of common threats at the application layer, including SQL injections, cross-site scripting (XSS), and other common attacks.
- **Detailed Logging:** Maintains detailed logs of all transactions, facilitating audit and event analysis for proactive identification of potential threats or anomalous behavior.
- **Load Balancing:** Offers load balancing capabilities to evenly distribute requests among backend servers, improving resilience and operational efficiency.
- **Operational Simplicity:** Uses **OpenResty** to provide a lightweight, easily configurable, and maintainable solution, reducing operational overhead.
- **Scalability:** The modular architecture facilitates horizontal scalability, allowing expansion as demand for services increases.


## NProxy Distribution Formats

### Container Image
For containerized environments, NProxy is also available as a container image. This enables seamless deployment using container orchestration tools such as Docker or Kubernetes. Pull the NProxy container image from the registry and run it in your containerized environment.

```docker
docker run -it -p 5000:5000 -p 80:80 -p 443:443 \
liberatti/nproxy:latest
```

**Managment interface:** [http://localhost:5000](http://localhost:5000)

**Default Account:** admin@local **Password:** admin   

### Test security

#### Gotestwaf
GoTestWAF is a tool for API and OWASP attack simulation that supports a wide range of API protocols including REST, GraphQL, gRPC, SOAP, XMLRPC, and others.
[Know more](https://github.com/wallarm/gotestwaf)

```docker
docker run --rm -v ${PWD}/reports:/app/reports \
    wallarm/gotestwaf --url=https://<PUBLIC_ENDPOINT> --noEmailReport
```

## License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Related Projects

### OpenResty
OpenResty® is a full-fledged web platform that integrates our enhanced version of the Nginx core, our enhanced version of LuaJIT, many carefully written Lua libraries, lots of high quality 3rd-party Nginx modules, and most of their external dependencies. It is designed to help developers easily build scalable web applications, web services, and dynamic web gateways.
[Know more](https://openresty.org/en/)

### ModSecurity
ModSecurity is an open-source web application firewall (WAF) that operates as a module for the Apache, Nginx, and IIS web servers. It provides protection against various web security threats and attacks. Learn more about the 
[Know more](https://www.modsecurity.org/).