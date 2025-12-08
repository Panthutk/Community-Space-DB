from rest_framework import serializers
from .models import Item, User
from .utils.calling_codes import CALLING_CODES
from .utils.phone_utils import format_phone_number


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):

    #DEVNOTE: for the data that we not exact contain inside database as same as user so we need to add more logic
    #Data get from frontend before merge and format
    country = serializers.ChoiceField(choices=list(CALLING_CODES.keys()), write_only=True)
    phone = serializers.CharField(write_only=True) #NOTE: although we want only digit we still contain in string because the first number can be 0
    #Formatted data ready to send to backend
    phone_number = serializers.CharField(source='phone', read_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password_hash",
            "is_host",
            "is_renter",
            # incoming data
            "country",
            "phone",
            # outgoing data
            "phone_number",
        ]

    def validate(self, data):
        instance = getattr(self, 'instance', None)

        # CREATE or updating phone
        if "phone" in data or instance is None:
            country = data.get("country")
            raw_phone = data.get("phone")

            if raw_phone is None or country is None:
                raise serializers.ValidationError({
                    "phone": "Both country and phone are required when updating the phone number."
                })

            try:
                final_phone = format_phone_number(raw_phone, country)
            except ValueError as e:
                raise serializers.ValidationError({"phone": str(e)})

            data["phone"] = final_phone

        return data


    def create(self, validated_data):
        # When call create remove "country" data out
        validated_data.pop("country", None)
        return super().create(validated_data)