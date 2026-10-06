# Daily Tea 📰

> Your daily dose of what's happening.

Daily Tea is a Django-based news application that allows readers to access approved news articles and newsletters, while journalists and editors manage news content through role-based permissions.

The project includes publisher management, reader subscriptions, an editor-controlled article approval  workflow, independent journalist publishing, a REST API, token authentication, subscriber notifications, automated testing, and MySQL-compatible database integration.

---

## Features

- User registration and authentication
- Role-based access control
- Reader, Journalist and Editor roles
- Publisher creation and management
- Assignment of editors and journalists to publishers
- Article creation and management
- Publisher article approval workflow
- Independent journalist article publishing
- Newsletter creation and management
- Publisher subscriptions
- Journalist subscriptions
- Subscriber article feed
- Email notifications when articles are approved
- Internal REST API integration after article approval
- Django REST Framework API
- Token authentication
- Automated API and application tests
- MariaDB database
- Responsive web interface

---

## User Roles

### Reader

Readers can:

- View approved articles
- View newsletters
- Subscribe to publishers
- Subscribe to journalists
- View articles from their subscriptions

Readers cannot create, edit, delete or approve articles.

### Journalist

Journalists can:

- Create articles
- View their articles
- Edit their own articles
- Delete their own articles
- Publish their own independent articles
- Create newsletters
- Edit their own newsletters
- Delete their own newsletters

Journalists can be assigned to publishers by an editor.

Articles associated with a publisher require editor approval before becoming publicly available.

Independent articles that are not associated with a publisher can be published directly by the journalist who created them.

### Editor

Editors can:

- View articles awaiting approval
- Approve publisher articles
- Edit articles
- Delete articles
- Create newsletters
- Edit newsletters
- Delete newsletters
- Create and manage publishers
- Assign journalists to publishers
- Assign editors to publishers

Editors control the approval workflow for publisher-associated articles.

---

## Publisher Management

Editors can create and manage publishers through the publisher management section.

A publisher can have:

- A name
- A description
- Multiple editors
- Multiple journalists

Editors can assign journalists and editors to a publisher when creating or managing the publisher.

Journalists assigned to a publisher can select that publisher when creating an article.

---

## Reader Subscriptions

Readers can manage their subscriptions from the **My Subscriptions** page.

Readers can subscribe to:

- Publishers
- Individual journalists

The subscribed article feed returns approved articles from the publishers and journalists selected by the reader.

---

## Article Approval Workflow

Daily Tea uses two article publishing workflows.

### Publisher Articles

1. A journalist creates an article associated with a publisher.
2. The article is initially unapproved.
3. The article appears in the Editor Dashboard.
4. An editor reviews the article.
5. The editor approves the article.
6. The article becomes publicly available.
7. Subscribers are notified by email.
8. Daily Tea sends the approved article to its internal API endpoint.

### Independent Articles

1. A journalist creates an article without selecting a publisher.
2. The article is initially unapproved.
3. The article appears in the journalist's **My Articles** page as **Ready to Publish**.
4. The journalist can review the article and choose **Publish Article**.
5. The article becomes publicly available.
6. Subscribers are notified by email.
7. Daily Tea sends the approved article to its internal API endpoint.

Independent articles cannot be published through the independent publishing workflow by another journalist, a reader, or for an article that belongs to a publisher.

---

# REST API

The application provides a REST API using Django REST Framework.

## Authentication

Token authentication is available through:

```text
/api/token/
```

### Article endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/approved/` | Retrieve approved articles |
| GET | `/api/articles/` | Retrieve approved articles |
| GET | `/api/articles/subscribed/` | Retrieve approved articles matching reader subscriptions |
| GET | `/api/articles/<id>/` | Retrieve a single article |
| POST | `/api/articles/` | Create an article |
| PUT | `/api/articles/<id>/` | Update an article |
| DELETE | `/api/articles/<id>/` | Delete an article |

### Newsletter endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/newsletters/` | Retrieve newsletters |
| GET | `/api/newsletters/<id>/` | Retrieve a single newsletter |

The API applies role-based permissions to article creation, editing, deletion and approval.

## Technology Stack

- Python
- Django
- Django REST Framework
- MariaDB / MySQL
- HTML
- CSS
- Bootstrap
- Django Templates

## Installation

### 1. Get the project

Clone or download the project repository and navigate to the `Daily_Tea` directory.

```bash
git clone <repository-url>
cd Daily_Tea
```

If the repository has already been downloaded, open a terminal in the `Daily_Tea` directory.

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

If Command Prompt is being used instead:

```bat
venv\Scripts\activate
```

### 3. Install the required packages

Install the project dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

The project uses environment variables for the Django secret key, database connection and internal API authentication.

Create a `.env` file in the root of the `Daily_Tea` project.

