from flask import Flask, url_for, render_template, redirect, request, g
from wtforms import StringField, DateField, BooleanField, TextAreaField
from wtforms.widgets import TextArea
from flask_wtf import FlaskForm, widgets, Form
from wtforms.validators import DataRequired, Length
import sqlite3

# global variable Num helps with the calculation of the index for each ToDOItem
Num = 1


app = Flask(__name__)
app.secret_key = 'very secret'


def get_db():
    if not hasattr(g, 'sqlite_db'):
        con = sqlite3.connect('todo.db')
        g.sqlite_db = con
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'): g.sqlite_db.close()


class ToDoItem(FlaskForm):
    # ToDoItem's attributes are defined by Fields from wtforms
    title = TextAreaField('title', validators=[DataRequired(), Length(min=1)])
    description = TextAreaField('description')
    due = TextAreaField('due')
    done = BooleanField(False)

class ToDoList(ToDoItem):
    #stores local arrays for todo items as well as already finished tasks
    posts = []
    done_posts = []
    search_posts = []

class SearchForm(Form):
    search = TextAreaField('search', widget=TextArea(), validators=[DataRequired(), Length(min=1)])


@app.route("/", methods=['GET','POST'])
def toDO():
    # database connection with sqlite3
    con = get_db()
    cur = con.cursor()
    cur.execute('select * from todo')
    # ToDoItems are stored locally for display
    ToDoList.posts = [{
        'ID': row[0],
        'title': row[1].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'content': row[2].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'due': row[3].replace("(", "").replace(")", "").replace(",","").replace("'","")
    } for row in cur.fetchall()]
    return render_template('toDO.html', posts = ToDoList.posts, title = 'toDO',form = ToDoItem())


@app.route("/add_entry", methods=['GET','POST'])
def add_entry():
    form = ToDoItem()
    global Num

    # attributes pull their data form user input
    title = form.title.data,
    content = form.description.data,
    due = form.due.data

    # inserting input values into first database
    con = get_db()
    cur = con.cursor()
    cur.execute('insert into todo values (?,?,?,?)',(int(Num),str(title), str(content), str(due)))
    con.commit()

    con = get_db()
    cur = con.cursor()
    cur.execute('select * from todo')
    posts = [{
        'ID': row[0],
        'title': row[1].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'content': row[2].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'due': row[3].replace("(", "").replace(")", "").replace(",","").replace("'",""),
    } for row in cur.fetchall()]
    Num += 1


    ToDoList.posts = posts.copy()
    return redirect('/')


@app.route("/done")
def done():
    # renders page where all done tasks (which are being pulled from todo_done in the db) are displayed
    return render_template('done.html', done_posts = ToDoList.done_posts, title = 'done')



@app.route("/check")
def check():
    global Num

    id = int(request.args.get('id'))
    con = get_db()
    cur = con.cursor()

    # pulling the attributes from the checked ToDoItem
    cur.execute("SELECT * FROM todo where id=id")
    save = cur.fetchall()
    entry = save[id-1]

    id =entry[0]
    title =entry[1]
    description =entry[2]
    due =entry[3]

    # inserting checked iteam into other db table
    cur.execute('INSERT INTO todo_done VALUES(?,?,?,?)',(id,title,description,due))
    con.commit()

    con = get_db()
    cur = con.cursor()
    cur.execute('select * from todo_done')
    posts = [{
        'ID': row[0],
        'title': row[1].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'content': row[2].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'due': row[3].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'done': False

    } for row in cur.fetchall()]

    # saving done tasks locally for display
    ToDoList.done_posts = posts.copy()


    # deleting checked item from the db table todo
    con = get_db()
    cur.execute('DELETE FROM todo WHERE id=?', (id,))
    con.commit()
    con = get_db()
    cur = con.cursor()
    i = id + 1
    while i <= len(ToDoList.posts):
        cur.execute('UPDATE todo SET id=? WHERE id=?', (i - 1, i))
        con.commit()
        i += 1
    Num -= 1

    return redirect ('/')

@app.route("/delete")
def delete_entry():
    global Num
    id = int(request.args.get('id'))
    con = get_db()
    cur = con.cursor()

    #deleting item from todo in db
    cur.execute('DELETE FROM todo WHERE id=?', (id,))
    con.commit()
    con = get_db()
    cur = con.cursor()
    i = id + 1
    while i <= len(ToDoList.posts):
        cur.execute('UPDATE todo SET id=? WHERE id=?', (i - 1, i))
        con.commit()
        i += 1
    Num -= 1
    return redirect('/')

@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/search", methods=['GET','POST'])
def search():
    return render_template('search.html', form = SearchForm(), title = 'Search', posts = ToDoList.search_posts)


@app.route("/search_results", methods=['GET','POST'])
def search_results():
    form = SearchForm()
    search = form.search.data
    search = "('" + search + "',)"

    con = get_db()
    cur = con.cursor()
    cur.execute('select * from todo where title = ?', (search,))
    posts = [{
        'ID': row[0],
        'title': row[1].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'content': row[2].replace("(", "").replace(")", "").replace(",","").replace("'",""),
        'due': row[3].replace("(", "").replace(")", "").replace(",","").replace("'","")
    } for row in cur.fetchall()]
    ToDoList.search_posts = posts.copy()
    return redirect('/search')

if __name__ == '__main__':
            app.run(debug = True)
