from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import re,ast
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
sortcollection=db["sortcollection"]
@app.route('/')
def home():
    if 'username' in session:
        username = session['username']
        return render_template('admin.html', username=username)
    elif 'user' in session:
        username=session['user']
        return render_template('home.html', username=username)
    elif 'student' in session:
        username=session['student']
        return render_template('student.html', username=username)
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
            session['user']=username
            return render_template('home.html',error=error)
        elif student:
            session['student']=username
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
                students_collection.find_one_and_update(jsoned,{'$set':{'password':newpass}})
                flash('Password updated successfully!', 'info')
                return redirect(url_for('home'))
    return render_template('changepassword.html',student=student)

@app.route('/myquestionnaires',methods=['GET','POST'])
def myquestionnaires():
    if 'student' in session:
        username=session['student']
        stud=students_collection.find_one({'username':username})
        myq=list(questionnaires.find({'student_id':int(stud.get('reg_number'))}))
        return render_template('myquestionnaires.html',myq=myq)
    return render_template('myquestionnaires.html')

@app.route('/changeqname',methods=['GET','POST'])
def changeqname():
    username=session['student']
    stud=students_collection.find_one({'username':username})
    rnumber=stud.get('reg_number')
    if request.method=='POST':
        qid=request.form['questionnaire_id']
        if 'findq' in request.form:
            qforchange=questionnaires.find_one({'questionnaire_id':int(qid),'student_id':int(rnumber)})
            return render_template('changeqname.html',qforchange=qforchange)
        if 'setnewname' in request.form:
            newname=request.form['newname']
            questionnaires.find_one_and_update({'questionnaire_id':int(qid),'student_id':int(rnumber)},{'$set':{'title':newname}})
            flash('Questionnaire title updated successfully!', 'info')
            return redirect(url_for('home'))
    return render_template('changeqname.html')


@app.route('/createq',methods=['GET','POST'])
def createq():
    check=False
    #auto increment
    lastq=list(questionnaires.find({}).sort({'questionnaire_id':-1}).limit(1)) 
    nextid=(lastq[0]['questionnaire_id'])+1
    if 'student' in session:
        username=session['student']
        stud=students_collection.find_one({'username':username})
        reg=stud.get('reg_number')
        if request.method=='POST':
            if 'addquestions' in request.form:
                title=request.form['title']
                desc=request.form['desc']
                nofqs=int(request.form['nofqs'])
                check=True
                return render_template('createq.html',title=title,desc=desc,nofqs=nofqs,check=check)
            if 'create' in request.form:
                title=request.form['title']
                desc=request.form['desc']
                nofqs=int(request.form['nofqs'])
                questions=[]
                for i in range(nofqs):
                    questiondesc=request.form[f'question{i}']
                    typeofq=request.form['type']
                    finalized={'type':typeofq,'description':questiondesc,'question_num':i+1}
                    questions.append(finalized)
                jsoned={'student_id':reg,'questionnaire_id':nextid,'title':title,'description':desc,'unique_url':f'localhost:5000/questionnaire/{nextid}','questions':questions,'answer_count':0}
                questionnaires.insert_one(jsoned)
                return render_template('home.html')
    return render_template('createq.html')

@app.route('/deleteq',methods=['GET','POST'])
def deleteq():
    check=False
    if 'student' in session:
        username=session['student']
        stud=students_collection.find_one({'username':username})
        reg=int(stud.get('reg_number'))
        print(reg)
        if request.method=='POST':
            if 'findq' in request.form:
                qid=int(request.form['qid'])
                qfordel=questionnaires.find_one({'student_id':reg,'questionnaire_id':qid})
                if qfordel:
                    check=True
                print(qfordel,check)
                return render_template('deleteq.html',check=check,questionnaire=qfordel)
            if 'delete' in request.form:
                qid=int(request.form['questionnaire_id'])
                questionnaires.find_one_and_delete({'student_id':reg,'questionnaire_id':qid})
                flash('questionnaire deleted succesfully!')
                return redirect(url_for('home'))
    return render_template('deleteq.html')

#admin exclusive
@app.route('/admin',methods=['GET','POST'])
def admin():
    if 'username' in session:
        username = session['username']
        return render_template('admin.html', username=username)
    
    # Redirect to login if not logged in
    return redirect(url_for('login'))

@app.route('/admin/addstudent',methods=['GET','POST'])
def addstudent():
    if 'username' in session:
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
    else:
        return redirect(url_for('login'))
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
                return render_template('showquestionnaires.html',questionnaire=questionnaire,check=check,length=len(questionnaire))
            
            elif questionnaires.find_one({'title':uservalue}):
                search_by_title=list(questionnaires.find({'title':uservalue}))
                return render_template('showquestionnaires.html',questionnaire=search_by_title,check=check,length=len(search_by_title))
            
            elif students_collection.find_one({'department':uservalue}):
                search_by_dept=list(students_collection.find({'department':uservalue}))
                studentids=[student['reg_number'] for student in search_by_dept]
                print(studentids)                  
                questionnaire=list(questionnaires.find({'student_id': {'$in':studentids}}))
                return render_template('showquestionnaires.html',questionnaire=questionnaire,check=check,length=len(questionnaire))
        
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
                return render_template('showquestionnaires.html',questionnaire=rangeofq,check=check,length=len(rangeofq))
        
        if 'sortaftersearch' in request.form:
            length=int(request.form['lengthofresults'])
            
            for i in range(length): 
                qid=request.form.getlist('qid')

            tmp=list(map(int,qid))
            itemstosort=[]
            for i in range(len(tmp)):
                itemstosort.append(questionnaires.find_one({'questionnaire_id':tmp[i]}))
            #last one remaining pls fix
            itemstosort.sort(key=lambda x: x['answer_count'])
            return render_template('showquestionnaires.html',sorted=itemstosort,check=check)
        
    return render_template('showquestionnaires.html',q=q)
 
 #unique link for every questionnaire 
 #questionnaire list and answer functions
@app.route('/questionnaire/<num>',methods=['GET','POST'])
def questionnairelink(num):
    unique=questionnaires.find_one({"questionnaire_id": int(num)}) 
    return render_template('unique_q.html',unique=unique)

@app.route('/questionnaire/<num>/answer',methods=['GET','POST'])
def answerquestionnaire(num):
    fromstudent=False
    if 'student' in session:
        fromstudent=True
    questionnaire=questionnaires.find_one({'questionnaire_id':int(num)})
    questions=questionnaire['questions']
    if request.method=='POST':
        useranswers=[]
        if 'answers' in request.form:
            for i in range(1,len(questionnaire['questions'])+1):
                qn=questions[i-1]['question_num']
                print(qn)
                answer=request.form[f'question{i}']
                if re.fullmatch(r'^\d+$', answer):
                    jsoned={'question_num':qn,'content':int(answer)}
                else:
                    jsoned={'question_num':qn,'content':answer}
                useranswers.append(jsoned)
        send={'questionnaire_id':int(num),'from_student':fromstudent,'answers':useranswers}
        answered_questionnaires.insert_one(send)
        return render_template('home.html')
    return render_template('answerq.html',questionnaire=questionnaire,questions=questions)


# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000)