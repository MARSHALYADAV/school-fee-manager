# School Fee Management System

A Flask-based school fee management system migrated to MongoDB for scalability and cloud deployment.

## Features
- **Admin Dashboard:** View statistics, recent activities, and manage fees.
- **Student Management:** Add, edit, delete, and filter students.
- **Fee Management:** Create fee records, manage payments, and generate PDF receipts.
- **Audit Logging:** Tracks all admin actions.

## Tech Stack
- **Backend:** Flask (Python)
- **Database:** MongoDB (via MongoEngine)
- **Deployment:** Ready for Render (Gunicorn)

## Local Development

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set Environment Variables:**
    Create a `.env` file (optional for local, but recommended):
    ```
    SECRET_KEY=your_secret_key
    MONGO_URI=mongodb://localhost:27017/school_fee_db
    ```

3.  **Run the Application:**
    ```bash
    python run.py
    ```
    Access at `http://localhost:5051`.

## Deployment to Render

1.  **Create a New Web Service** on [Render](https://render.com/).
2.  **Connect your GitHub Repository.**
3.  **Settings:**
    -   **Runtime:** Python 3
    -   **Build Command:** `pip install -r requirements.txt`
    -   **Start Command:** `gunicorn run:app`
4.  **Environment Variables:**
    -   `MONGO_URI`: Your MongoDB Atlas connection string.
    -   `SECRET_KEY`: A secure random string.

## Database Migration Note
This project was migrated from SQLite to MongoDB. Previous SQLite data is **not** automatically migrated. You will start with a fresh database.
