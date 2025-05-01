from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import re
# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'a_random_key'
# MongoDB Client Initialization
client = MongoClient('localhost', 27017)  # Adjust the host and port if necessary
db = client["questionnares_db"]  # Database name
students_collection = db["students"]
users_collection = db["users"]
answered_questionnaires=db["answered_questionnaires"]
questionnaires=db["questionnaires"]

@app.route('/')
def home():
    if 'username' in session:
        username = session['username']
        return render_template('home.html', username=username)
    
    # Redirect to login if not logged in
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        query={"username":username,"password":password}
        user = users_collection.find_one(query)
        student=students_collection.find_one(query)
        
        if username == 'admin' and password == 'admin123':
            session['username'] = username
            return redirect(url_for('admin'))
        else:
            error = 'Invalid Credentials'
        if user:
            return render_template('home.html',error=error)
        elif student:
            return render_template('student.html',error=error)
    return render_template('login.html', error=error)

@app.route('/logout',methods=['GET','POST'])
def logout():
    # Remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))

#not fixed keep for later
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        name=request.form['name']
        surname=request.form['surname']
        if name and surname and username and password:
            user = {'username':username,'password':password ,'name': name, 'surname': surname}
            users_collection.insert_one(user)
            flash('User registered successfully!')
            return redirect(url_for('login'))
            
        else:
            flash('All fields are required!', 'danger')
    return render_template('register.html')
@app.route('/admin',methods=['GET','POST'])
def admin():
    if 'username' in session:
        username = session['username']
        return render_template('admin.html', username=username)
    
    # Redirect to login if not logged in
    return redirect(url_for('login'))
@app.route('/admin/addstudent',methods=['GET','POST'])
def addstudent():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        name=request.form['name']
        surname=request.form['surname']
        reg_number=request.form['reg_number']
        dept=request.form['dept']
        reg_number=int(reg_number)
        if name and surname and username and password and reg_number and dept:
            student = {'username':username,'password':password ,'name': name, 'surname': surname,"reg_number":reg_number,"department":dept}
            students_collection.insert_one(student)
            flash('student added successfully!')
            return redirect(url_for('admin'))
        
        else:
            flash('All fields are required!', 'danger')
    return render_template('addstudent.html')
@app.route('/admin/deletestudent',methods=['GET','POST'])
def deletestudent():
    check=False
    student=None
    success = request.args.get('success')
    if request.method=='POST':
        reg_number = request.form['reg_number']
        print(type(reg_number))
        if re.search(r'[a-zA-Z]', reg_number):
            jsoned={'reg_number':reg_number}
        else:
            jsoned={'reg_number':int(reg_number)}

        if 'findstudent' in request.form: 
            student = students_collection.find_one(jsoned)
            check = True
            return render_template('deletestudent.html', check=check, student=student)

        elif 'delete' in request.form:
            students_collection.delete_one(jsoned)
            return redirect(url_for('deletestudent', success=True))
    return render_template('deletestudent.html', check=check, student=student, success=success)



# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000)