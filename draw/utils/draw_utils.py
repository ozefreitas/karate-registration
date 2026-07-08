from events.models import DisciplineMember, DisciplineTeam, Discipline
from draw.models import Match, Bracket, ScoringEntry, ScoringRound
import math
from registration.utils.utils import next_power_of_2
import random


def seed_registrations_by_club(registrations: list, discipline_type: str):
    # Group by club
    club_groups = {}
    for reg in registrations:
        if discipline_type == "team":
            club_id = reg.team.club.id
        else:
            club_id = reg.person.club.id
        if club_id not in club_groups:
            club_groups[club_id] = []
        club_groups[club_id].append(reg)

    # Shuffle within each club group
    for group in club_groups.values():
        random.shuffle(group)

    # Sort groups by size descending (largest club first)
    groups = sorted(club_groups.values(), key=len, reverse=True)

    # If only 1 club, just return shuffled
    if len(groups) == 1:
        return groups[0]

    # Snake distribution into bracket slots
    slots = [None] * len(registrations)
    indices = list(range(len(registrations)))
    direction = 1
    idx_pos = 0

    for group in groups:
        for reg in group:
            slots[indices[idx_pos]] = reg
            idx_pos += direction
            if idx_pos >= len(indices):
                direction = -1
                idx_pos = len(indices) - 1
            elif idx_pos < 0:
                direction = 1
                idx_pos = 0

    return slots


def generate_liga_draw(config: dict) -> None:
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


def generate_torneio_draw(event: str, config: dict = None, misto: bool = False) -> bool:
    """_summary_

    Args:
        event (_type_): _description_
        config (dict, optional): _description_. Defaults to None
        misto (bool, optional): If misto, starts by checking the finals size, only to create round robins until there. Defaults to False

    Returns:
        bool: _description_
    """
    split_clubs = config["splitClubs"]
    split_favourites = config["splitFavourites"]
    finals_size = config.get("finalsSize", None)
    discipline = Discipline.objects.filter(id=config["disciplineId"]).first()

    # if coming from misto draw generate, checks if finals_size is set
    will_go_to_scoring = False
    if misto and finals_size:
        will_go_to_scoring = True
            
    for category in discipline.categories.all():
        
        if discipline.is_team:
            # Retrieves all teams for the current category
            category_registrations = DisciplineTeam.objects.filter(
                team__category=category,
                discipline=discipline,
            ).order_by("id")

        else:
            # Retrieves all registrations for the current category
            category_registrations = DisciplineMember.objects.filter(
                category=category,
                discipline=discipline
            ).order_by("id")

        if split_clubs:
            registrations = seed_registrations_by_club(list(category_registrations), "team" if discipline.is_team else "indiv")
        else:
            registrations = list(category_registrations)
        total_players = len(registrations)

        # Categories with less than 2 registration will not take place, so proceed to the next category
        if len(registrations) < 2:
            continue
        
        bracket_name = f'{discipline.name} {category.name} {category.gender}'
        if category.min_weight is not None:
            bracket_name += f' + {category.min_weight} Kg'
        elif category.max_weight is not None:
            bracket_name += f' - {category.max_weight} Kg'

        new_bracket = Bracket.objects.create(
                                            name=bracket_name,
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
                for i, reg in enumerate(registrations):
                    if discipline.is_team:
                        ScoringEntry.objects.create(scoring_round=scoring_round, team=reg.team, entry_number=i)
                    else:
                        ScoringEntry.objects.create(scoring_round=scoring_round, person=reg.person, entry_number=i)
    
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

        real_matches_count = total_players - (bracket_size // 2)
        total_matches = len(first_round_matches)

        # Calculate evenly spread positions for real matches
        if real_matches_count > 0:
            step = total_matches / real_matches_count
            real_positions = set(int((i + 0.5) * step) for i in range(real_matches_count))
        else:
            real_positions = set()

        reg_index = 0

        for i, match in enumerate(first_round_matches):
            if i in real_positions:
                # Real match — 2 contenders
                if discipline.is_team:
                    match.team_contender_1 = registrations[reg_index].team
                else:
                    match.contender_1 = registrations[reg_index].person
                reg_index += 1
                if discipline.is_team:
                    match.team_contender_2 = registrations[reg_index].team
                else:
                    match.contender_2 = registrations[reg_index].person
                reg_index += 1
            else:
                # BYE match — 1 contender
                if discipline.is_team:
                    match.team_contender_1 = registrations[reg_index].team
                else:
                    match.contender_1 = registrations[reg_index].person
                reg_index += 1

            match.save()

        for match in first_round_matches:
            if discipline.is_team:
                if match.team_contender_1 and not match.team_contender_2:
                    match.team_winner = match.team_contender_1
                elif match.team_contender_2 and not match.team_contender_1:
                    match.team_winner = match.team_contender_2
                match.save()
                match.advance_winner()
                match.advance_loser()
            else:
                if match.contender_1 and not match.contender_2:
                    match.winner = match.contender_1
                elif match.contender_2 and not match.contender_1:
                    match.winner = match.contender_2
                match.save()
                match.advance_winner()
                match.advance_loser()
    
    return True