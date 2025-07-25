from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
# Cambio forzado para reconstruir
app = Flask(__name__)

# Render pone DATABASE_URL en variables de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

if not os.path.exists('uploads'):
    os.makedirs('uploads')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80), nullable=False)
    receiver = db.Column(db.String(80), nullable=False)
    subject = db.Column(db.String(200))
    body = db.Column(db.Text)
    filename = db.Column(db.String(200))

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'User exists'}), 400
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        return jsonify({'message': 'Login successful'})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/send', methods=['POST'])
def send():
    sender = request.form['sender']
    receiver = request.form['receiver']
    subject = request.form['subject']
    body = request.form['body']
    filename = None

    if 'file' in request.files:
        file = request.files['file']
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_msg = Message(sender=sender, receiver=receiver, subject=subject, body=body, filename=filename)
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({'message': 'Message sent'})

@app.route('/inbox/<username>')
def inbox(username):
    messages = Message.query.filter_by(receiver=username).all()
    output = []
    for m in messages:
        output.append({
            'id': m.id,
            'sender': m.sender,
            'subject': m.subject,
            'body': m.body,
            'filename': m.filename
        })
    return jsonify(output)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_message(id):
    msg = Message.query.get(id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
        return jsonify({'message': 'Message deleted'})
    return jsonify({'error': 'Message not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
