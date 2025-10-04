from rest_framework import serializers


class PredictAQIQuerySerializer(serializers.Serializer):
	# Coordinates or city
	lat = serializers.FloatField(required=False)
	lon = serializers.FloatField(required=False)
	q = serializers.CharField(required=False)
	city = serializers.CharField(required=False)
	# Time period
	start = serializers.CharField(required=False)
	end = serializers.CharField(required=False)
	hours = serializers.IntegerField(required=False, min_value=1)

	def validate(self, attrs):
		# Ensure at least lat/lon or city/q provided (we allow fallback default though)
		# Keep permissive: if nothing provided, view will fallback to defaults
		lat = attrs.get('lat')
		lon = attrs.get('lon')
		if (lat is not None and lon is None) or (lat is None and lon is not None):
			raise serializers.ValidationError('Both lat and lon must be provided together')
		return attrs


class PredictAQIItemSerializer(serializers.Serializer):
	timestamp_utc = serializers.IntegerField(allow_null=True)
	components = serializers.DictField(child=serializers.FloatField(allow_null=True), allow_null=True)
	openweather_aqi = serializers.IntegerField(allow_null=True)
	predicted_aqi = serializers.FloatField(allow_null=True)
	predicted_components = serializers.DictField(child=serializers.FloatField(allow_null=True), required=False)
	prediction_raw = serializers.ListField(child=serializers.FloatField(), required=False)


class PredictAQIResponseSerializer(serializers.Serializer):
	message = serializers.CharField()
	coordinates = serializers.DictField()
	location = serializers.DictField()
	time_range = serializers.DictField()
	feature_order = serializers.ListField(child=serializers.CharField())
	model = serializers.DictField()
	count = serializers.IntegerField()
	results = PredictAQIItemSerializer(many=True)
