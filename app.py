from flask import Flask, render_template, request, redirect, session, url_for, flash
import pandas as pd
import os

app = Flask(__name__)# Create a Flask application
app.secret_key = "your_secret_key" 

# CSV file paths
USER_DB = "dataset/users.csv"
OUTFITS_CSV = "dataset/fits_updated.csv"


def load_users():
    """Load user data from CSV into a dictionary"""
    try:
        if not os.path.exists(USER_DB):
            print("Error: User database not found.")
            return {}

        df = pd.read_csv(USER_DB).fillna("")  # Fill missing values with empty strings
        
        # Ensure username and password columns exist
        if "username" not in df.columns or "password" not in df.columns:
            print("Error: 'username' or 'password' column missing in users.csv")
            return {}

        return {row["username"].strip().lower(): row["password"].strip() for _, row in df.iterrows()}
    
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def get_recommendations(height, weight, gender, body_shape, theme):
    """Fetch outfit recommendations based on user input"""
    try:
        if not os.path.exists(OUTFITS_CSV):
            print("Error: Outfit database not found.")
            return []

        df = pd.read_csv(OUTFITS_CSV).fillna("")  # Fill missing values with empty strings

        # Check if required columns exist
        required_columns = {"Outfit", "Gender", "Body Shape", "Theme", "Height Min", "Height Max", "Weight Min", "Weight Max", "Image URL", "Description"}
        if not required_columns.issubset(set(df.columns)):
            print(f"Error: CSV is missing one or more required columns: {required_columns}")
            return []

        # Clean column names (strip spaces)
        df.columns = df.columns.str.strip()

        # Convert height and weight to numeric values safely
        try:
            height = float(height)
            weight = float(weight)
        except ValueError:
            print("Error: Invalid height or weight input.")
            return []

        # Apply filtering conditions
        filtered_df = df[
            (df["Gender"].str.lower() == gender.lower()) &
            (df["Body Shape"].str.lower() == body_shape.lower()) &
            (df["Theme"].str.lower() == theme.lower()) &
            (df["Height Min"].astype(float) <= height) &
            (df["Height Max"].astype(float) >= height) &
            (df["Weight Min"].astype(float) <= weight) &
            (df["Weight Max"].astype(float) >= weight)
        ]

        if filtered_df.empty:
            return []

        return filtered_df.to_dict(orient="records")
    
    except Exception as e:
        print(f"Error loading outfit recommendations: {e}")
        return []

@app.route("/")
def home():
    return redirect(url_for("signin"))

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()

        users = load_users()

        if username in users and users[username] == password:
            session["user"] = username
            flash("Login successful! Welcome back.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for("signin"))

    return render_template("sign-in.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    if "user" not in session:
        flash("Please sign in first.", "warning")
        return redirect(url_for("signin"))

    themes = ["Wedding", "Party", "Festival", "Casual", "Formal", "Beach", "Winter"]

    if request.method == "POST":
        height = request.form.get("height", "").strip()
        weight = request.form.get("weight", "").strip()
        gender = request.form.get("gender", "").strip()
        body_shape = request.form.get("body_shape", "").strip()
        theme = request.form.get("theme", "").strip()

        if not height or not weight or not gender or not body_shape or not theme:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("index"))

        session["outfit_preferences"] = {
            "height": height,
            "weight": weight,
            "gender": gender,
            "body_shape": body_shape,
            "theme": theme
        }

        return redirect(url_for("recommendation"))

    return render_template("index.html", themes=themes)

@app.route("/recommendation")
def recommendation():
    if "user" not in session:
        flash("Please sign in first.", "warning")
        return redirect(url_for("signin"))

    if "outfit_preferences" not in session:
        flash("Please enter your outfit preferences first.", "error")
        return redirect(url_for("index"))

    preferences = session["outfit_preferences"]
    recommended_outfits = get_recommendations(
        preferences["height"],
        preferences["weight"],
        preferences["gender"],
        preferences["body_shape"],
        preferences["theme"]
    )

    return render_template("recommendation.html", outfits=recommended_outfits)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("signin"))

if __name__ == "__main__":
    app.run(debug=True)
