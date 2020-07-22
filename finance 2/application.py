import os
import sqlite3
import datetime
import math


from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():

    # get username and cash from user id from users table
    user = db.execute("SELECT * FROM users WHERE id = :session",
                        session=session["user_id"])
    username = user[0]["username"]
    cash = user[0]["cash"]
    cash = round(cash, 2)

    gtotal = cash
    # searches holding table
    holding = db.execute("SELECT * FROM holdings WHERE username = :username", username=user[0]["username"])
    # opens and writes an html table with extracted info
    f_html = open("templates/index.html", 'w')
    f_html.write('{% extends "layout.html" %}\n\n{% block title %}\nIndex\n{% endblock %}\n{% block main %}\n')
    f_html.write("<style>table, th, td {border: 1px solid black;padding: 10px;}tr:hover {background-color:#f5f5f5;}</style>")
    f_html.write("<table><tr><th>Company</th><th>Symbol</th><th>Quantity</th><th>Current Price</th><th>Value</th></tr>")
    # loops over each row in transactions extrating data and inserting into html table
    for y in range(len(holding)):
        if (holding[y]['holding'] > 0):
            quote = (lookup(holding[y]["stock"]))
            price = quote['price']
            q_inp = (holding[y]['holding'])
            value = price * (holding[y]['holding'])
            gtotal = gtotal + value

            f_html.write("<tr><th>" + holding[y]["company"] + "</th><th>" + holding[y]["stock"] + "</th><th>" + str(holding[y]['holding'])+"</th><th>"
                        + str(usd(price))+"</th><th>" + str(usd(value)) + "</th></tr>")

    f_html.write("<tr><th></th><th></th><th></th><th>Total Cash</th><th>"+str(usd(cash))+"</th></tr>")
    f_html.write("<tr><th></th><th></th><th></th><th>Grand Total</th><th>"+str(usd(gtotal))+"</th></tr>")

    f_html.write("</table>")
    f_html.write('\n{% endblock %}')
    f_html.close
    f_html = open('templates/index.html', 'r')

    return render_template("index.html")

    # return render_template("quoted.html", name = trasnactions,symbol = quote["symbol"], price = quote["price"] )

    return apology("homepage")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        """Buy shares of stock"""
        if not request.form.get("symbol"):
            return apology("Please provide a stock quote")
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Stock symbol not recognised")
        if not request.form.get("shares"):
            return apology("Please provide a quanity")
        quantity = request.form.get("shares")
        if(quantity.isnumeric() == False):
            return apology("Please provide a valid number")
        quantity = float(quantity)
        mod = quantity % 1
        if mod > 0:
            return apology("Please provide a valid number")
        if quantity < 1:
            return apology("Please provide positive number")

        # get username from user id from database
        user = db.execute("SELECT * FROM users WHERE id = :session",
                          session=session["user_id"])

        username = user[0]["username"]
        stock = quote['symbol']
        buysell = "BUY"
        price = quote['price']
        company = quote['name']
        now = datetime.datetime.now()
        cash = user[0]["cash"]
        quantity = int(quantity)
        value = price * quantity

        if cash < (price * quantity):
            return apology("Insufficient cash")
        else:
            # creates entry to trsanaction database
            transac = db.execute("INSERT INTO transactions(username,stock,quantity,buysell,price,date,company,time,value)VALUES(:username,:stock,:quantity,:buysell,:price,:date,:company,:time,:value)",username = user[0]["username"],
            stock = quote['symbol'],quantity = quantity, buysell = "BUY",price = quote['price'],date = (now.strftime("%Y-%m-%d")),company = quote['name'],time = (now.strftime("%H:%M:%S")),value = value)
            holding = db.execute("SELECT * FROM holdings WHERE stock = :stock AND username = :username",stock = quote['symbol'],username = user[0]["username"] )
            print("hello",holding)
            if not holding:
                db.execute("INSERT INTO holdings(username,stock,company,holding)VALUES(:username,:stock,:company,:holding)",
                username = user[0]["username"],stock = quote['symbol'],company = quote['name'],holding = quantity)
            else:
                db.execute("UPDATE holdings SET holding = :holding WHERE stock = :stock AND username =:username", holding = (holding[0]["holding"] + quantity), username=username, stock = stock)


            cash = cash-value
            db.execute("UPDATE users SET cash = :cash WHERE username = :username", cash=cash, username=user[0]["username"])
            return redirect("/")
    return render_template("buy.html")

    # change to username
    # sort out true
    # change to check


@app.route("/check", methods=["GET"])
def check():
    print("test")
    userlist=[]
    USERS = db.execute("SELECT username FROM users")
    for h in range(len(USERS)):
        userlist.append(USERS[h]['username'])

    username = request.args.get("username","")
    if len(username) > 0:
        if username in userlist:
            return jsonify(False)
        else:
            return jsonify(True)



