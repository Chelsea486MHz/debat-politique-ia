from flask import Flask, request, send_file
from flask_sqlalchemy import SQLAlchemy
from TTS.api import TTS
import hashlib
import torch
import os

# Initialize Flask
app = Flask(__name__)

# Database config
DATABASE_HOST = os.environ.get('DB_HOST')
DATABASE_NAME = os.environ.get('DB_NAME')
DATABASE_USER = os.environ.get('DB_USER')
DATABASE_PASS = os.environ.get('DB_PASS')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(DATABASE_USER, DATABASE_PASS, DATABASE_HOST, DATABASE_NAME)

db = SQLAlchemy(app)

# Use CUDA if available
torch.set_num_threads(int(os.environ.get("NUM_THREADS", os.cpu_count())))
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)


# Represents the entries in the database
class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(48), unique=True, nullable=False)


@app.route('/api/generate', methods=['POST'])
def generate_step():
    # Check for token in headers
    if not request.headers.get('Authorization'):
        print('No authorization token provided')
        return 'Unauthorized', 401

    # Check for token format
    if not request.headers.get('Authorization').startswith('Bearer '):
        print('Invalid authorization token format')
        return 'Unauthorized', 401

    # Check for token length
    token = request.headers.get('Authorization').split(' ')[1]
    if len(token) != 64:
        print('Invalid authorization token length')
        return 'Unauthorized', 401

    # Validate the hashed authorization token against the database
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    if not Token.query.filter_by(token=hashed_token).first():
        print('Authentication failed')
        return 'Unauthorized', 401

    # Check for required fields
    if not request.json or 'texttospeak' not in request.json.keys() or 'voice' not in request.json.keys():
        print('Required fields are missing')
        return 'Bad request', 400

    # Extract the text from the request
    requested_text = request.json.get('texttospeak')
    requested_voice = "{}.wav".format(request.json.get('voice'))

    # Generate audio file
    tts.tts_to_file(text=requested_text,
                    file_path="output.wav",
                    speaker_wav=requested_voice,
                    language="fr")

    # Return the audio file
    print('Returning audio file')
    return send_file("output.wav", mimetype="audio/wav")


if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', False))
