# Multi-Tenant E-Commerce Platform

This is a comprehensive multi-tenant e-commerce platform built with Python and Django, designed to host multiple independent stores on a single codebase. The project leverages a modern, containerized architecture with advanced features like a real-time search engine and asynchronous task processing.

---

## Core Features

- **Multi-Tenancy Architecture:** Uses `django-tenants` to provide complete data isolation for each store via PostgreSQL schemas.
- **Full E-Commerce Flow:** Complete user journey from product viewing, cart management, to a real payment process using Stripe.
- **Elasticsearch Integration:** A powerful, typo-tolerant, and fast search engine for the product catalog.
- **Asynchronous Tasks:** Uses Celery and Redis to handle time-consuming tasks like sending order confirmation emails in the background.
- **REST API:** A secure, read-write API built with Django REST Framework for programmatic access to the product catalog.
- **Dockerized Environment:** The entire application stack (Django, PostgreSQL, Elasticsearch, Redis, Celery) is containerized with Docker and Docker Compose for a consistent and portable development environment.
- **Continuous Integration (CI):** An automated testing pipeline using GitHub Actions to ensure code quality and reliability.

---

## Technology Stack

- **Backend:** Python, Django, Django REST Framework
- **Database:** PostgreSQL
- **Multi-Tenancy:** django-tenants
- **Search Engine:** Elasticsearch
- **Task Queue:** Celery, Redis
- **Payment Gateway:** Stripe
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions

---

## Local Setup & Installation

1.  **Prerequisites:**
    - Docker
    - Docker Compose

2.  **Clone the repository:**
    ```bash
    git clone [https://github.com/SerhatFiliz/multi_tenant_shop.git](https://github.com/SerhatFiliz/multi_tenant_shop.git)
    cd multi_tenant_shop
    ```

3.  **Environment Variables:**
    - Rename the `.env.example` file to `.env`.
    - Fill in the required values (especially `SECRET_KEY` and your Stripe API keys).

4.  **Build and Run the Containers:**
    ```bash
    docker-compose build
    docker-compose up
    ```

5.  **Initial Database Setup (Run in a separate terminal):**
    - Apply shared migrations:
      ```bash
      docker-compose exec web python manage.py migrate_schemas --shared
      ```
    - Create a superuser:
      ```bash
      docker-compose exec web python manage.py createsuperuser
      ```
    - Create the first tenant (run inside the shell):
      ```bash
      docker-compose exec web python manage.py shell
      # ... (paste the tenant creation script here) ...
      ```

6.  **Accessing the Application:**
    - **Main Store:** `http://inciboncuk.localhost:8000/` (You may need to edit your local `hosts` file).
    - **Admin Panel:** `http://localhost:8000/admin/`
    - **API:** `http://inciboncuk.localhost:8000/api/products/`
    - **Kibana:** `http://localhost:5601/`

