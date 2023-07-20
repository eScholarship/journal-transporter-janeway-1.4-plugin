from django.test import TestCase

from .serializers import UserSerializer
from .views import UserViewSet
from core.models import Account, Interest

class UserSerializerTest(TestCase):
    """
    Test UserSerializer
    """

    def test_user_serializer_valid_user(self):
        valid_user_data = {"username": "valid_user", "email": "validuser@example.com", "first_name": "Imma", "last_name": "Perfect"}
        serializer = UserSerializer(data=valid_user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(user.email, valid_user_data['email'])
        self.assertEqual(user.first_name, valid_user_data['first_name'])
        self.assertEqual(user.last_name, valid_user_data['last_name'])

    def test_user_serializer_invalid_user_missing_email(self):
        user_data = {"username": "invalid_user", "email": "", "first_name": "Sam", "last_name": "Sam"}
        serializer = UserSerializer(data=user_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_add_interests(self):
        data = {"username": "valid_user", 
                "email": "validuser@example.com", 
                "first_name": "Imma", 
                "last_name": "Perfect", 
                "interests": "Cats, Dogs"}
        serializer = UserSerializer(data=data)
        serializer.context["view"] = UserViewSet(kwargs={})
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Interest.objects.count(), 2)
        self.assertEqual(user.interest.count(), 2)        

    # For some reason first and last name are not required by the serializer
    # but if they are not filled out serializer.save will return None
    # DRF does NOT like this. We should probably just make them required but
    # I'm just not sure why the code was written this way in the first place.
    def test_user_serializer_invalid_user_missing_first_name(self):
        user_data = {"username": "invalid_user", "email": "invaliduser@example.com", "first_name": None, "last_name": "Sam"}
        serializer = UserSerializer(data=user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertTrue(serializer.is_valid())

    def test_user_serializer_invalid_user_missing_last_name(self):
        user_data = {"username": "invalid_user", "email": "invaliduser@example.com", "first_name": "Sam", "last_name": None}
        serializer = UserSerializer(data=user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertTrue(serializer.is_valid())
