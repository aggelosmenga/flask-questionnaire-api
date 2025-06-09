from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import re,os,json
# Flask App Initialization #αντιγραμμενο απο τα παραδειγματα
app = Flask(__name__)
app.secret_key = 'a_random_key'
# MongoDB Client Initialization

SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000)) #συνδεση με το container που χρησιμοποιειται για τη βαση δεδομενων
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'uniQ')
MOGNO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))

# MongoDB Client Initialization
client = MongoClient(MOGNO_HOST, MONGO_PORT)
db = client[MONGO_DATABASE]  # Database name
students_collection = db["students"]
users_collection = db["users"] #οριζουμε εδω ολα τα collections αν δεν υπαρχουν items μεσα τοτε δημιουργουνται μονο μετα την εισαγωγη αντικειμενων
answered_questionnaires=db["answered_questionnaires"]
questionnaires=db["questionnaires"]

@app.route('/')
def home(): #to home route ειναι πολυ απλο, απλα κανουμε το καταλληλο redirect αναλογα με το ποιος ειναι συνδεδεμενος
    if 'username' in session:
        username = session['username'] #σημαντικη σημειωση εδω ο admin εχει το session username, ξεχασα να το αλλαξω οσο εγραφα τον κωδικα
        return render_template('admin.html', username=username)
    elif 'user' in session:
        username=session['user'] #user για απλο user
        return render_template('home.html', username=username)
    elif 'student' in session:
        username=session['student'] #student για φοιτητες
        return render_template('student.html', username=username)
    # Redirect to login if not logged in
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login(): #το Log in ειναι σχετικα απλο, παιρνουμε τα values apo ta post forms των flask templates και ψαχνουμε μεσα στη βαση δεδομενων 
    error = None #για να δουμε αν αυτα τα credentials υπαρχουν στο user collection or student collection
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        query={"username":username,"password":password}
        user = users_collection.find_one(query)
        student=students_collection.find_one(query)
        
        if username == 'admin' and password == 'admin123': #στη περιπτωση που ειναι admin δε ψαχνουμε καμια βαση, ελεγχουμε μονα τους τα στοιχεια και οριζουμε εδω το session
            session['username'] = username
            return redirect(url_for('admin'))
        else:
            error = 'Invalid Credentials' 
        if user:
            session['user']=username
            return render_template('home.html',error=error)
        elif student: #μετα την επιτυχη συνδεση στελνεται ο user Η ο student στα αντιστοιχα pages
            session['student']=username
            return render_template('student.html',error=error) #σημειωση εδω:καλυτερα redirect sto template παρα render το template αλλα δεν αλλαζει κατι στο συστημα απλα ειναι πιο Optimized
    return render_template('login.html', error=error)

@app.route('/logout',methods=['GET','POST'])
def logout():
    # Remove the username from the session if it's there
    session.pop('username', None) #logout
    session.pop('user', None)
    session.pop('student', None)
    return redirect(url_for('login'))

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST': #στην εγγραφη χρηστη παιρνουμε τα στοιχεια απο το html template Και τα εισαγουμε στo users  collections
        username=request.form['username']
        password=request.form['password'] #θα ηταν καλυτερα επισης εδω να ελεγχαμε για μοναδικοτητα username 
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
    student=None #αλλαγη κωδικου
    if request.method=='POST': 
        reg_number=request.form['reg_number']
        oldpass=request.form['oldpass']
        newpass=request.form['newpass']
        jsoned={'reg_number':int(reg_number),'password':oldpass}#παιρνουμε τα στοιχεια του φοιτητη και ελεγχουμε αν ειναι σωστα με βαση τον ΑΜ του και τον παλιο κωδικο
        if 'changepass' in request.form:
            student=students_collection.find_one(jsoned)
            if student:
                students_collection.find_one_and_update(jsoned,{'$set':{'password':newpass}}) #επειτα αλλαζουμε τον κωδικο στη βαση δεδομενων
                flash('Password updated successfully!', 'info') 
                return redirect(url_for('home'))
    return render_template('changepassword.html',student=student)

@app.route('/myquestionnaires',methods=['GET','POST'])
def myquestionnaires(): #τα ερωτηματολογια μου, δειχνει ολα τα ερωτηματολογια ενος φοιτητη με βαση τον αριθμο μητρωου του
    if 'student' in session:
        username=session['student']
        stud=students_collection.find_one({'username':username})
        myq=list(questionnaires.find({'student_id':int(stud.get('reg_number'))}))
        return render_template('myquestionnaires.html',myq=myq)
    elif 'username' in session:
        myq=list(questionnaires.find({'student_id':'admin'}))
        return render_template('myquestionnaires.html',myq=myq)
    return render_template('myquestionnaires.html')

