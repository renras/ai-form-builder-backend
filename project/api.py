from openai import OpenAI
from flask import request, jsonify, Blueprint
import os
from project.models import User
from project import db
import json
from project.utils import handle_api_exception

api = Blueprint('api', __name__)

OPEN_AI_ENABLED = os.getenv('OPEN_AI_ENABLED', 'false') == 'true'

#
# main endpoints
#

@api.route("/api/v1/prompt", methods=["POST"])
def prompt():
  try:
    if not OPEN_AI_ENABLED:
      return {
        'data': OPEN_AI_DUMMY_RESPONSE
      }
    
    text = request.json.get('text', None)

    if not text:
      return {
        'message': 'Missing required parameter: text'
      }, 400

    return jsonify({
      'data': json.loads(get_completion(create_prompt(text)))
    })
  except Exception as e:
    return handle_api_exception(e)
 
    
client = OpenAI()
    
# give instructions to llm on how to complete the task based on the text provided
def create_prompt(text):
  prompt = f"""
    You will be provided with text delimited by triple backticks.
    This text will describe a form that you need to help create.
    Your task is to provide an array of objects in JSON format.
    - label: The label of the field.
    - name: The name attribute of the field.
    - type: The type of the input field (e.g., text, email, password).
    - validations: An array of validation rules for the field.

    Validations are optional. If validations are provided, you must provide an array of validation objects. And it must contain the following properties:
    - type: The type of validation (e.g., required, minLength, maxLength).
    - value: The value of the validation (e.g., true, 10, 100).
    - message: The error message to display if the validation fails.

    Supported validations are:
    - required: The field is required.
    - minLength: The minimum length of the field.
    - maxLength: The maximum length of the field.
    - min: The minimum value of the field.
    - max: The maximum value of the field.
    - pattern: The pattern the field must match.

    ```{text}```
    """
  
  return prompt

# returns the response from llm based on the prompt provided
def get_completion(prompt, model="gpt-3.5-turbo"):
  messages = [{"role": "user", "content": prompt}]
  response =  client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=0
  )
  
  return response.choices[0].message.content

# dummy response for when openai is disabled
OPEN_AI_DUMMY_RESPONSE = [
        {
            "label": "Username",
            "name": "username",
            "type": "text",
            "validations": [
                {
                    "message": "Username is required",
                    "type": "required",
                    "value": True
                },
                {
                    "message": "Username must be at least 6 characters long",
                    "type": "minLength",
                    "value": 6
                },
                {
                    "message": "Username cannot exceed 20 characters",
                    "type": "maxLength",
                    "value": 20
                }
            ]
        },
        {
            "label": "Email",
            "name": "email",
            "type": "email",
            "validations": [
                {
                    "message": "Email is required",
                    "type": "required",
                    "value": True
                },
                {
                    "message": "Invalid email format",
                    "type": "pattern",
                    "value": "^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
                }
            ]
        },
        {
            "label": "Password",
            "name": "password",
            "type": "password",
            "validations": [
                {
                    "message": "Password is required",
                    "type": "required",
                    "value": True
                },
                {
                    "message": "Password must be at least 8 characters long",
                    "type": "minLength",
                    "value": 8
                }
            ]
        },
        {
            "label": "Confirm Password",
            "name": "confirmPassword",
            "type": "password",
            "validations": [
                {
                    "message": "Confirm Password is required",
                    "type": "required",
                    "value": True
                },
                {
                    "message": "Confirm Password must be at least 8 characters long",
                    "type": "minLength",
                    "value": 8
                }
            ]
        }
    ]

#
# user endpoints
#

@api.route("/api/v1/users", methods=["GET"])
def get_users():
  try:
    users = User.query.all()

    return jsonify({
      'data': [{
        'id': user.id,
        'username': user.username,
        'email': user.email
      } for user in users]
    })
  except Exception as e:
    handle_api_exception(e)

@api.route("/api/v1/user", methods=["POST"])
def create_user():
  try:
    username = request.json.get('username', None)
    email = request.json.get('email', None)
    
    if not username:
      return jsonify({
        'message': 'Missing required parameter: username'
      }), 400
    
    if not email:
      return jsonify({
        'message': 'Missing required parameter: email'
      }), 400
    
    user = User(username=username, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({
      'data': {
        'id': user.id,
        'username': user.username,
        'email': user.email
      }
    })
  except Exception as e:
    handle_api_exception(e)