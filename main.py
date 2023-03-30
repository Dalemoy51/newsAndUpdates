from flask import Flask, render_template, redirect, url_for,g, session ,request, jsonify, flash
import sqlite3
from werkzeug.utils import secure_filename
import os
import re

app = Flask("__main__")


app.secret_key = "Secret key"

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.before_request
def conn():
    g.conn = sqlite3.connect("newsupdate.db")
    g.cur = g.conn.cursor()


@app.route("/")
def index():
    if "login" not in session:
        return redirect(url_for("login")) 
    image_names = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    sql = "SELECT * FROM contacts"
    g.cur.execute(sql)
    g.conn.commit()
    messages = g.cur.fetchall()
    
    return render_template("index.html", data=session['login'], image_names=image_names,   messages = messages)

@app.route("/login")
def login():
    if "login" in session:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/login_process", methods=['POST'])
def login_process():

    username = request.form['username']
    password = request.form['password']
    sql = "SELECT * FROM account WHERE username = '{}' AND password = '{}'".format(username,password)
    g.cur.execute(sql)
    data = g.cur.fetchall()

    if len(data) == 1:
        session['login'] = data[0]
        return redirect(url_for("index"))
    flash("Invalid Username or Password!")
    return redirect(url_for("login")) 

@app.route("/logout")
def logout():    
    session.pop("login", None)
    return redirect(url_for('login'))

@app.route("/display")
def display():
    if "login" not in session:
        return redirect(url_for("login")) 
    image_names = os.listdir(app.config['UPLOAD_FOLDER'])

    sql = "SELECT * FROM contacts"
    g.cur.execute(sql)
    g.conn.commit()
    messages = g.cur.fetchall()
    
    
    return render_template('display.html',image_names=image_names, messages=messages)

@app.route('/get_images')
def get_images():
    # Get list of image paths in folder
    image_folder = 'static/uploads'
    image_paths = [os.path.join(image_folder, filename) for filename in os.listdir(image_folder)]
    
    # Return list of image paths as JSON
    return jsonify(image_paths=image_paths)

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        # check if there is an image in the request
        if 'image' not in request.files:
            return 'No image in the request'
        image = request.files['image']
        # check if image is empty
        if image.filename == '':
            return 'No image selected'
        # save image to upload folder
        if image and allowed_file(image.filename):
            # Secure the filename and save it to upload folder
            filename = secure_filename(image.filename)
            
            # Get a list of existing images in the upload folder
            existing_images = os.listdir(app.config['UPLOAD_FOLDER'])
            
            # Find the highest existing index and add 1 to get the new index
            max_index = 0
            for existing_image in existing_images:
                match = re.search(r'image\[(\d+)\]', existing_image)
                if match:
                    index = int(match.group(1))
                    max_index = max(max_index, index)
            new_index = max_index + 1
            
            # Get the file extension from the original filename
            file_ext = os.path.splitext(filename)[1]
            
            # Rename the file to "image[new_index].ext"
            new_filename = f'image[{new_index}]{file_ext}'
            
            # Save the file with the new filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
            
            # Return the filename to template and display it using image tag
            return jsonify({
                'image_path': url_for('static', filename='uploads/' + new_filename),
                'image_name': new_filename
             })
    else:
        # render upload form template
        return render_template('index.html')

    
@app.route('/delete_image', methods=['POST', 'GET'])
def delete_image():
    if request.method == 'POST':
        data = request.get_json()
        image_name = data['image_name']
    else:
        image_name = request.args.get('image_name')
    
    image_folder = app.config['UPLOAD_FOLDER']
    image_path = os.path.join(image_folder, image_name)
    
    # Prompt user for confirmation
    if request.args.get('confirm') == 'yes':
        try:
            os.remove(image_path)
            return jsonify({'message': 'Image deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)})
    else:
        return jsonify({'message': 'Are you sure you want to delete this image?', 'confirm_url': '/delete_image?confirm=yes&image_name=' + image_name})
    
@app.route("/update_contact", methods=["POST"])
def update_contact():
    contact_id = request.form["contact_id"]
    new_contact = request.form["new_contact"]

    sql = "UPDATE contacts SET contacts = ? WHERE id = ?"
    g.cur.execute(sql, (new_contact, contact_id))
    g.conn.commit()

    return jsonify(new_contact=new_contact)

@app.route("/get_contact", methods=["GET"])
def get_contact():
    # query your database for the latest contact information
    sql = "SELECT contacts FROM contacts ORDER BY id DESC LIMIT 1"
    g.cur.execute(sql)
    contact = g.cur.fetchone()[0]

    # return the contact information as a JSON response
    return jsonify(contact=contact)

if __name__ == ('__main__'):
    app.run(debug=True, host='0.0.0.0')