@app.route('/qstats',methods=['GET','POST']) #στατιστικα ερωτηματολογιου
def qstats():
    if 'student' in session:
        username=session['student']
        stud=students_collection.find_one({'username':username}) 
        rnumber=stud.get('reg_number') #παιρνουμε πρωτα τα στοιχεια του φοιτητη, για να κανουμε την αντιστοιχιση με τα ερωτηματολογια
        if request.method=='POST':
            qid=int(request.form['questionnaire_id'])
            if questionnaires.find_one({'questionnaire_id':qid}):
                return redirect(url_for('answers', studentid=rnumber, qid=qid)) #ελεγχουμε αν ο φοιτητης εχει ερωτηματολογιο με το id που εδωσε
            else:
                return "Questionnaire not found!", 404
    return render_template('qstats.html')
                    
        
@app.route('/qstats/studentid_<studentid>/q_id_<qid>',methods=['GET','POST'])
def answers(studentid,qid):
    totalans=list(answered_questionnaires.find({'questionnaire_id':int(qid)})) #μετα αφου βρουμε αν το ερωτηματολογιο αντιστοιχει στον φοιτητη 
    ansbystudents=list(answered_questionnaires.find({'from_student':True,'questionnaire_id':int(qid)})) #εμφανιζουμε ολα τα στοιχεια και τα στατιστικα που ζητησε η εκφωνηση της εργασιας
    ansbyusers=list(answered_questionnaires.find({'from_student':False,'questionnaire_id':int(qid)}))
    studpercentage=round((len(ansbystudents)/len(totalans))*100,2)
    userpercentage=round((len(ansbyusers)/len(totalans))*100,2) #ποσοστα φοιτητων και χρηστων  (ο admin μετραει ως χρηστης)
    return render_template('answers.html',studpercentage=studpercentage,userpercentage=userpercentage,totalans=totalans,nstudents=len(ansbystudents),nusers=len(ansbyusers))

@app.route('/changeqname',methods=['GET','POST'])
def changeqname(): #αλλαγη ονοματος ερωτηματολογιου, στη περιπτωση που ειναι φοιτητης logged in ελεγχουμε αν το questionnaire id αντιστοιχει με τον ΑΜ του και επειτα αλλαζουμε το ονομα
    if 'student' in session:
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
    elif 'username' in session: #για τον admin δε χρειαζεται αντιστοιχηση απλα ψαχνουμε αν το ερωτηματολογιο με το id που εδωσε υπαρχει στο collection
        if request.method=='POST':
            qid=request.form['questionnaire_id']
            if 'findq' in request.form:
                qforchange=questionnaires.find_one({'questionnaire_id':int(qid)})
                return render_template('changeqname.html',qforchange=qforchange)
            if 'setnewname' in request.form:
                newname=request.form['newname']
                questionnaires.find_one_and_update({'questionnaire_id':int(qid)},{'$set':{'title':newname}})
                flash('Questionnaire title updated successfully!', 'info')
                return redirect(url_for('home'))
    return render_template('changeqname.html')


@app.route('/createq',methods=['GET','POST'])
def createq():
    check=False
    #auto increment για το questionnaire id
    lastq=list(questionnaires.find({}).sort({'questionnaire_id':-1}).limit(1)) 
    nextid=(lastq[0]['questionnaire_id'])+1
    if 'student' in session:
        username=session['student'] #δημιουργια ερωτηματολογιου ως φοιτητης
        stud=students_collection.find_one({'username':username})
        reg=stud.get('reg_number')
        if request.method=='POST': #παιρνουμε τον τιτλο και τα στοιχεια που εδωσε και κανουμε refresh για να εισαγει το πληθος των ερωτησεων που θελει
            if 'addquestions' in request.form:
                title=request.form['title']
                desc=request.form['desc']
                nofqs=int(request.form['nofqs'])
                check=True
                return render_template('createq.html',title=title,desc=desc,nofqs=nofqs,check=check)
            if 'create' in request.form:
                title=request.form['title']
                desc=request.form['desc']
                nofqs=int(request.form['nofqs']) #εδω περα παιρνουμε ολα τα στοιχεια μαζεμενα μαζι και τα εισαγουμε στο collection
                questions=[] #οι ερωτησεις στο questionnaires collection αποθηκευονται ως λιστα που περιεχει dicts μεσα με 2 keys (question_num,question)
                for i in range(nofqs):
                    questiondesc=request.form[f'question{i}']
                    typeofq=request.form['type']
                    finalized={'type':typeofq,'description':questiondesc,'question_num':i+1}
                    questions.append(finalized) #τελος βαζουμε ολες τις ερωτησεις μαζι, φτιαχνουμε ενα query Που περιεχει ολα τα δεδομενα και εισαγουμε το ερωτηματολογιο στη βαση
                jsoned={'student_id':reg,'questionnaire_id':nextid,'title':title,'description':desc,'unique_url':f'localhost:5000/questionnaire/{nextid}','questions':questions,'answer_count':0}
                questionnaires.insert_one(jsoned)
                return redirect(url_for('home'))
    elif 'username' in session: #Για τον admin η διαδικασια ειναι ιδια απλα βαζουμε ως student id την λεξη admin
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
                jsoned={'student_id':'admin','questionnaire_id':nextid,'title':title,'description':desc,'unique_url':f'localhost:5000/questionnaire/{nextid}','questions':questions,'answer_count':0}
                questionnaires.insert_one(jsoned)
                return redirect(url_for('home'))
    return render_template('createq.html')

