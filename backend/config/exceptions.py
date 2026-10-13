from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, dict) and "detail" in data:
        response.data = {"message": str(data["detail"]), "errors": None}
    else:
        errors = data if isinstance(data, dict) else {"non_field_errors": data}
        response.data = {"message": "Please fix the highlighted fields.", "errors": errors}
    return response
