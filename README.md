# Fuchs Register

A Django web application for tracking financial operations, sales, and client management. Features multi-language support and role-based access control.

## Features

- **Sales Management**: Point-of-sale interface for creating purchase operations
- **Operations Tracking**: Full CRUD operations with filtering and pagination
- **Debt Management**: Track and manage client debts with payment functionality
- **Statistics**: Visual charts showing income/expenses aggregation by day/month
- **Multi-language Support**: English, German, and Russian translations
- **Role-based Access**: Admin and regular user roles with different permissions

## Requirements

- Python 3.10+
- Django 5.2+

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fuchs-register
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Compile translation messages**
   ```bash
   python manage.py compilemessages
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main app: http://127.0.0.1:8000/register/
   - Admin panel: http://127.0.0.1:8000/admin/

## Initial Setup

After installation, you need to set up some initial data:

1. Log in to the Django admin panel at `/admin/`
2. Create operation types (e.g., PURCHASE, EXPENSE, DEBT return)
3. Add products with names and prices
4. Create a `CurrentBalance` record with initial amount and debt values
5. Optionally, create an "admins" group and assign users for admin access

## User Roles

- **Regular users**: Can access sales page and view operations/statistics (read-only)
- **Admin users**: Full access to create, edit, and manage operations
  - Must be either a superuser or member of the "admins" group

## URL Routes

| URL | Description |
|-----|-------------|
| `/register/` | Redirects to sales page |
| `/register/sales/` | Sales entry interface |
| `/register/operations/` | Operations list with filtering |
| `/register/statistics/` | Statistics and charts |
| `/register/debts/` | Debt management |
| `/admin/` | Django admin panel |
| `/i18n/setlang/` | Language switching |

## Project Structure

```
fuchs-register/
├── fuchs-register/      # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── register/            # Main Django app
│   ├── models.py        # Data models
│   ├── views.py         # View functions
│   ├── urls.py          # App URL routes
│   ├── templates/       # HTML templates
│   └── static/          # CSS files
├── locale/              # Translation files
│   ├── de/              # German
│   ├── en/              # English
│   └── ru/              # Russian
└── manage.py
```

## Development

### Adding new translations

1. Mark strings for translation in templates using `{% trans "string" %}`
2. Extract messages:
   ```bash
   python manage.py makemessages -l <language_code>
   ```
3. Edit the `.po` file in `locale/<language_code>/LC_MESSAGES/`
4. Compile messages:
   ```bash
   python manage.py compilemessages
   ```

## License

This project is proprietary software.