The `.env` file should contain:

```text
SECRET_KEY=your-secret-key
DB_NAME=daily_tea
DB_USER=daily_tea_user
DB_PASSWORD=your-database-password
DB_HOST=127.0.0.1
DB_PORT=3306
DAILY_TEA_INTERNAL_API_KEY=your-internal-api-key
```

Generate a secure Django secret key and place it in the `SECRET_KEY` variable.

Do not use the example value `your-secret-key`.

The real secret key should not be committed to GitHub.

Create a secure random value for the internal API key and place it in `DAILY_TEA_INTERNAL_API_KEY`.

This key is used to authenticate the application's internal API request made after an article is approved or published.

Do not commit the real API key to GitHub.

The repository should only contain `.env.example` with placeholder values.

### 5. Create the MariaDB database

Make sure MariaDB is installed and running.

Create the database:

```sql
CREATE DATABASE daily_tea;
```

Create a database user:

```sql
CREATE USER 'daily_tea_user'@'localhost' IDENTIFIED BY 'your-database-password';
```

Grant the required permissions:

```sql
GRANT ALL PRIVILEGES ON daily_tea.* TO 'daily_tea_user'@'localhost';
```

Apply the privileges:

```sql
FLUSH PRIVILEGES;
```

The database credentials should match the values in `.env`.

### 6. Apply database migrations

Run:

```bash
python manage.py migrate
```

This creates the database tables required by Django and the Daily Tea application.

### 7. Create a superuser

Create an administrator account:

```bash
python manage.py createsuperuser
```

Follow the prompts to enter the username, email address and password.

### 8. Run the Django system check

Run:

```bash
python manage.py check
```

The project should report:

```text
System check identified no issues (0 silenced).
```

### 9. Run the automated tests

Run the complete test suite:

```bash
python manage.py test
```

The project includes automated tests covering registration, permissions, article workflows, publisher functionality, subscriptions, REST API functionality and approval/publishing behaviour.

### 10. Start the development server

Run:

```bash
python manage.py runserver
```

Open the development server in a browser:

```text
http://127.0.0.1:8000/
```

## Docker

Daily Tea can also be run using Docker Compose. The Docker configuration starts both the Django application and a MySQL 8.4 database container.

### Build the Docker image

```bash
docker compose build
```

### Start the application

```bash
docker compose up
```

The application will be available at:

```text
http://localhost:8000/
```

### Stop the containers

```bash
docker compose down
```

The MySQL database data is stored in a Docker volume so that it persists between container restarts.

## Documentation

The project includes Sphinx documentation for the main Daily Tea Python modules.

The documentation source files are stored in:

```text
docs/
```

The generated HTML documentation is stored in:

```text
docs/_build/
```

The main documentation page is:

```text
docs/_build/index.html
```

The Sphinx documentation uses the following extensions:

- `sphinx.ext.autodoc`
- `sphinx.ext.viewcode`
- `sphinx.ext.napoleon`

The documentation uses the Read the Docs theme.

## Environment Variables

The following environment variables are required:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django application security |
| `DB_NAME` | MariaDB / MySQL database name |
| `DB_USER` | MariaDB / MySQL database username |
| `DB_PASSWORD` | MariaDB / MySQL database password |
| `DB_HOST` | MariaDB / MySQL host |
| `DB_PORT` | MariaDB / MySQL port |
| `DAILY_TEA_INTERNAL_API_KEY` | Authentication for the internal API request |

Never commit the actual `.env` file or production secrets to the repository.

## Project Structure

```text
Daily_Tea/
│
├── daily_tea/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── news/
│   ├── migrations/
│   ├── templates/
│   │   └── news/
│   ├── api_views.py
│   ├── api_urls.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── docs/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

The application includes automated tests for:

- User registration
- Role assignment
- Duplicate email validation
- Article creation
- Article editing
- Article deletion
- Publisher article approval
- Independent article publishing
- Role-based permissions
- Publisher management
- Reader subscriptions
- Subscriber article filtering
- REST API authentication
- REST API permissions
- Newsletter functionality
- Subscriber notifications
- Internal API integration

Run all tests with:

```bash
python manage.py test
```

## Security

Sensitive configuration values are stored using environment variables.

The following values must not be committed to the repository:

- Django `SECRET_KEY`
- Database passwords
- `DAILY_TEA_INTERNAL_API_KEY`
- Other production credentials

Use `.env.example` as a template for local configuration.

## Development Notes

Daily Tea uses MariaDB as its production database configuration.

The application uses Django's built-in authentication system together with role-based permissions and Django REST Framework token authentication.

Publisher-associated articles follow the editor approval workflow, while independent journalist articles can be published directly by their author.

## License

This project was created as part of the HyperionDev Software Engineering course.
