from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match

@receiver(post_save, sender=Match)
def handle_match_absence(sender, instance, **kwargs):
    match = instance

    if match.bracket.discipline.is_team:
        if not match.team_contender_1_present and match.team_contender_2 and match.team_contender_2_present:
            if not match.team_winner:
                match.winner = match.team_contender_2
                # Disconnect signal temporarily to avoid recursion
                post_save.disconnect(handle_match_absence, sender=Match)
                match.save()
                post_save.connect(handle_match_absence, sender=Match)
                match.advance_winner()
                match.advance_loser()

        elif not match.team_contender_2_present and match.team_contender_1 and match.team_contender_1_present:
            if not match.team_winner:
                match.winner = match.team_contender_1
                post_save.disconnect(handle_match_absence, sender=Match)
                match.save()
                post_save.connect(handle_match_absence, sender=Match)
                match.advance_winner()
                match.advance_loser()

    else:
        if not match.contender_1_present and match.contender_2 and match.contender_2_present:
            if not match.winner:
                match.winner = match.contender_2
                # Disconnect signal temporarily to avoid recursion
                post_save.disconnect(handle_match_absence, sender=Match)
                match.save()
                post_save.connect(handle_match_absence, sender=Match)
                match.advance_winner()
                match.advance_loser()

        elif not match.contender_2_present and match.contender_1 and match.contender_1_present:
            if not match.winner:
                match.winner = match.contender_1
                post_save.disconnect(handle_match_absence, sender=Match)
                match.save()
                post_save.connect(handle_match_absence, sender=Match)
                match.advance_winner()
                match.advance_loser()