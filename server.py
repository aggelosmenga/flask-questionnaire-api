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
@app.route('/changepassword',methods=['GET','POST'])
def changepassword():
    student=None
    if request.method=='POST':
        reg_number=request.form['reg_number']
        oldpass=request.form['oldpass']
        newpass=request.form['newpass']
        jsoned={'reg_number':int(reg_number),'password':oldpass}
        if 'changepass' in request.form:
            student=students_collection.find_one(jsoned)
            if student:
                updated=students_collection.find_one_and_update(jsoned,{'$set':{'password':newpass}})
                flash('Password updated successfully!', 'info')
                return redirect(url_for('home'))
    return render_template('changepassword.html',student=student)
#admin
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

#for all
@app.route('/showquestionnaires',methods=['GET','POST'])
def showquestionnaires():
    q=questionnaires.find({})
    check=False
    if request.method=='POST':
        if 'sortbyanswer' in request.form:
            sorted=questionnaires.find().sort("answer_count",1)
            return(render_template('showquestionnaires.html',q=sorted))
        if 'showall' in request.form :
            q=questionnaires.find({})
        if 'search' in request.form:
            uservalue=request.form['searchfield'].strip()
            check=True
            
            if students_collection.find_one({'name':uservalue}):
                search_by_name=list(students_collection.find({'name':uservalue}))
                studentids=[student['reg_number'] for student in search_by_name]
                questionnaire=list(questionnaires.find({'student_id':{'$in':studentids}}))
                return render_template('showquestionnaires.html',questionnaire=questionnaire,check=check)
            
            elif questionnaires.find_one({'title':uservalue}):
                search_by_title=list(questionnaires.find({'title':uservalue}))
                return render_template('showquestionnaires.html',questionnaire=search_by_title,check=check)
            
            elif students_collection.find_one({'department':uservalue}):
                search_by_dept=list(students_collection.find({'department':uservalue}))
                studentids=[student['reg_number'] for student in search_by_dept]
                print(studentids)                  
                questionnaire=list(questionnaires.find({'student_id': {'$in':studentids}}))
                return render_template('showquestionnaires.html',questionnaire=questionnaire,check=check)
        if 'bound' in request.form:
            lowerbound=request.form['lowerbound'].strip()
            upperbound=request.form['upperbound'].strip()
            if re.search(r'[a-zA-Z]', lowerbound) or re.search(r'[a-zA-Z]',upperbound) or lowerbound=='' or upperbound=='':
                return render_template('showquestionnaires.html',q=q)
            else:
                lowerbound=int(lowerbound)
                upperbound=int(upperbound)
                check=True
                if lowerbound>upperbound:
                    return render_template('showquestionnaires.html',q=q)
                rangeofq=list(questionnaires.find({'answer_count':{'$gte':lowerbound,'$lte':upperbound}}))
                print(rangeofq)
                return render_template('showquestionnaires.html',rangeofq=rangeofq,check=check)
            #fix sort
    return render_template('showquestionnaires.html',q=q)
 
 #unique link for every questionnaire
@app.route('/questionnaire/<num>')
def questionnairelink(num):
    print(num)
    unique=questionnaires.find_one({"questionnaire_id": int(num)}) 
    print(unique) 
    return render_template('unique_q.html',unique=unique)

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000)