from flask import Flask, request, redirect, render_template, session, flash
import datetime
import re
import md5
from mysqlconnection import MySQLConnector
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = 'rangersleadtheway'
mysql = MySQLConnector(app,'thewall')

# HOME / INDEX *********************************************

@app.route('/')
def index():
    return render_template('index.html')

# WALL *********************************************

@app.route('/wall')
def wall():
    query = "SELECT users.first_name, users.last_name, message, messages.id, messages.created_at, comments.comment, comments.messages_id FROM messages JOIN users ON users.id = messages.users_id LEFT JOIN comments ON messages.id = comments.messages_id ORDER BY created_at DESC;"
    messages = mysql.query_db(query)
    query2 = "SELECT comments.users_id, users.id, users.first_name, users.last_name, comments.messages_id, comment, comments.created_at, messages.id FROM comments JOIN users ON users.id = comments.users_id LEFT JOIN messages ON messages.id = comments.messages_id ORDER BY comments.created_at DESC;"
    comments = mysql.query_db(query2)

    return render_template('wall.html', all_msg=messages, all_cmts=comments)

# REGISTRATION *********************************************

@app.route('/registration', methods=['POST'])
def registration():
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['regemail']
    hashed_password = md5.new(request.form['regpassword']).hexdigest()
    password2 = request.form['regpassword2']
    session['fname'] = fname
    session['lname'] = lname
    # Write query as a string.
    # we want to insert into our Db.
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:fname, :lname, :regemail, :hashed_password, NOW(), NOW());"
    # query data for email validation
    query_val = "SELECT email FROM users WHERE email = :regemail;"
    # query data for grabing id from new registrant
    query_id = "SELECT id FROM users WHERE email = :regemail;"
 
   # We'll then create a dictionary of data from the POST data received.
    data = {
            'fname': request.form['fname'],
            'lname':  request.form['lname'],
            'regemail': request.form['regemail'],
            'hashed_password': hashed_password
           }
    check = mysql.query_db(query_val, data)
    
    data_id = {
            'regemail': request.form['regemail'],
            }
    # Check name fields
    if len(fname) < 2 or len(lname) < 2:
        flash("Name must be longer.")
        return redirect('/')
    elif not str(fname).isalpha():
        flash("First Name can only be letters.")
        return redirect('/')       
    elif not str(lname).isalpha():
        flash("Last Name can only be letters.")
        return redirect('/')
    
    # Validates email address for proper format.
    if len(email) < 1:
        flash("Email cannot be blank!")
        return redirect('/')
    elif not EMAIL_REGEX.match(email):
        flash("Invalid Email Address!")
        return redirect('/')
    elif len(check) != 0:
        flash("Duplicate address, enter another one!")
        return redirect('/')
    
    # Check password length and confirmation
    if len(request.form['regpassword']) < 8:
        flash("Password is not long enough!")
        return redirect('/')
    elif request.form['regpassword'] != password2:
        flash("Passwords do not match!")
        return redirect('/')

    # Run query, with dictionary values injected into the query.
    mysql.query_db(query, data)
    get_id = mysql.query_db(query_id, data_id)
    session['logged_id'] = get_id[0]['id']
    return redirect('/wall')

# LOGIN*********************************************

@app.route('/login', methods=['POST'])
def login():
    query = "SELECT email FROM users WHERE email = :logemail;"
    query_pw = "SELECT password FROM users WHERE email = :logemail;"
    query_id = "SELECT id, first_name, last_name FROM users WHERE email = :logemail;"
    hashed_password = md5.new(request.form['logpassword']).hexdigest()
    # We'll then create a dictionary of data from the POST data received.
    data = {
             'logemail': request.form['logemail'],
             'logpassword': request.form['logpassword']
           }
    data_id = {
            'logemail': request.form['logemail'],
            }   
    # query for email validation
    check = mysql.query_db(query, data)
    # query for password validation
    check_pw = mysql.query_db(query_pw, data)

    # Validates email address for proper format.
    if len(request.form['logemail']) < 1:
        flash("Email cannot be blank!")
        return redirect('/')
    elif not EMAIL_REGEX.match(request.form['logemail']):
        flash("Invalid Email Address!")
        return redirect('/')
    elif len(check) == 0:
        flash("Email not found!")
        return redirect('/')

    #password validation
    # if hashed_password != check_pw[0]['password']:
    #     flash("Password does not match.")
    #     return redirect('/')

    get_id = mysql.query_db(query_id, data_id)
    session['logged_id'] = get_id[0]['id']
    session['fname'] = get_id[0]['first_name']
    session['lname'] = get_id[0]['last_name']
    return redirect('/wall')

# POST MESSAGE*********************************************

@app.route('/post_msg', methods=['POST'])
def post_msg():
    message = request.form['message']
    userid = session['logged_id']

    # Write query as a string.
    # we want to insert into our Db.
    query = "INSERT INTO messages (message, created_at, updated_at, users_id) VALUES (:message, NOW(), NOW(), :userid);"
 
   # We'll then create a dictionary of data from the POST data received.
    data = {
            'message': request.form['message'],
            'userid':  session['logged_id']
           }

    mysql.query_db(query, data)
    return redirect('/wall')

# POST COMMENTS *********************************************

@app.route('/post_cmt', methods=['POST'])
def post_cmt():
    comment = request.form['comment']
    userid = session['logged_id']
    message_id = request.form['message_id']
    # Write query as a string.
    # we want to insert into our Db.
    query = "INSERT INTO comments (comment, created_at, updated_at, messages_id, users_id) VALUES (:comment, NOW(), NOW(), :message_id, :userid);"
 
   # We'll then create a dictionary of data from the POST data received.
    data = {
            'comment': request.form['comment'],
            'message_id':  request.form['message_id'],
            'userid': session['logged_id']
           }
    mysql.query_db(query, data)
    return redirect('/wall')


app.run(debug=True)