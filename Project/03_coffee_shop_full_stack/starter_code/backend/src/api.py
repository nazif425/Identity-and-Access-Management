import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks", methods=['GET'])
def get_drinks():
    drink_records = Drink.query.all()
    if not drink_records:
        abort(404)
    
    return jsonify({
        "drinks": [drink.short() for drink in drink_records],
        "success": True
    })

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks-detail", methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_detail(payload, *args, **kwargs):
    drink_records = Drink.query.all()
    if not drink_records:
        abort(404)
    
    return jsonify({
        "drinks": [drink.long() for drink in drink_records],
        "success": True
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks", methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt_payload, *args, **kwargs):
    
    # validate post data
    if not request.get_json().get('title', None) \
        or not request.get_json().get('recipe', None):
        abort(400)
    

    # validate drink title. Abort if title already exists
    if Drink.query.filter(Drink.title==request.get_json()['title']).count() > 0:
        abort(400)
    
    # insert new drink to database
    try:
        drink = Drink(
            title=request.get_json()['title'],
            recipe=json.dumps(request.get_json()['recipe']))
        drink.insert()
    except:
        abort(500)

    return jsonify({
        'drinks': [drink.long()], 
        'success': True
    })

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks/<int:id>", methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink_detail(jwt_payload, id, *args, **kwargs):
        
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)
    
    # update drink record in the database
    if 'title' in request.get_json():
        drink.title = request.get_json()['title']
    if 'recipe' in request.get_json():
        drink.recipe = json.dumps(request.get_json()['recipe'])
    
    try:
        drink.update()
    except:
        abort(422)
    
    return jsonify({
        'drinks': [drink.long()],
        'success': True
    })

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks/<int:id>", methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt_payload, id, *args, **kwargs):
    
    # fetch drink record from database
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)
    
    # perform delete operation
    try:
        drink.delete() 
    except:
        abort(422)
    
    return jsonify({
        'delete': id,
        'success': True
    })

# Error Handling
'''
Example error handling for unprocessable entity
'''

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "message": "unprocessable",
        "success": False,
        "error": 422
    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404
'''

@app.errorhandler(400)
def handle_invalid_request(error):
    return jsonify({
        "message": "Invalid request",
        "success": False,
        "error": 400
    }), 400

@app.errorhandler(500)
def handle_server_error(error):
    return jsonify({
        "message": "Server error",
        "success": False, 
        "error": 500
    }), 500

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''

@app.errorhandler(404)
def handle_resource_not_found(error):
    return jsonify({
        "message": "resource not found",
        "success": False, 
        "error": 404
    }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def handle_auth_error(error):
    return jsonify({
        "description": error.error['description'],
        "message": error.error["code"]
    }), error.status_code
