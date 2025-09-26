from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_connection


app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------
# AUTH ROUTES
# -----------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        # Plain password check
        if user and user["password_hash"] == password:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            return render_template("register.html", error="Username already exists")

        # Store plain text password
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, password, role),
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return render_template("logout.html")


# -----------------------
# ADMIN DASHBOARD
# -----------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session)


# -----------------------
# FLIGHTS
# -----------------------

@app.route("/")
def home():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT f.id, f.flight_no, a1.code AS origin, a2.code AS destination,
                   f.departure_time, f.arrival_time, f.price
                   FROM flights f
                   JOIN airports a1 ON f.origin_airport_id=a1.id
                   JOIN airports a2 ON f.destination_airport_id=a2.id
                   ORDER BY f.departure_time ASC""")
    flights = cur.fetchall()
    cur.execute("SELECT * FROM airports")
    airports = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", flights=flights, airports=airports)


@app.route("/flights")
def flights():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT f.id, f.flight_no, a1.code AS origin, a2.code AS destination,
                   f.departure_time, f.arrival_time, f.price
                   FROM flights f
                   JOIN airports a1 ON f.origin_airport_id=a1.id
                   JOIN airports a2 ON f.destination_airport_id=a2.id""")
    flights = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("flights.html", flights=flights)
# -----------------------
# ADD FLIGHT
# -----------------------

@app.route("/flights/add", methods=["GET", "POST"])
def add_flight():
    if "user_id" not in session:   # optional: only logged-in users can add
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch airports for dropdowns
    cur.execute("SELECT * FROM airports")
    airports = cur.fetchall()

    if request.method == "POST":
        flight_no = request.form["flight_no"]
        origin_airport_id = request.form["origin_airport_id"]
        destination_airport_id = request.form["destination_airport_id"]
        departure_time = request.form["departure_time"]
        arrival_time = request.form["arrival_time"]
        capacity = request.form["capacity"]
        price = request.form["price"]

        cur.execute(
            """INSERT INTO flights 
               (flight_no, origin_airport_id, destination_airport_id, departure_time, arrival_time, capacity, price) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (flight_no, origin_airport_id, destination_airport_id, departure_time, arrival_time, capacity, price)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Flight added successfully!")
        return redirect(url_for("flights"))

    cur.close()
    conn.close()
    return render_template("add_flight.html", airports=airports)



@app.route("/flights/<int:flight_id>")
def flight_detail(flight_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""SELECT f.*, a1.code AS origin_code, a2.code AS dest_code
                   FROM flights f
                   JOIN airports a1 ON f.origin_airport_id=a1.id
                   JOIN airports a2 ON f.destination_airport_id=a2.id
                   WHERE f.id=%s""", (flight_id,))
    flight = cur.fetchone()

    cur.execute("""SELECT b.*, p.first_name, p.last_name, p.email
                   FROM bookings b
                   JOIN passengers p ON b.passenger_id=p.id
                   WHERE b.flight_id=%s""", (flight_id,))
    bookings = cur.fetchall()

    seats_left = flight["capacity"] - len([b for b in bookings if b["status"] == "CONFIRMED"])

    cur.close()
    conn.close()
    return render_template("flight_detail.html", flight=flight, bookings=bookings, seats_left=seats_left)


# -----------------------
# BOOKINGS
# -----------------------

@app.route("/book", methods=["POST"])
def book():
    flight_id = request.form["flight_id"]
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    seat_no = request.form.get("seat_no")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("INSERT INTO passengers (first_name, last_name, email, phone) VALUES (%s,%s,%s,%s)",
                (first_name, last_name, email, phone))
    passenger_id = cur.lastrowid

    cur.execute("INSERT INTO bookings (flight_id, passenger_id, seat_no) VALUES (%s,%s,%s)",
                (flight_id, passenger_id, seat_no))
    booking_id = cur.lastrowid
    conn.commit()

    cur.execute("""SELECT b.id, b.seat_no, f.flight_no, f.departure_time, f.arrival_time,
                   a1.code AS origin_code, a2.code AS dest_code
                   FROM bookings b
                   JOIN flights f ON b.flight_id=f.id
                   JOIN airports a1 ON f.origin_airport_id=a1.id
                   JOIN airports a2 ON f.destination_airport_id=a2.id
                   WHERE b.id=%s""", (booking_id,))
    booking = cur.fetchone()

    passenger = {"first_name": first_name, "last_name": last_name}

    cur.close()
    conn.close()
    return render_template("booking_success.html", booking=booking, passenger=passenger)


@app.route("/bookings")
def bookings():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT b.*, p.first_name, p.last_name, f.flight_no,
                   a1.code AS origin_code, a2.code AS dest_code
                   FROM bookings b
                   JOIN passengers p ON b.passenger_id=p.id
                   JOIN flights f ON b.flight_id=f.id
                   JOIN airports a1 ON f.origin_airport_id=a1.id
                   JOIN airports a2 ON f.destination_airport_id=a2.id""")
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("bookings.html", bookings=bookings)


@app.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE bookings SET status='CANCELLED' WHERE id=%s", (booking_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("bookings"))


# -----------------------
# PASSENGERS
# -----------------------

@app.route("/passengers")
def passengers():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM passengers")
    passengers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("passengers.html", passengers=passengers)


# -----------------------
# AIRPORTS
# -----------------------

@app.route("/airports", methods=["GET", "POST"])
def airports():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        code = request.form["code"]
        name = request.form["name"]
        city = request.form["city"]
        country = request.form["country"]
        cur.execute("INSERT INTO airports (code, name, city, country) VALUES (%s,%s,%s,%s)",
                    (code, name, city, country))
        conn.commit()

    cur.execute("SELECT * FROM airports")
    airports = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("airports.html", airports=airports)


if __name__ == "__main__":
    app.run(debug=True)
