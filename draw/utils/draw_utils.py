from events.models import DisciplineMember, DisciplineTeam, Discipline
from draw.models import Match, Bracket, ScoringEntry, ScoringRound, BracketGroup, BracketGroupMember
import math
from registration.utils.utils import next_power_of_2
import random
from itertools import combinations


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

    # Interleave: pick one from each group in rotation
    result = []
    while any(groups):
        for group in groups:
            if group:
                result.append(group.pop(0))
        groups = [g for g in groups if g]  # remove empty groups

    return result


DEFAULT_MIN_GROUP_SIZE = 3
DEFAULT_MAX_GROUP_SIZE = 6
PREFERRED_GROUP_SIZE = 4

def compute_group_sizes(total: int,
                        min_size: int = DEFAULT_MIN_GROUP_SIZE,
                        max_size: int = DEFAULT_MAX_GROUP_SIZE,
                        preferred: int = PREFERRED_GROUP_SIZE) -> list[int]:
    """
    Returns the size of each group (largest first), or [] if the category does
    not take place (fewer than min_size athletes).

    - total <= max_size  -> a single group.
    - otherwise tries every valid number of groups k, with sizes as balanced as
      possible (differ by at most 1), and picks the k that:
        1) has the fewest groups of min_size (3),
        2) has an average size closest to `preferred` (4),
        3) has the fewest groups.
    """
    if total < min_size:
        return []
    if total <= max_size:
        return [total]

    best_key, best_sizes = None, None
    for k in range(math.ceil(total / max_size), total // min_size + 1):
        base, extra = divmod(total, k)
        sizes = [base + 1] * extra + [base] * (k - extra)
        if min(sizes) < min_size or max(sizes) > max_size:
            continue
        key = (sizes.count(min_size), abs(total / k - preferred), k)
        if best_key is None or key < best_key:
            best_key, best_sizes = key, sizes

    if best_sizes is None:
        raise ValueError(f"Cannot split {total} athletes into groups of {min_size}-{max_size}.")
    return best_sizes


def _club_id(person):
    club = getattr(person, "club", None)
    return club.id if club else None


def distribute_into_groups(registrations: list, sizes: list[int], split_clubs: bool = True) -> list[list]:
    """
    Fills groups with fixed sizes. Club separation has priority, but group sizes
    are never broken: when a club is too big, clashes are minimised, not refused.

    Clubs are placed largest first. Each athlete goes to the open group with the
    fewest athletes of the same club (ties: more free slots, then random).
    Athletes without a club never clash with anyone.
    """
    groups = [[] for _ in sizes]

    if not split_clubs:
        shuffled = random.sample(registrations, len(registrations))
        pos = 0
        for i, size in enumerate(sizes):
            groups[i] = shuffled[pos:pos + size]
            pos += size
        return groups

    by_club, no_club = {}, []
    for reg in registrations:
        cid = _club_id(reg.person)
        if cid is None:
            no_club.append(reg)
        else:
            by_club.setdefault(cid, []).append(reg)

    ordered = []
    for members in sorted(by_club.values(), key=lambda m: (-len(m), random.random())):
        ordered.extend(random.sample(members, len(members)))
    ordered.extend(random.sample(no_club, len(no_club)))

    for reg in ordered:
        cid = _club_id(reg.person)
        open_groups = [i for i, g in enumerate(groups) if len(g) < sizes[i]]

        def cost(i):
            same = sum(1 for r in groups[i] if cid is not None and _club_id(r.person) == cid)
            return (same, -(sizes[i] - len(groups[i])), random.random())

        groups[min(open_groups, key=cost)].append(reg)

    return groups


def _clashes(pairs, club_ids):
    return sum(1 for a, b in pairs if club_ids[a] is not None and club_ids[a] == club_ids[b])


def pick_pairings(persons: list) -> list[tuple[int, int]]:
    """
    Returns pairs of indexes into `persons`.

    - 3 athletes: 5 matches (all pairs + 2 rematches) -> 3, 3 and 4 matches.
      The athlete with 4 matches is chosen to avoid same-club rematches.
    - 4 athletes: all vs all (6 matches, 3 each).
    - 5 athletes: 8 matches, 3 each except one with 4.
    - 6 athletes: 9 matches, everyone plays exactly 3 of the other 5.
    For 5 and 6, all valid sets are enumerated and the ones with the fewest
    same-club matches are kept (random choice between ties).
    Any other size (only possible if min/max change) falls back to all vs all.
    """
    n = len(persons)
    club_ids = [_club_id(p) for p in persons]
    all_pairs = list(combinations(range(n), 2))

    if n == 3:
        options = []
        for extra in range(3):
            rematches = [tuple(sorted((extra, o))) for o in range(3) if o != extra]
            pairs = all_pairs + rematches
            options.append((_clashes(pairs, club_ids), random.random(), pairs))
        return min(options)[2]

    if n in (5, 6):
        target = math.ceil(3 * n / 2)
        best_score, candidates = None, []
        for chosen in combinations(all_pairs, target):
            degree = [0] * n
            for a, b in chosen:
                degree[a] += 1
                degree[b] += 1
            if min(degree) < 3:
                continue
            score = _clashes(chosen, club_ids)
            if best_score is None or score < best_score:
                best_score, candidates = score, [chosen]
            elif score == best_score:
                candidates.append(chosen)
        return list(random.choice(candidates))

    return all_pairs


def order_matches(pairs: list[tuple[int, int]], attempts: int = 500) -> list[tuple[int, int]]:
    """
    Orders the matches so that, as far as possible, nobody plays two matches
    in a row. Random restarts; keeps the ordering with the fewest back-to-back plays.
    (In a group of 4 this cannot be below 2, and in a group of 3 it cannot be 0.)
    """
    best_penalty, best_order = None, None
    for _ in range(attempts):
        order = random.sample(pairs, len(pairs))
        penalty = sum(1 for m1, m2 in zip(order, order[1:]) if set(m1) & set(m2))
        if best_penalty is None or penalty < best_penalty:
            best_penalty, best_order = penalty, order
            if penalty == 0:
                break
    return best_order


def generate_group_draw(event, config: dict) -> bool:
    """
    One Bracket per category, with its groups and all group matches.

    config: disciplineId, splitClubs, minMembersPerGroup (default 3), maxMembersPerGroup (default 6)

    Match numbering inside a bracket:
      round_number = position of the match inside its group (1, 2, 3...)
      match_number = overall playing order in the bracket; groups alternate, so
                     (round 1 of group 1, round 1 of group 2, ..., round 2 of group 1...)
    """
    from django.db import transaction

    discipline = Discipline.objects.filter(id=config["disciplineId"]).first()
    split_clubs = config.get("splitClubs", True)
    min_size = int(config.get("minMembersPerGroup", DEFAULT_MIN_GROUP_SIZE))
    max_size = int(config.get("maxMembersPerGroup", DEFAULT_MAX_GROUP_SIZE))

    with transaction.atomic():
        for category in discipline.categories.all():
            registrations = list(
                DisciplineMember.objects
                .filter(category=category, discipline=discipline)
                .select_related("person__club")
                .order_by("id")
            )

            sizes = compute_group_sizes(len(registrations), min_size, max_size)
            if not sizes:
                continue  # fewer than 3 athletes: the category does not take place

            bracket_name = f'{discipline.name} {category.name} {category.gender}'
            if category.min_weight is not None:
                bracket_name += f' +{category.min_weight}kg'
            elif category.max_weight is not None:
                bracket_name += f' -{category.max_weight}kg'

            bracket = Bracket.objects.create(
                name=bracket_name,
                category=category,
                discipline=discipline,
                event=event,
                draw_type="Liga",
            )

            groups = distribute_into_groups(registrations, sizes, split_clubs)

            schedules = []
            for number, members in enumerate(groups, start=1):
                group = BracketGroup.objects.create(bracket=bracket, number=number)
                persons = [reg.person for reg in members]
                BracketGroupMember.objects.bulk_create([
                    BracketGroupMember(group=group, person=person, position=i)
                    for i, person in enumerate(persons, start=1)
                ])
                schedules.append((group, persons, order_matches(pick_pairings(persons))))

            matches, match_number = [], 1
            for round_number in range(1, max(len(s[2]) for s in schedules) + 1):
                for group, persons, pairs in schedules:
                    if round_number <= len(pairs):
                        a, b = pairs[round_number - 1]
                        matches.append(Match(
                            bracket=bracket,
                            group=group,
                            contender_1=persons[a],
                            contender_2=persons[b],
                            round_number=round_number,
                            match_number=match_number,
                        ))
                        match_number += 1
            Match.objects.bulk_create(matches)

    return True


def generate_torneio_draw(event: str, config: dict = None, misto: bool = False) -> bool:
    """_summary_

    Args:
        event (_type_): _description_
        config (dict, optional): _description_. Defaults to None
        misto (bool, optional): If misto, starts by checking the finals size, only to create round robins until there. Defaults to False

    Returns:
        bool: If generation was successful, returns True
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
            bracket_name += f' +{category.min_weight}kg'
        elif category.max_weight is not None:
            bracket_name += f' -{category.max_weight}kg'

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
                shuffled = list(registrations)
                random.shuffle(shuffled)
                for i, reg in enumerate(shuffled):
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