@app.route('/deleteq',methods=['GET','POST'])
def deleteq(): #η διαγραφη ειναι πολυ παρομοια με την αλλαγη ονοματος ερωτηματολογιου. Βλεπουμε αν αντιστοιχουν τα ids Και αν υπαρχει το ερωτηματολογιο 
    check=False #και επειτα το διαγραφουμε οταν ο χρηστης πατησει το κουμπι delete
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
            if 'delete' in request.form: #αυτο εμφανιζεται μετα αφου εισαγει το id ο student
                qid=int(request.form['questionnaire_id'])
                questionnaires.find_one_and_delete({'student_id':reg,'questionnaire_id':qid})
                answered_questionnaires.find_one_and_delete({'questionnaire_id':qid})
                flash('questionnaire deleted succesfully!')
                return redirect(url_for('home'))
    elif 'username' in session: #για τον admin ισχυουν τα ιδια απλα δεν αντιστιχουμε student id με questionnaire id
        if request.method=='POST':
            if 'findq' in request.form:
                qid=int(request.form['qid'])
                qfordel=questionnaires.find_one({'questionnaire_id':qid})
                if qfordel:
                    check=True
                return render_template('deleteq.html',check=check,questionnaire=qfordel)
            if 'delete' in request.form:
                qid=int(request.form['questionnaire_id'])
                questionnaires.find_one_and_delete({'questionnaire_id':qid})
                answered_questionnaires.find_one_and_delete({'questionnaire_id':qid})
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
    if 'username' in session: #εισαγωγη φοιτητη, πολυ παρομοιο με εισαγωγη ερωτηματολογιου απλα εισαγουμε τα στοιχεια του φοιτητη που θελουμε
        if request.method=='POST': #σημειωση:Μονο ετσι εισαγεται ενας φοιτητης δεν μπορει να κανει register στο συστημα φοιτητης, μονο user
            username=request.form['username']
            password=request.form['password']
            name=request.form['name']
            surname=request.form['surname']
            reg_number=request.form['reg_number']
            dept=request.form['dept']
            reg_number=int(reg_number)
            #αν εχουν εισαχθει ολα τα στοιχεια και δεν ειναι κενα τοτε εισαγουμε τον φοιτητη στο συστημα
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
    
    if request.method=='POST': #η διαγραφη φοιτητη γινεται μεσω ΑΜ 
        reg_number = request.form['reg_number']
        if re.search(r'[a-zA-Z]', reg_number): #στη περιπτωση που περιεχει strings το student id
            jsoned={'reg_number':reg_number}
        else:
            jsoned={'reg_number':int(reg_number)}

        if 'findstudent' in request.form: 
            student = students_collection.find_one(jsoned) #αν υπαρχει ο φοιτητης εμφανιζονται τα στοιχεια του και μετα ο admin μπορει να επιλεξει το κουμπι delete student
            check = True
            return render_template('deletestudent.html', check=check, student=student)

        elif 'delete' in request.form:
            students_collection.delete_one(jsoned) #delete query
            return redirect(url_for('deletestudent', success=True))
    return render_template('deletestudent.html', check=check, student=student, success=success)

