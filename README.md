# User Profile Audit

## Project Purpose
The User Profile Audit project is designed to provide a robust backend solution for managing user profiles and auditing changes made to them. This application allows for the creation, updating, retrieval, and deletion of user profiles while maintaining a comprehensive audit trail of all actions performed on these profiles. It aims to enhance data integrity and accountability within user management systems.

## Features
- Create, read, update, and delete user profiles.
- Audit logging for all actions performed on user profiles.
- Retrieve active and deleted user profiles.
- Rollback changes to user profiles based on audit events.
- User authentication and authorization for secure access.
- Comprehensive API documentation for easy integration.

## Getting Started

### Prerequisites
- Docker installed on your machine.
- Docker Compose (comes with Docker Desktop).

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/jaozc/user-profile-audit.git
   cd user-profile-audit
   ```

2. Build and run the application using Docker:
   ```bash
   docker-compose up --build
   ```

   This command will:
   - Build the Docker images defined in the `docker-compose.yml` file.
   - Start the application and the PostgreSQL database in separate containers.

### PostgreSQL Setup
The application uses PostgreSQL as its database. The database configuration is defined in the `docker-compose.yml` file. By default, the application will connect to a PostgreSQL instance running in a Docker container.

- **Database Name**: `audit_db`
- **User**: `audit_user`
- **Password**: `password`
- **Host**: `db` (the name of the PostgreSQL service in Docker)

### Accessing the Application
Once the application is running, you can access the API documentation at `http://127.0.0.1:8000/docs`.

## Running Tests
To run the tests within the Docker container, use the following command:
```bash
docker exec -it audit_api pytest tests -v
```

This command will:
- Execute the `pytest` testing framework inside the running Docker container named `audit_api`.
- The `-v` flag enables verbose output, providing detailed information about the tests being run.

## Usage
Once the application is running, you can interact with the API using tools like Postman or directly through the Swagger UI provided at the `/docs` endpoint.

## Default Authentication Credentials

For testing purposes, the application includes default authentication credentials:

- **Username**: `test`
- **Password**: `secret`

You can use these credentials to access the API and test the functionality without needing to create a new user profile.

### Example Usage
When making requests to the API, include the credentials in the Authorization header:

```http
Authorization: Bearer test
```

## Copyright
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Credits
- Developed by [Joao Costa](https://github.com/jaozc)
- Inspired by the need for efficient user management and auditing in backend systems.

## Acknowledgments
- Thanks to the FastAPI community for their excellent documentation and support.
- Special thanks to contributors and testers who helped improve the project.

## Additional Information
For any issues or feature requests, please open an issue in the GitHub repository. Contributions are welcome!
