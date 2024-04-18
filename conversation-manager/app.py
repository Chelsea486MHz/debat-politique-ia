from flask import Flask, request, send_file, after_this_request
from flask_api import status
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC
from minio import Minio
import requests
import hashlib
import base64
import uuid
import yaml
import os

# Check if the logfile already exists, rename with .date if it does
if os.path.exists('/var/log/conversation-manager/requests.log'):
    os.rename('/var/log/conversation-manager/requests.log', '/var/log/conversation-manager/requests.log.' + str(datetime.now()))

# Initialize Flask
app = Flask(__name__)

# MinIO config
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


def get_chat_completion(actor, message_history):
    try:
        response = requests.post(
            os.environ.get('OPENAI_ENDPOINT'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + os.environ.get('OPENAI_API_KEY')
            },
            json={
                'model': os.environ.get('OPENAI_MODEL'),
                'messages': message_history,
                'max_tokens': 150
            },
            timeout=10
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(e)
        return 'Internal error', status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/api/generate/text', methods=['POST'])
def api_generate_text():
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
        if request.headers.get('Content-Type') != 'application/json':
            raise Exception('Invalid content type')
    except (KeyError, Exception) as e:
        print(e)
        return 'Bad request 1', status.HTTP_400_BAD_REQUEST

    # Authenticate the request
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    try:
        Token.query.filter_by(token=hashed_token).first()
    except Exception as e:
        print(e)
        return 'Unauthorized 1', status.HTTP_401_UNAUTHORIZED

    # Get the request body
    # Some sanization happens here
    try:
        requested_topic = request.json['topic']
        requested_actor1 = request.json['actor1']
        requested_actor2 = request.json['actor2']
        requested_length = request.json['length']
    except KeyError as e:
        print(e)
        return 'Bad request 2', status.HTTP_400_BAD_REQUEST

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
        return 'Internal error 1', status.HTTP_500_INTERNAL_SERVER_ERROR

    # Parse the actors file to get the voice and filter to use
    try:
        with open(actors_file, 'r') as file:
            actors = yaml.safe_load(file)
            requested_actor1 = actors[requested_actor1]
            requested_actor2 = actors[requested_actor2]
            file.close()
    except Exception as e:
        print(e)
        return 'Internal error 2', status.HTTP_500_INTERNAL_SERVER_ERROR

    # Initialize the actors
    # Since we're using the OpenAI chat completion API, each actor has their own conversation history where they are the assistant and the other is the user
    message_history_actor1 = []
    message_history_actor2 = []
    actor1_preprompt = requested_actor1['preprompt'] + 'Ton interlocuteur est ' + requested_actor2['name'] + '.'
    actor2_preprompt = requested_actor2['preprompt'] + 'Ton interlocuteur est ' + requested_actor1['name'] + '.'
    message_history_actor1.append({'role': 'system', 'content': actor1_preprompt})
    message_history_actor2.append({'role': 'system', 'content': actor2_preprompt})

    # Initiate the conversation with the requested topic
    messages = []
    messages.append(
        {
            'actor': requested_actor1['name'],
            'text': requested_topic
        }
    )

    # Actor 1 initiated the conversation with the requested topic. Actor 2 has to know about it
    message_history_actor2.append({'role': 'user', 'content': requested_topic})

    for i in range(requested_length):
        # Actor 2 speaks first because actor 1 initiated the conversation with the requested topic
        completion_actor2 = get_chat_completion(requested_actor2, message_history_actor2)
        if completion_actor2 == 'Internal error 3':
            return 'Internal error', status.HTTP_500_INTERNAL_SERVER_ERROR

        # Append actor 2's chat history with their response
        message_history_actor2.append({'role': 'assistant', 'content': completion_actor2})

        # Append actor 1's chat history with actor 2's response
        message_history_actor1.append({'role': 'user', 'content': completion_actor2})

        # Actor 1 now responds
        completion_actor1 = get_chat_completion(requested_actor1, message_history_actor1)
        if completion_actor1 == 'Internal error 4':
            return 'Internal error', status.HTTP_500_INTERNAL_SERVER_ERROR

        # Append actor 1's chat history with their response
        message_history_actor1.append({'role': 'assistant', 'content': completion_actor1})

        # Append actor 2's chat history with actor 1's response
        message_history_actor2.append({'role': 'user', 'content': completion_actor1})

        # We're done with this iteration, now let's append the global message history
        messages.append(
            {
                'actor': requested_actor2['name'],
                'text': completion_actor2
            }
        )

        # And with actor 1's response
        messages.append(
            {
                'actor': requested_actor1['name'],
                'text': completion_actor1
            }
        )

    # Generate a random UUID for the conversation
    conversation_uuid = str(uuid.uuid1())

    # Log the request
    with open('/var/log/conversation-manager/requests.log', 'a') as logfile:
        logfile.write('report:\n')
        logfile.write('  utc: ' + str(datetime.now(UTC)) + '\n')
        logfile.write('  host: ' + request.remote_addr + '\n')
        logfile.write('  token-hash: ' + hashed_token + '\n')
        logfile.write('  user-agent: ' + request.headers.get('User-Agent') + '\n')
        logfile.write('  uuid: ' + conversation_uuid + '\n')
        logfile.write('  topic: ' + str(base64.b64encode(bytes(requested_topic.encode('utf-8')))) + '\n')
        logfile.write('  actor1: ' + requested_actor1 + '\n')
        logfile.write('  actor2: ' + requested_actor2 + '\n')
        logfile.write('  length: ' + requested_length + '\n')
        logfile.close()

    # Return the conversation as json
    return messages, status.HTTP_200_OK
