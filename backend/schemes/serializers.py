"""schemes/serializers.py"""
from rest_framework import serializers
from .models import Scheme


class SchemeListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing — no full description"""
    required_documents = serializers.SerializerMethodField()

    class Meta:
        model  = Scheme
        fields = [
            'id', 'name', 'ministry', 'category', 'icon',
            'eligible_category', 'eligible_occupation', 'eligible_gender',
            'eligible_state', 'min_income', 'max_income',
            'benefit_amount', 'benefit_period',
            'last_date', 'status', 'description',
            'required_documents', 'official_url',
        ]

    def get_required_documents(self, obj):
        return obj.get_documents_list()


class SchemeDetailSerializer(SchemeListSerializer):
    """Full detail including all fields"""
    class Meta(SchemeListSerializer.Meta):
        fields = SchemeListSerializer.Meta.fields + ['created_at', 'updated_at']


class SchemeCreateSerializer(serializers.ModelSerializer):
    """Used by admin to create/update schemes"""
    required_documents = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )

    class Meta:
        model  = Scheme
        fields = '__all__'

    def create(self, validated_data):
        docs = validated_data.pop('required_documents', [])
        scheme = Scheme(**validated_data)
        scheme.set_documents_list(docs)
        scheme.save()
        return scheme

    def update(self, instance, validated_data):
        docs = validated_data.pop('required_documents', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if docs is not None:
            instance.set_documents_list(docs)
        instance.save()
        return instance
