# Assignment Store App

This is a fresh web application for DevOps Assignment 3. It uses Flask for the web app and PostgreSQL as the database server.

## Assignment Fit

- Web application with database server: Flask + PostgreSQL
- Containerized deployment: Dockerfile + Docker Compose
- Selenium-ready UI: stable element IDs and `data-testid` attributes
- Jenkins-ready pipeline: Jenkinsfile included
- Manager page supports product CRUD and order status updates

## Run Locally With Docker

```bash
docker compose up --build
```

Open the app:

```text
http://localhost:8081
```

Manager login:

```text
http://localhost:8081/manager-login
```

Default manager password:

```text
admin123
```

Stop the app:

```bash
docker compose down
```

## Useful URLs

- Storefront: `/`
- Manager login: `/manager-login`
- Manager panel: `/manager`
- Health check: `/health`

## Selenium Test Ideas

This app supports at least 15 test cases:

1. Storefront page loads.
2. Product cards are visible.
3. Search filters products.
4. Category filter works.
5. Reset filter returns all products.
6. Valid order can be placed.
7. Empty order fields show validation.
8. Invalid quantity is rejected.
9. Out of stock product cannot be ordered.
10. Manager login page loads.
11. Incorrect manager password is rejected.
12. Correct manager password opens manager panel.
13. Product can be created.
14. Duplicate product name is rejected.
15. Product can be edited.
16. Product can be deleted.
17. Order status can be updated.
18. Manager logout works.

## GitHub Setup

Create a GitHub repository for this app, then run:

```bash
git init
git add .
git commit -m "Add PostgreSQL storefront app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_APP_REPO.git
git push -u origin main
```

Before final Jenkins submission, update `TEST_REPO_URL` in `Jenkinsfile` with your Selenium test repository URL.
