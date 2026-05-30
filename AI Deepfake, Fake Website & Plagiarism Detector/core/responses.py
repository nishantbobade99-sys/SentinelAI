from flask import jsonify

def success_response(data=None, message="Success"):
    response = {"success": True, "message": message}
    if data:
        response.update(data)
    return jsonify(response), 200

def error_response(error_code, message, status_code=400):
    return jsonify({
        "success": False,
        "error_code": error_code,
        "message": message
    }), status_code
