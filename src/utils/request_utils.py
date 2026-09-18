import uuid


def get_or_create_request_id(request):
    """
    Return the request ID from the request header.

    If the client does not provide one,
    generate a new UUID.
    """

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    return request_id