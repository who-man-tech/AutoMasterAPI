from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from masters.models import Master
from masters.serializers import MasterSerializer
from registers.exceptions import MasterIsBusy, NonWorkingTime, RegisterAlreadyStarted

from registers.models import Register
from registers.services import RegisterService


class RegisterSerializer(serializers.ModelSerializer):
    """
    Запись можно создать или обновить, если:
    - Указанная дата входит в рабочее время и имеет запас на работу до конца рабочего дня.
    - Указанная дата входит в рабочие дни.
    - Указанный мастер не имеет записи на указанное время и имеет запас на работу до следующей записи.
    """

    master = MasterSerializer(read_only=True)
    start_at = serializers.DateTimeField(required=True)
    master_id = serializers.IntegerField(required=True)

    class Meta:
        model = Register
        fields = [
            'pk',
            'start_at',
            'end_at',
            'master',
            'created_at',
            'master_id',
        ]
        read_only_fields = [
            'pk',
            'end_at',
            'master',
            'created_at',
            'master_id',
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start_at: datetime = attrs['start_at']
        master_pk = attrs['master_id']

        if not RegisterService.check_is_working_time(start_at):
            raise NonWorkingTime()

        master = Master.objects.get(pk=master_pk)

        attrs['master'] = master
        attrs['user'] = self.context['request'].user
        return attrs

    def create(self, validated_data):
        start_at = validated_data['start_at']
        master = validated_data['master']

        if Register.objects.filter(
            master=master,
            start_at__range=[start_at, start_at + timedelta(hours=settings.REGISTER_LIFETIME)],
            end_at__gte=start_at
        ).exists():
            raise MasterIsBusy()

        # TODO: Проверить!
        # if Register.objects.filter(
        #         master=master,
        #         start_at__lte=start_at,
        #         end_at__gte=start_at
        # ).exists():
        #     raise UnavailableTime()

        return super().create(validated_data)

    def update(self, instance: Register, validated_data):
        start_at = validated_data['start_at']
        master = validated_data['master']
        user = validated_data['user']

        if Register.objects.filter(
                master=master,
                start_at__range=[start_at, start_at + timedelta(hours=settings.REGISTER_LIFETIME)],
                end_at__gte=start_at
        ).exclude(user=user).exists():
            raise MasterIsBusy()

        if instance.start_at <= timezone.now():
            raise RegisterAlreadyStarted()

        # TODO: Проверить!
        # if Register.objects.filter(
        #         master=master,
        #         start_at__lte=start_at,
        #         end_at__gte=start_at
        # ).exists():
        #     raise UnavailableTime()

        return super().update(instance, validated_data)
