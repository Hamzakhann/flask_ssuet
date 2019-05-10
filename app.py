from flask import Flask ,request, render_template , flash , redirect , url_for , session
import logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form , StringField , TextAreaField, PasswordField , validators
from passlib.hash import sha256_crypt
from functools import wraps



app = Flask(__name__)




# Config MySQL
app.config['MYSQL_HOST'] = "remotemysql.com"
app.config['MYSQL_USER'] = "CsJjcWdoOF"
app.config['MYSQL_PASSWORD'] = "bVjuyIAvaD"
app.config['MYSQL_DB'] = "CsJjcWdoOF"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"




# app.config['MYSQL_HOST'] = "localhost"
# app.config['MYSQL_USER'] = "root"
# app.config['MYSQL_PASSWORD'] = "123456"
# app.config['MYSQL_DB'] = "newAppp"
# app.config['MYSQL_CURSORCLASS'] = "DictCursor"


# Init database
mysql = MySQL(app)
# Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()
    
    result = cur.execute("SELECT * FROM articles")
    articles= cur.fetchall()
    if result > 0:
        return render_template('articles.html' , articles=articles)
    else:
        msg = "No article found"
        return render_template('articles.html' , msg=msg)
    cur.close()

@app.route('/article/<string:id>')
def article(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    article = cur.fetchone()
    return render_template('article.html' ,  article=article )

class RegisterForm(Form):
    name = StringField('Name' , [validators.Length(min=1 , max=50)])
    username = StringField('Username' , [validators.Length(min=4 , max=25)])
    email = StringField('Email' , [validators.Length(min=6 , max=50)])
    password = PasswordField('Password' , [
        validators.DataRequired(),
        validators.EqualTo('confirm' , message = 'Password do not match')
        ])
    confirm = PasswordField('Confirm Password')


@app.route('/register' , methods=['GET' , 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name =  form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name , email , username , password) VALUES(%s, %s , %s , %s)" ,
        (name , email , username , password))
        
        # commit to db
        mysql.connection.commit()

        # close connectioin
        cur.close()

        flash("You are now registered and can login" , "success")
        return redirect(url_for('login'))

    return render_template('register.html' , form=form)


@app.route('/login' , methods=['GET' , 'POST'])
def login():
    if request.method == 'POST':
        #GET FORM FIELDS
        username = request.form['username']
        password_candid = request.form['password']

        #CREATE CURSOR
        cur = mysql.connection.cursor()
        #GET USER BY USERNAME
        result = cur.execute("SELECT * FROM users WHERE username = %s" ,[username])

        if result > 0:
            #GET STORED HASH
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candid , password):
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash("You are now logged in " , 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid LOgin"
                return render_template('login.html' , error=error)
            cur.close()
        else:
            error = "Username not found"
            return render_template('login.html' ,error = error)
    if 'logged_in' not in session:
        return render_template('login.html')
    else:
        return redirect(url_for('dashboard'))


def is_logged_in(g):
    @wraps(g)
    def wrap(*args , **kwargs):
        if 'logged_in' in session:
            return g(*args , **kwargs)
        else:
            flash("Un authorized, Please login " , "danger")
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out" , "success")
    return redirect(url_for('login'))


@app.route('/dashboard' )
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")
    
    articles= cur.fetchall()
    if result > 0:
        return render_template('dashboard.html' , articles=articles)
    else:
        msg = "No article found"
        return render_template('dashboard.html' , msg=msg)

    cur.close()


class ArticleForm(Form):
    title = StringField('Title' , [validators.Length(min=1 , max=200)])
    body = TextAreaField('Body' , [validators.Length(min=40)])

@app.route('/add_article' , methods=['GET' , 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method =='POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO articles(title , body , author) VALUES(%s , %s , %s)", (title,body,session['username']))
        
        #Commit to db
        mysql.connection.commit()
        
        #Close the db
        cur.close()
        flash("Article Created" , "success")
        return redirect(url_for('dashboard'))
    return render_template("add_article.html" , form=form)


@app.route('/edit_article/<id>' , methods=['GET' , 'POST'])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id = %s" , [id])
    article = cur.fetchone()
    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method =='POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title , body , id))
        
        #Commit to db
        mysql.connection.commit()

        #Close the db
        cur.close()
        flash("Article Updated" , "success")
        return redirect(url_for('dashboard'))
    return render_template("edit_article.html" , form=form)

@app.route("/delete_article/<id>" , methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor() 
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash("Article Deleted" , "success")
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.secret_key = 'secret'
    app.run(debug=True)
