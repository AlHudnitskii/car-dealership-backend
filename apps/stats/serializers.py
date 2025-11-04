from rest_framework import serializers


class DealershipStatsSerializer(serializers.Serializer):
    """Serializer for dealership statistics"""

    dealership_id = serializers.IntegerField()
    dealership_name = serializers.CharField()
    total_cars_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_purchases = serializers.IntegerField()
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    unique_customers = serializers.IntegerField()
    current_inventory_count = serializers.IntegerField()
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_promotions = serializers.IntegerField()


class CustomerStatsSerializer(serializers.Serializer):
    """Serializer for customer statistics"""

    customer_id = serializers.IntegerField()
    customer_email = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_purchases = serializers.IntegerField()
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_offers = serializers.IntegerField()
    rejected_offers = serializers.IntegerField()
    favorite_car_model = serializers.CharField(required=False, allow_null=True)


class SupplierStatsSerializer(serializers.Serializer):
    """Serializer for supplier statistics"""

    supplier_id = serializers.IntegerField()
    supplier_name = serializers.CharField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    ctive_offers = serializers.IntegerField()
    total_stock = serializers.IntegerField()
    partner_dealerships = serializers.IntegerField()
    active_promotions = serializers.IntegerField()


class GlobalStatsSerializer(serializers.Serializer):
    """Serializer for global system statistics"""

    total_dealerships = serializers.IntegerField()
    total_suppliers = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    total_transaction_volume = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_cars_sold = serializers.IntegerField()
    active_offers = serializers.IntegerField()
    most_popular_car_model = serializers.CharField(required=False, allow_null=True)
    most_popular_manufacturer = serializers.CharField(required=False, allow_null=True)
