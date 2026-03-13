from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


@extend_schema(
    tags=['auth'],
    summary='Register a new user',
    description='Creates a new user account and immediately logs the user in. '
                'A session cookie and CSRF token are set in the response.',
    request=RegisterSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiResponse(description='Validation error (duplicate username or weak password)'),
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['auth'],
    summary='Log in',
    description='Authenticates with username and password. Sets a session cookie on success.',
    request=LoginSerializer,
    responses={
        200: UserSerializer,
        400: OpenApiResponse(description='Invalid credentials'),
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        return Response(UserSerializer(user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['auth'],
    summary='Log out',
    description='Ends the current session.',
    request=None,
    responses={
        200: OpenApiResponse(description='{"detail": "Logged out."}'),
        403: OpenApiResponse(description='Not authenticated'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'detail': 'Logged out.'})


@extend_schema(
    tags=['auth'],
    summary='Current user profile',
    description='Returns the authenticated user\'s profile.',
    responses={
        200: UserSerializer,
        403: OpenApiResponse(description='Not authenticated'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@extend_schema(
    tags=['auth'],
    summary='Obtain API token',
    description=(
        'Returns (or creates) a long-lived API token for the user. '
        'Use this token in the `Authorization: Token <token>` header for all '
        'subsequent requests — no CSRF needed. '
        'This is the recommended way to authenticate when using the Swagger UI.'
    ),
    request=LoginSerializer,
    responses={
        200: inline_serializer(
            'TokenResponse',
            fields={
                'token': drf_serializers.CharField(),
                'user': UserSerializer(),
            },
        ),
        400: OpenApiResponse(description='Invalid credentials'),
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_token(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UserSerializer(user).data})