@app.route("/history")
@login_required
def history():
    # gets username from session id
    user = db.execute("SELECT * FROM users WHERE id =:session", session=session["user_id"])
    username = user[0]["username"]
    transactions = db.execute("SELECT * FROM transactions WHERE username =:username", username=username)

    history = open("templates/history.html", 'w')
    history.write('{% extends "layout.html" %}\n\n{% block title %}\nIndex\n{% endblock %}\n{% block main %}\n')
    history.write("<style>table, th, td {border: 1px solid black;padding: 10px;}tr:hover {background-color:#f5f5f5;}</style>")
    history.write("<table><tr><th>Company</th><th>Symbol</th><th>Buy or Sell</th><th>Price</th><th>Quantity</th><th>Date</th><th>Time</th></tr>")

    for h in range(len(transactions)):
        history.write("<tr><th>"+transactions[h]["company"]+"</th><th>"+transactions[h]["stock"]+"</th><th>"+transactions[h]["buysell"]
        +"</th><th>"+str(transactions[h]["price"])+"</th><th>"+str(transactions[h]["quantity"])+"</th><th>"+transactions[h]["date"]+"</th><th>"+transactions[h]["time"]+"</th></tr>")

    history.write("</table>")
    history.write('\n{% endblock %}')
    history.close
    history = open("templates/history.html", 'r')

    return render_template("history.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        print(check_password_hash(
            "pbkdf2:sha256:150000$ntTqNOZQ$cd036fc1c7b4548038285f92637f96202e423bcd1c943de5d9f79d22d8067a8b", request.form.get("password")))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Unable to log you in", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Please input a stock symbol")
        stock = request.form.get("symbol")
        quote = lookup(stock)
        if not quote:
            return apology("Stock symbol not recognised")
        print("QUOTE", quote)
        stock_name = quote['name']
        print(stock_name)
        return render_template("quoted.html", name=quote['name'], symbol=quote["symbol"], price=usd(quote["price"]))
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if username == "":
            return apology("Please enter a username")
        if password == "":
            return apology("Please enter a password")
        if confirmation == "":
            return apology("Please confirm your password")
        if password != confirmation:
            return apology("Please ensure passwords match")

        password_hash = generate_password_hash("password")

        password_hash = generate_password_hash(request.form.get("password"))

        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if rows:
            return apology("username already in use", 400)

        inserted = db.execute("INSERT INTO users(username,hash)VALUES(:username, :hash)",
        username=request.form.get("username"), hash=password_hash,)
        session["user_id"] = inserted

        return redirect("/")

    else:
        return render_template("register.html")

    return render_template("/register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    # get username and cash from user id from users table
    user = db.execute("SELECT * FROM users WHERE id = :session",
                    session=session["user_id"])
    username = user[0]["username"]
    cash = user[0]["cash"]
    # gets current holdings for username from holdings table
    stocks = db.execute("SELECT stock,holding FROM holdings WHERE username =:username", username=user[0]["username"])
    print(stocks)
    print(len(stocks))

    # opens and writes an html file with select menu containing stocks info
    f_html = open("templates/sell.html", 'w')
    f_html.write('{% extends "layout.html" %}{% block title %}Sell{% endblock %}{% block main %}<form action="/sell" method="post"><div class="form-group"><select class="form-control" name="symbol"><option disabled selected>Select stock to sell...</option>')
    for s in range(len(stocks)):
        x = stocks[s]['stock']
        f_html.write("<option>"+ x +"</option>")
    f_html.write('</select></div><div class="form-group"><input class="form-control" name="shares" placeholder="Quantity" type="number" min="1"></div><button class="btn btn-primary" type="submit">Sell</button></form>{% endblock %}')
    f_html.close
    f_html = open("templates/sell.html", "r")
    # gets dats from  sell form
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        print(symbol)
        print(shares)
        shares = int(shares)
        if symbol == None:
            return apology("Please select a share to sell")
        if shares == "":
            return apology("Please enter a quantity")
        if shares < 0:
            return apology("please enter a positive number")
        quote = lookup(symbol)
        now = datetime.datetime.now()
        # goes through holdings query and gets number of shares in holdings
        for s in range(len(stocks)):
            if stocks[s]['stock'] == symbol:
                port = stocks[s]['holding']

        # port is number of shares in portfolio
        port = int(port)
        price = quote['price']
        date = (now.strftime("%Y-%m-%d"))
        if (shares > port) :
            return apology("Not enough shares in your portfolio")
        else:
            revenue = price * shares
            transac = db.execute("INSERT INTO transactions(username,stock,quantity,buysell,price,date,company,time,value)VALUES(:username,:stock,:quantity,:buysell,:price,:date,:company,:time,:revenue)",username = user[0]["username"],
            stock = quote['symbol'],quantity = shares, buysell = "SELL",price = quote['price'],date = (now.strftime("%Y-%m-%d")),company = quote['name'],time = (now.strftime("%H:%M:%S")),revenue = revenue)
            cash = cash + revenue
            db.execute("UPDATE users SET cash =:cash WHERE username =:username",cash = cash , username = username)
            db.execute("UPDATE holdings SET holding = :holding WHERE username =:username AND stock =:stock", holding = port - shares, username = username, stock = quote['symbol'])
            return redirect("/")
    return render_template("/sell.html")

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """settings"""
    if request.method == "POST":
        deposit = request.form.get("deposit")
        if deposit == '':
            return apology("Please enter a quantity")
        deposit = int(deposit)
        if deposit < 0:
            return apology("please enter a positive number")
        # get username and cash from user id from users table
        user = db.execute("SELECT * FROM users WHERE id = :session",
                        session = session["user_id"])
        username = user[0]["username"]
        cash = user[0]["cash"]
        newtotal = cash + deposit
        print(newtotal)
        db.execute("UPDATE users SET cash =:cash WHERE username =:username",cash = newtotal , username = username)


    return render_template("/settings.html")




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
