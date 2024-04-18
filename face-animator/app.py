from flask import Flask, request, send_file, after_this_request
from flask_api import status
from flask_sqlalchemy import SQLAlchemy
from minio import Minio
from datetime import datetime
import subprocess
import tempfile
import hashlib
import uuid
import os

# Check if the logfile already exists, rename with .date if it does
if os.path.exists('/var/log/face-animator/requests.log'):
    os.rename('/var/log/face-animator/requests.log', '/var/log/face-animator/requests.log.' + str(datetime.now()))

# Initialize Flask
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'wav'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MinIO config
DEFAULT_BUCKET = os.environ.get('S3_BUCKET')
minio_client = Minio(
    os.environ.get('S3_HOST'),
    access_key=os.environ.get('S3_ACCESS_KEY'),
    secret_key=os.environ.get('S3_SECRET_KEY'),
    secure=False
)

# Database config
DATABASE_HOST = os.environ.get('DB_HOST')
DATABASE_NAME = os.environ.get('DB_NAME')
DATABASE_USER = os.environ.get('DB_USER')
DATABASE_PASS = os.environ.get('DB_PASS')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(DATABASE_USER, DATABASE_PASS, DATABASE_HOST, DATABASE_NAME)
db = SQLAlchemy(app)


# Represents the entries in the database
class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(48), unique=True, nullable=False)


def get_face_from_minio(face_name, temp_folder):
    face_file = face_name + '.png'
    try:
        minio_client.fget_object(
            os.environ.get('S3_BUCKET'),
            'faces/' + face_name + '.png',
            os.path.join(temp_folder, face_file)
        )
    except Exception as e:
        print(e)
        return None
    return face_file


@app.route('/api/generate/video', methods=['POST'])
def api_generate_video():
    # Create a directory unique to each request
    request_folder_uuid = str(uuid.uuid1())
    request_output_dir = os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], request_folder_uuid))

    # Get the wav file
    try:
        voice_file = request.files['voice']
        if voice_file.filename.split('.')[-1] not in ALLOWED_EXTENSIONS:
            raise Exception('Invalid file extension')
        voice_file.save(os.path.join(request_output_dir, voice_file.filename))
    except (KeyError, Exception) as e:
        print(e)
        return 'Bad request 1', status.HTTP_400_BAD_REQUEST

    # Get the headers
    try:
        token = request.headers.get('Authorization')
        # Check for token format
        if not token.startswith('Bearer '):
            raise Exception('Invalid authorization token format')
        # Check for token length
        if len(token.split(' ')[1]) != 64:
            raise Exception('Invalid authorization token length')
        # Check for content type
        if request.headers.get('Content-Type') != 'audio/wav':
            raise Exception('Invalid content type')
    except (KeyError, Exception) as e:
        print(e)
        return 'Bad request 2', status.HTTP_400_BAD_REQUEST

    # Authenticate the request
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    try:
        Token.query.filter_by(token=hashed_token).first()
    except Exception as e:
        print(e)
        return 'Unauthorized', status.HTTP_401_UNAUTHORIZED

    # Get the requested actor
    try:
        requested_actor = request.args.get('actor')
    except KeyError as e:
        print(e)
        return 'Bad request 3', status.HTTP_400_BAD_REQUEST

    # TODO: Sanitize the input
    # TODO: Sanitize the input
    # TODO: Sanitize the input
    # TODO: Sanitize the input
    # TODO: Sanitize the input

    # Get the actors file from MinIO
    actors_file = 'actors.yml'
    try:
        minio_client.fget_object(
            os.environ.get('S3_BUCKET'),
            'actors.yml',
            actors_file
        )
    except Exception as e:
        print(e)
        return 'Internal error', status.HTTP_500_INTERNAL_SERVER_ERROR

    # Parse the actors file to get the face to use
    try:
        with open(actors_file, 'r') as file:
            actors = yaml.safe_load(file)
            requested_face = actors[requested_actor]['face']
            file.close()
    except Exception as e:
        print(e)
        return 'Internal error', status.HTTP_500_INTERNAL_SERVER_ERROR

    # Get the face file from MinIO
    face_file = get_face_from_minio(requested_face, request_output_dir)
    if face_file is None:
        return 'Bad request', status.HTTP_400_BAD_REQUEST

    # Move the face file to the request directory
    os.rename(face_file, os.path.join(request_output_dir, face_file))

    # Generate the video
    try:
        args = ['python', './SadTalker/inference.py', '--driven_audio', voice_file, '--source_image', face_file, '--results_dir', request_output_dir, '--still', '--preprocess', 'full', '--enhancer', 'gfpgan']
        subprocess.call(args)
    except Exception as e:
        print(e)
        return 'Internal server error', status.HTTP_500_INTERNAL_SERVER_ERROR

    # The outfile file has an unknown name, but ends in .mp4
    # We have to find it
    for file in os.listdir(request_output_dir):
        if file.endswith('.mp4'):
            output_video = os.path.join(request_output_dir, file)
            break

    # Remove the video file after the request is done
    @after_this_request
    def cleanup(response):
        try:
            os.remove(request_output_dir)
        except Exception as e:
            print(e)
        return response

    # Log the request
    with open('/var/log/face-animator/requests.log', 'a') as logfile:
        logfile.write('report:\n')
        logfile.write('  utc: ' + str(datetime.now().replace(tzinfo=UTC).isoformat()) + '\n')
        logfile.write('  host: ' + request.remote_addr + '\n')
        logfile.write('  token-hash: ' + hashed_token + '\n')
        logfile.write('  user-agent: ' + request.headers.get('User-Agent') + '\n')
        logfile.write('  uuid: ' + request_folder_uuid + '\n')
        logfile.write('  face: ' + requested_face + '\n')
        logfile.close()

    # Return the audio file
    return send_file(output_video, mimetype="video/mp4"), status.HTTP_200_OK