#for all
@app.route('/showquestionnaires',methods=['GET','POST'])
def showquestionnaires():
    q=questionnaires.find({}) #εμφανιση ολων των ερωτηματολογιων
    check=False
    
    if request.method=='POST':
        
        if 'sortbyanswer' in request.form: #εμφανιση της λιστας ερωτηματολογιων ταξινομημενη
            sorted=questionnaires.find().sort("answer_count",1)
            return(render_template('showquestionnaires.html',q=sorted))
       
        if 'showall' in request.form :
            q=questionnaires.find({}) #εμφανιση ολων παλι
        
        if 'search' in request.form: #αναζητηση ερωτηματολογιου
            uservalue=request.form['searchfield'].strip()
            check=True
            #ελεγχουμε αν ειναι ονομα φοιτητη η τμημα η ονομα ερωτηματολογιου και ετσι βγαζουμε τα αποτελεσματα, αν δεν αντιστοιχει τιποτα τοτε βγαινει κενο
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
        
        if 'bound' in request.form: #εδω κανουμε αναζητηση με βαση το πληθος απαντησεων που εβαλε (πχ απο 1 εως 3 απαντησεις)
            lowerbound=request.form['lowerbound'].strip()#κατω φραγμα
            upperbound=request.form['upperbound'].strip()#ανω φραγμα
            if re.search(r'[a-zA-Z]', lowerbound) or re.search(r'[a-zA-Z]',upperbound) or lowerbound=='' or upperbound=='':
                return render_template('showquestionnaires.html',q=q) #ελεγχουμε υποπεριπτωσεις οπου εχει εισαγει στρινγκ η κατω φραγμα>ανω φραγμα
            else:
                lowerbound=int(lowerbound)
                upperbound=int(upperbound)
                check=True
                if lowerbound>upperbound: #κατω φραγμα>ανω φραγμα
                    return render_template('showquestionnaires.html',q=q)
                rangeofq=list(questionnaires.find({'answer_count':{'$gte':lowerbound,'$lte':upperbound}})) #αλλιως ψαχνουμε με βαση αυτο το query
                return render_template('showquestionnaires.html',questionnaire=rangeofq,check=check,length=len(rangeofq))
        
        if 'sortaftersearch' in request.form:
            length=int(request.form['lengthofresults'])
            #ταξινομηση των αποτελεσματων αναζητησης
            for i in range(length): 
                qid=request.form.getlist('qid') #παιρνουμε ολα τα id των εμφανιζομενων ερωτηματολογιων

            tmp=list(map(int,qid)) #απο τα input fields τα δεδομενα επιστρεφονται ως string, ετσι φτιαχνουμε μια λιστα οπου μετατρεπουμε τα id απο string σε list of ints
            itemstosort=[]
            for i in range(len(tmp)): #επειτα βαζουμε σε μια λιστα καθε αντικειμενο με το id Που εχουν και ταξινομουμε τη λιστα με βαση το πληθος απαντησεων
                itemstosort.append(questionnaires.find_one({'questionnaire_id':tmp[i]})) #find_one γιατι πρεπει να κανουμε συνεχομενη αναζητηση πολλων ids 
            #last one remaining pls fix
            itemstosort.sort(key=lambda x: x['answer_count']) #επιστρεφουμε την ταξινομημενη λιστα και εμφανιζεται στο frontend
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
        fromstudent=True #στο answered questionnaires collection υπαρχει ενα αντικειμενο με boolean value για στατιστικους λογους για να δουμε απαντησε φοιτητης η οχι
    questionnaire=questionnaires.find_one({'questionnaire_id':int(num)})
    questions=questionnaire['questions']
    if request.method=='POST':
        useranswers=[]
        if 'answers' in request.form:
            for i in range(1,len(questionnaire['questions'])+1):
                qn=questions[i-1]['question_num']
                print(qn)
                answer=request.form[f'question{i}']  #παιρνουμε ολες τις απαντησεις του χρηστη και τις εισαγουμε σε ενα dict που θα στειλουμε στη βαση
                if re.fullmatch(r'^\d+$', answer):
                    jsoned={'question_num':qn,'content':int(answer)}
                else:
                    jsoned={'question_num':qn,'content':answer}
                useranswers.append(jsoned) #οι απαντησεις αποθηκευονται σε λιστα μεσα στο dict
        send={'questionnaire_id':int(num),'from_student':fromstudent,'answers':useranswers}
        answered_questionnaires.insert_one(send) #εισαγουμε στη βαση δεδομενων την απαντηση του χρηστη
        return render_template('home.html')
    return render_template('answerq.html',questionnaire=questionnaire,questions=questions)


# Run the Flask App
if __name__ == '__main__': #0.0.0.0 για να τρεξει μεσω docker container
    app.run(debug=True, host='0.0.0.0', port=5000)