from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from crm1.infrastructure.internal import JwtClient
from accounts.models import User


def jwt_required(view_func):
    """
    This is the decorator that checks if a valid JWT is available in the request headers
    :param view_func:
    :return:
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        authorization = request.headers.get("Authorization") or request.headers.get('HTTP_AUTHORIZATION')

        if authorization is None:
            return Response(
                {
                    "message": "Unauthenticated Error",
                },
                status=status.HTTP_401_UNAUTHORIZED)

        token = authorization.replace("Bearer ", "")

        decoded_jwt = JwtClient.decode(token)

        if decoded_jwt is None:
            return Response({
                "message": "Unauthenticated Error",
                }, status=status.HTTP_401_UNAUTHORIZED)

        user_id = decoded_jwt.get('id')

        if user_id is None:
            return Response(
                {
                    "message": "Unauthenticated Error",
                }, 
                status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=user_id)
            request.user = user
            response = view_func(request, *args, **kwargs)
            return response

        except User.DoesNotExist:
            return Response(
            {
                "message": "Unauthenticated Error",
            }, 
            status=status.HTTP_401_UNAUTHORIZED)

    return wrapper