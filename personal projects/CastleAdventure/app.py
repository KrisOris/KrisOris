from flask import Flask, render_template, redirect, request, url_for
from database import get_db


app = Flask (__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"



@app.route("/")
def main():
    return render_template("main.html")

@app.route("/castle_adventure")
def castle_adventure():
    return render_template("castle_adventure.html")

@app.route("/instructions")
def instructions():
    return render_template("instructions.html")


@app.route("/submit_score", methods=["POST"])
def submit_score():
    name = request.form.get("name")
    hp = request.form.get("hp")
    time_seconds = request.form.get("time_seconds")
    db = get_db()
    db.execute("""INSERT INTO results (name, hp, time_seconds) 
                    VALUES (?, ?, ?)""", 
                    (name, hp, time_seconds))
    db.commit()
    return redirect(url_for("leaderboard", sort="hp"))

@app.route("/leaderboard")
def leaderboard():
    sort = request.args.get("sort", "hp")
    db = get_db()
    if sort == "time":
        results = db.execute(
            """SELECT * 
                FROM results
                ORDER BY time_seconds ASC, hp DESC"""
        ).fetchall()
        sort_mode = "time"
    else:
        results = db.execute(
            """SELECT * 
                FROM results
                ORDER BY hp DESC, time_seconds ASC"""
        ).fetchall()
        sort_mode = "hp"
    return render_template(
        "leaderboard.html", results=results, sort_mode=sort_mode
    )