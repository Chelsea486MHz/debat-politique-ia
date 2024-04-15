from flask import Flask, request, send_file, after_this_request
from flask_api import status
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC
from TTS.api import TTS
import importlib
import hashlib
import logging
import torch
import uuid
import os

# Initialize Flask
app = Flask(__name__)

# Configure logging to file
logging.basicConfig(level=logging.INFO)
logging.basicConfig(filename='xtts.log', level=logging.INFO)

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

# Status report
logging.info('Model:        ', tts.model_name)
logging.info('Device:       ', device)
if device == 'cuda':
    logging.info('CUDA device:  ', torch.cuda.get_device_name())
else:
    logging.info('CPU cores:    ', os.cpu_count())
logging.info('Server is UP and GO for requests')


# Represents the entries in the database
class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(48), unique=True, nullable=False)


@app.route('/api/generate', methods=['POST'])
def api_generate():
    # Get the headers
    try:
        token = request.headers.get('Authorization')
        content_type = request.headers.get('Content-Type')
        # Check for token format
        if not token.startswith('Bearer '):
            raise Exception('Invalid authorization token format')
        # Check for token length
        if len(token.split(' ')[1]) != 64:
            raise Exception('Invalid authorization token length')
        # Check for content type
        if content_type != 'application/json':
            raise Exception('Invalid content type')
    except (KeyError, Exception) as e:
        print(e)
        return 'Unauthorized', status.HTTP_400_BAD_REQUEST

    # Get the request body
    try:
        requested_text = request.json['texttospeak']
        requested_voice = request.json['voice']
        requested_filter = request.json['voicefilter']
    except KeyError as e:
        print(e)
        return 'Bad request', status.HTTP_400_BAD_REQUEST

    # Authenticate the request
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    try:
        Token.query.filter_by(token=hashed_token).first()
    except Exception as e:
        print(e)
        return 'Unauthorized', status.HTTP_401_UNAUTHORIZED

    # Generate a random UUID as the file name for the audio to generate
    filename_without_ext = str(uuid.uuid1())
    audio_file = filename_without_ext + '.wav'

    # Log the request
    logging.info(
        '----------- BEING REQUEST REPORT -----------',
        'UTC:              ', str(datetime.now(UTC)),
        'Host:             ', request.remote_addr,
        'Token:            ', hashed_token,
        'User-Agent:       ', request.headers.get('User-Agent'),
        'UUID:             ', filename_without_ext,
        'Requested text:   ', requested_text,
        'Requested voice:  ', requested_voice,
        'Requested filter: ', requested_filter,
        '-----------  END REQUEST REPORT  -----------'
    )

    # Verify the requested voice exists
    # reminder: voices are .wav files located in ./voices
    voice_file = f'/xtss/voices/{requested_voice}.wav'
    if not os.path.exists(voice_file):
        print('Invalid voice')
        return 'Bad request', status.HTTP_400_BAD_REQUEST

    # Generate audio file
    try:
        tts.tts_to_file(text=requested_text,
                        file_path=audio_file,
                        speaker_wav=voice_file,
                        language="fr")
    except Exception as e:
        print(e)
        return 'Internal error', status.HTTP_500_INTERNAL_SERVER_ERROR

    # Apply requested voice filters
    if requested_filter != 'none':
        try:
            module = importlib.import_module(f"filters.{requested_filter}")
            module.filter(audio_file)
        except module.ModuleNotFoundError:
            print('Invalid filter')
            return 'Bad request', status.HTTP_400_BAD_REQUEST

    # Remove the audio file after the request is done
    @after_this_request
    def cleanup(response):
        try:
            os.remove(audio_file)
        except Exception as e:
            print(e)
        return response

    # Return the audio file
    return send_file(audio_file, mimetype="audio/wav"), status.HTTP_200_OK