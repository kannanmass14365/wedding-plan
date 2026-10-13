import os
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("DB_PASSWORD"),
        database="weddingconnect"
    )

@app.route("/")
def home():
    return render_template("frontbage.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if len(password) < 8:
            message = "Password must be at least 8 characters."
        else:
            db = None
            cursor = None

            try:
                db = get_db_connection()
                cursor = db.cursor()

                password_hash = generate_password_hash(password)

                cursor.execute(
                    "INSERT INTO users (username, password_hash) "
                    "VALUES (%s, %s)",
                    (username, password_hash)
                )
                db.commit()
                message = "Registration successful!"

            except mysql.connector.IntegrityError:
                message = "Username already exists. Choose another."

            except mysql.connector.Error as e:
                print("DATABASE ERROR:", e)
                message = "Database error. Check VS Code terminal."

            finally:
                if cursor:
                    cursor.close()
                if db and db.is_connected():
                    db.close()

    return render_template("register.html", message=message)

@app.route("/users")
def show_users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("users.html", users=users)

@app.route("/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        username = request.form["username"].strip()

        try:
            cursor.execute(
                "UPDATE users SET username = %s WHERE id = %s",
                (username, user_id)
            )
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for("show_users"))

        except mysql.connector.Error as e:
            db.rollback()
            print("DATABASE ERROR:", e)

    cursor.execute(
        "SELECT id, username FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    cursor.close()
    db.close()

    if user is None:
        return "User not found", 404

    return render_template("edit_user.html", user=user)

@app.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id = %s",
        (user_id,)
    )
    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("show_users"))

    
if __name__ == "__main__":            
    app.run(debug=True)
    