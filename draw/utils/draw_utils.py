from events.models import DisciplineMember
from draw.models import Match, Bracket, ScoringEntry, ScoringRound
import math
from registration.utils.utils import next_power_of_2


def generate_liga_draw(disciplines: list, config: dict) -> None:
    """_summary_

    Args:
        disciplines (list): _description_
        config (dict): _description_

    Returns:
        _type_: _description_
    """
    min = int(config["minMembersPerGroup"])
    min = int(config["maxMembersPerGroup"])
    split_clubs = config["splitClubs"]
    split_favourites = config["splitFavourites"]
    return "OLA"


def generate_torneio_draw(event, disciplines: list, config: dict = None, misto: bool = False) -> bool:
    """_summary_

    Args:
        event (_type_): _description_
        disciplines (list): _description_
        config (dict, optional): _description_. Defaults to None.

    Returns:
        bool: _description_
    """
    split_clubs = config["splitClubs"]
    split_favourites = config["splitFavourites"]
    finals_size = config.get("finalsSize", None)

    # if coming from misto draw generate, checks if finals_size is set
    will_go_to_scoring = False
    if misto and finals_size:
        will_go_to_scoring = True

    for discipline in disciplines:
            
        for category in discipline.categories.all():
            
            # Retrieves all registrations for the current category
            category_registrations = DisciplineMember.objects.filter(
                category=category,
                discipline=discipline
            ).order_by("id")

            registrations = list(category_registrations)
            total_players = len(registrations)

            # Categories with less than 2 registration will not take place, so proceed to the next category
            if len(registrations) < 2:
                continue

            new_bracket = Bracket.objects.create(
                                                name=f'{discipline.name} {category.name} {category.gender}',
                                                category=category,
                                                discipline=discipline,
                                                event=event,
                                                draw_type="Misto" if misto else "Torneio/Finais"
                                                )

            bracket_size = next_power_of_2(total_players)
            total_rounds = int(math.log2(bracket_size))

            if will_go_to_scoring:
                elimination_rounds = total_rounds - int(math.log2(int(finals_size)))
            else:
                elimination_rounds = total_rounds

            for round_number in range(elimination_rounds):
                round_label = total_rounds - 1 - round_number
                matches_in_round = bracket_size // (2 ** (round_number + 1))

                for match_number in range(1, matches_in_round + 1):
                    Match.objects.create(
                        bracket=new_bracket,
                        round_number=round_label,
                        match_number=match_number
                    )
            
            if will_go_to_scoring:
                scoring_round = ScoringRound.objects.create(
                    bracket=new_bracket,
                    round_number=0,
                    is_final=True
                )

                if total_players > int(finals_size):
                    # Link the last elimination round's matches to feed into the scoring round
                    last_elim_round_label = total_rounds - elimination_rounds
                    last_elim_matches = Match.objects.filter(
                        bracket=new_bracket,
                        round_number=last_elim_round_label
                    )
                    for match in last_elim_matches:
                        match.feeds_into_scoring = scoring_round
                        match.save()

                    for i in range(int(finals_size)):
                        ScoringEntry.objects.create(scoring_round=scoring_round, entry_number=i)

                else:
                    for reg in registrations:
                        ScoringEntry.objects.create(scoring_round=scoring_round, person=reg.person)
        
            else:
                # Create 3rd place match only if there are semi-finals (4+ players)
                third_place_match = None
                if total_players >= 4:
                    third_place_match = Match.objects.create(
                        bracket=new_bracket,
                        round_number=0,
                        match_number=2,
                        is_third_place=True
                    )

                    # Link semi-final matches to the 3rd place match so losers are advanced there
                    semi_final_round = 1 
                    semi_final_matches = Match.objects.filter(
                        bracket=new_bracket,
                        round_number=semi_final_round
                    )
                    for semi in semi_final_matches:
                        semi.loser_goes_to = third_place_match
                        semi.save()

            first_round_matches = Match.objects.filter(
                bracket=new_bracket,
                round_number=total_rounds - 1  # first round is the highest number
            ).order_by("match_number")

            reg_index = 0

            for match in first_round_matches:
                if reg_index < total_players:
                    match.contender_1 = registrations[reg_index].person
                    reg_index += 1

                if reg_index < total_players:
                    match.contender_2 = registrations[reg_index].person
                    reg_index += 1

                match.save()

            for match in first_round_matches:
                if match.contender_1 and not match.contender_2:
                    match.winner = match.contender_1
                    match.save()
                    match.advance_winner()
                    match.advance_loser()

                elif match.contender_2 and not match.contender_1:
                    match.winner = match.contender_2
                    match.save()
                    match.advance_winner()
                    match.advance_loser()
        
    return True