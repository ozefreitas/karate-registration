from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from django.utils import timezone

from registration.models import MonthlyPersonPaymentConfig, MonthlyPersonPayment, Person
from core.models import MonthlyPaymentPlan
from core.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = "Creates yearly subscriptions for all clubs."

    def handle(self, *args, **kwargs):
        clubs = User.objects.filter(
            role__in=["subed_club"],
            clubsettings__billing_day=today
        )

        created, deleted = 0, 0

        for club in clubs:
            default_plan, _ = MonthlyPaymentPlan.objects.get_or_create(
                club_user=club,
                is_default=True,
                defaults={"name": "Default", "amount": 10}
            )
            members = Person.objects.filter(club=club, quotes_legible=True)

            for member in members:
                
                # config is only created for one type of member
                member_base_plan, _ = MonthlyPersonPaymentConfig.objects.get_or_create(
                    member=member,
                    defaults={"base_plan": default_plan}
                )

                final_amount = None
                if not member_base_plan.is_custom_active:
                    final_amount = member_base_plan.base_plan.amount
                else:
                    final_amount=member_base_plan.custom_amount

                # payment is only created for one type of member
                today = timezone.now()
                obj, was_created = MonthlyPersonPayment.objects.get_or_create(
                    person=member,
                    year=today.year,
                    month=today.month,
                    defaults={"amount": final_amount}
                )
                
                month_to_check, year_to_check = None, None
                if today.month == 1:
                    month_to_check = 12
                    year_to_check = today.year - 1
                else: 
                    month_to_check = today.month - 1
                    year_to_check = today.year

                if MonthlyPersonPayment.objects.filter(
                    person=member,
                    year=year_to_check, 
                    month=month_to_check
                    ).exists():
                    Notification.objects.create(
                        notification=f'O Membro {member.first_name} {member.last_name} falhou o pagamento do último mês.',
                        can_remove=True,
                        type="payment_overdue",
                        club_user=club,
                        payment_object="quotes",
                        target_person=member
                        )

                if was_created:
                    created += 1
                
                try:
                    # will delete the payment object one prior, of exists
                    obj = MonthlyPersonPayment.objects.get(
                            person=member, 
                            year=today.year - 1, 
                            month=today.month
                            )
                    obj.delete()
                    deleted += 1
                except MonthlyPersonPayment.DoesNotExist:
                    continue

        if created > 0:
            self.stdout.write(
                self.style.SUCCESS(f"{created} subscriptions created for {len(clubs)} Clubs.")
            )
        else:
            self.stdout.write(
                self.style.WARNING("No payment added")
            )

        if deleted > 0:
            self.stdout.write(
                self.style.SUCCESS(f"{deleted} subscriptions deleted.")
            )
