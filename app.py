from flask import send_from_directory
from flask import Flask, flash, request, redirect, url_for

from flask import request,session
from werkzeug.utils import secure_filename
from flask import render_template
from url_utils import get_base_url
import os
from keras.models import load_model
from keras.preprocessing import image
import numpy as np

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.secret_key="123"


con=sqlite3.connect("database.db")
con.execute("create table if not exists customer(pid integer primary key,name text,password varchar)")
con.close()

# Sample quiz data
questions = [
    {
        'question': 'What is Alzheimer\'s disease?',
        'options': [
            'A type of cancer',
            'A neurological disorder',
            'A viral infection',
            'A bacterial infection'
        ],
        'correct_answer': 'A neurological disorder'
    },
    {
        'question': 'Which part of the brain is primarily affected by Alzheimer\'s?',
        'options': [
            'Cerebellum',
            'Frontal lobe',
            'Hippocampus',
            'Occipital lobe'
        ],
        'correct_answer': 'Hippocampus'
    },
    {
        'question': 'What is a common early symptom of Alzheimer\'s disease?',
        'options': [
            'Joint pain',
            'Memory loss',
            'Vision problems',
            'Hearing loss'
        ],
        'correct_answer': 'Memory loss'
    },
    {
        'question': 'Is Alzheimer\'s disease reversible?',
        'options': [
            'Yes',
            'No'
        ],
        'correct_answer': 'No'
    },
    {
        'question': 'What age group is most commonly affected by Alzheimer\'s?',
        'options': [
            'Children',
            'Teenagers',
            'Young adults',
            'Elderly'
        ],
        'correct_answer': 'Elderly'
    },
    {
        'question': 'Are there any known ways to prevent Alzheimer\'s disease?',
        'options': [
            'Yes, through vaccination',
            'Yes, through regular exercise and a healthy diet',
            'No, it cannot be prevented'
        ],
        'correct_answer': 'Yes, through regular exercise and a healthy diet'
    },
    {
        'question': 'What is the main protein associated with Alzheimer\'s disease?',
        'options': [
            'Insulin',
            'Hemoglobin',
            'Amyloid beta',
            'Collagen'
        ],
        'correct_answer': 'Amyloid beta'
    },
    {
        'question': 'How is Alzheimer\'s disease diagnosed?',
        'options': [
            'Blood test',
            'X-ray',
            'MRI scan',
            'Clinical evaluation and cognitive tests'
        ],
        'correct_answer': 'Clinical evaluation and cognitive tests'
    },
    {
        'question': 'Is there a cure for Alzheimer\'s disease?',
        'options': [
            'Yes',
            'No'
        ],
        'correct_answer': 'No'
    },
    {
        'question': 'What organization uses the purple color as a symbol for Alzheimer\'s awareness?',
        'options': [
            'American Cancer Society',
            'Alzheimer\'s Association',
            'World Health Organization',
            'Red Cross'
        ],
        'correct_answer': 'Alzheimer\'s Association'
    },
]


verbose_name = {
	0: "AD",
	1: "CN",
	2: "MCI"
}

# Select model
model = load_model('alzahmimar_vgg.h5', compile=False)

def predict_label(img_path):
	test_image = image.load_img(img_path, target_size=(150,150))
	test_image = image.img_to_array(test_image)/255.0
	test_image = test_image.reshape(1, 150,150,3)

	predict_x=model.predict(test_image) 
	classes_x=np.argmax(predict_x,axis=1)
	
	return verbose_name[classes_x[0]]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/')
def index():
    return render_template('index.html')


# @app.route('/home')
# def index():
#     return render_template('home.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM customer WHERE name=?", (name,))
        data = cur.fetchone()

        print(f"Entered username: {name}")
        print(f"Entered password: {password}")
        print(f"Data from database: {data}")

        if data and check_password_hash(data["password"], password):
            # Correct username and password
            session["name"] = data["name"]
            return redirect(url_for('home'))
        else:
            flash("Username and Password Mismatch", "danger")

    return redirect(url_for("index"))




@app.route('/register', methods=['GET', 'POST'])
def register():
    con = None
    if request.method == 'POST':
        try:
            name = request.form['name']
            password = request.form['pass']

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("INSERT INTO customer(name, password) VALUES (?, ?)", (name, hashed_password))
            con.commit()
            flash("Record Added Successfully", "success")
        except Exception as e:
            print(f"Error: {e}")
            flash("Error in Insert Operation", "danger")
        finally:
            if con:
                con.close()
            return redirect(url_for("index"))

    return render_template('register.html')

@app.route("/submit", methods = ['GET', 'POST'])
def get_output():
	if request.method == 'POST':
		img = request.files['my_image']

		img_path = "static/tests/" + img.filename	
		img.save(img_path)

		predict_result = predict_label(img_path)

	return render_template("prediction.html", prediction = predict_result, img_path = img_path)

## CUSTOM ROUTES
@app.route(f'/data.html')
def data():
    return render_template('data.html')


@app.route(f'/miscellaneous.html')
def miscellaneous():
    return render_template('miscellaneous.html', questions=questions)


# @app.route(f'/home.html')
# def redirect_home():
#     return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

from flask import abort

@app.route('/submit_que', methods=['POST'])
def submit_que():
    score = 0
    user_answers = {key: request.form.get(key, '') for key in request.form}

    for question in questions:
        user_answer = user_answers.get(question['question'])
        if user_answer is not None:
            # Compare the lowercase version of answers to make it case-insensitive
            if user_answer.lower() == question['correct_answer'].lower():
                score += 1
        else:
            # If a question is not answered, you may handle it as you wish (e.g., consider it wrong or ignore)
            # For now, we'll abort with a 400 Bad Request status
            abort(400, f"Answer for question '{question['question']}' is missing.")

    return render_template('result.html', score=score, total_questions=len(questions))

@app.route('/logout')
def logout():
    if "name" in session:
        session.clear()
    return redirect(url_for("index"))


if __name__ == '__main__':

    app.run(port=5000, debug=True)



