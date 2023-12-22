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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + DATABASE_USER + ':' + DATABASE_PASS + '@' + DATABASE_HOST + '/' + DATABASE_NAME

db = SQLAlchemy(app)

# Use CUDA if available
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)


# Represents the entries in the database
class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(48), unique=True, nullable=False)


@app.route('/generate', methods=['POST'])
def generate_step():
    print('Request received')

    # Check if the authorization token is included in the request headers
    token = request.headers.get('Authorization')
    if not token:
        return 'Unauthorized', 401
    print('Request has authentication token')

    # Validate the hashed authorization token against the database
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    if not Token.query.filter_by(token=hashed_token).first():
        print('Authentication failed')
        return 'Unauthorized', 401
    print('Request authenticated')

    # Extract the text from the request
    try:
        request_variables = request.json
        requested_text = request_variables.get('texttospeak')
        requested_voice = request_variables.get('voice')
    except Exception as e:
        return f"Error: {e}", 400

    # Generate audio
    print('Generating audio')
    tts.tts_to_file(text=requested_text,
                    file_path="output.wav",
                    speaker_wav=requested_voice,
                    language="fr")

    # Return the audio file
    print('Returning audio file')
    return send_file("output.wav")


if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', False))
