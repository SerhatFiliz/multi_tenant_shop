from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0009_order_currency_order_stripe_payment_intent_id_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("sentiment", models.CharField(default="Neutral", max_length=40)),
                ("is_high_priority", models.BooleanField(default=False)),
                ("receiver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="received_messages", to=settings.AUTH_USER_MODEL)),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_messages", to=settings.AUTH_USER_MODEL)),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="store.tenant")),
            ],
            options={
                "ordering": ["-timestamp"],
                "indexes": [
                    models.Index(fields=["store", "timestamp"], name="store_messa_store_i_98a8a7_idx"),
                    models.Index(fields=["receiver", "is_read"], name="store_messa_receive_7aa603_idx"),
                    models.Index(fields=["is_high_priority"], name="store_messa_is_high_9e2a75_idx"),
                ],
            },
        ),
    ]
