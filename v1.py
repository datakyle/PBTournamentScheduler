import streamlit as st
import random
from collections import defaultdict

def calculate_rematch_interval(num_players):
    return max(1, num_players // 2)

def choose_player_to_rest(players, rest_counts):
    min_rests = min(rest_counts.values())
    candidates = [p for p in players if rest_counts[p] == min_rests]
    return random.choice(candidates)

def update_recent_partners(recent_partners, player1, player2, rematch_interval):
    for player in [player1, player2]:
        recent_partners[player].append(player2 if player == player1 else player1)
        if len(recent_partners[player]) > rematch_interval:
            recent_partners[player].pop(0)

def score_pairings(pairings, player_pairing_counts):
    score = 0
    for player1, player2 in pairings:
        if player_pairing_counts[player1][player2] == 0:
            score += 0  # Strongly reward new partnerships
        else:
            score += (player_pairing_counts[player1][player2] ** 2) * 10  # Heavily penalize repeat partnerships
    return score

def generate_random_pairings(players, rest_counts):
    available_players = players.copy()
    resting_player = None
    if len(available_players) % 2 == 1:
        resting_player = choose_player_to_rest(available_players, rest_counts)
        available_players.remove(resting_player)

    random.shuffle(available_players)
    pairings = [(available_players[i], available_players[i+1]) for i in range(0, len(available_players), 2)]
    return pairings, resting_player

def create_optimized_pairings(players, player_pairing_counts, rest_counts):
    best_pairings = None
    best_score = float('inf')
    best_resting_player = None

    for _ in range(10):  # Try 10 times to get the best pairings
        pairings, resting_player = generate_random_pairings(players, rest_counts)
        score = score_pairings(pairings, player_pairing_counts)

        if score < best_score:
            best_score = score
            best_pairings = pairings
            best_resting_player = resting_player

    # Update pairing counts
    for player1, player2 in best_pairings:
        player_pairing_counts[player1][player2] += 1
        player_pairing_counts[player2][player1] += 1

    return best_pairings, best_resting_player

def create_matches(pairings, previous_match_history, player_matchups):
    # Since we're now passing in just one match worth of pairings,
    # we can simply return it as is
    return [pairings]

def calculate_match_score(pair1, pair2, previous_match_history, player_matchups):
    novelty_score = 0 if tuple(pair2) in previous_match_history[tuple(pair1)] else 1
    balance_score = sum(player_matchups[p1][p2] for p1 in pair1 for p2 in pair2)
    return novelty_score * 10 - balance_score  # Prioritize new matchups, then balance

def update_match_history(pair1, pair2, previous_match_history, player_matchups):
    previous_match_history[tuple(pair1)].add(tuple(pair2))
    previous_match_history[tuple(pair2)].add(tuple(pair1))
    for p1 in pair1:
        for p2 in pair2:
            player_matchups[p1][p2] += 1
            player_matchups[p2][p1] += 1

def generate_multi_court_schedule(players, num_rounds, num_courts):
    num_players = len(players)
    games_per_player_per_cycle = num_courts * 4 // num_players
    rests_per_player_per_cycle = 1 if num_players % (num_courts * 4) != 0 else 0
    cycle_length = games_per_player_per_cycle + rests_per_player_per_cycle

    player_pairing_counts = defaultdict(lambda: defaultdict(int))
    player_matchups = defaultdict(lambda: defaultdict(int))
    all_rounds = []

    for cycle_start in range(0, num_rounds, cycle_length):
        cycle_rounds = min(cycle_length, num_rounds - cycle_start)
        cycle_players = players.copy()
        random.shuffle(cycle_players)

        for round_in_cycle in range(cycle_rounds):
            round_matches = []
            resting_players = []

            for court in range(num_courts):
                if len(cycle_players) >= 4:
                    match_players = [cycle_players.pop() for _ in range(4)]
                    pairings, _ = create_optimized_pairings(match_players, player_pairing_counts, defaultdict(int))
                    round_matches.append(pairings)
                else:
                    resting_players.extend(cycle_players)
                    break

            all_rounds.append((round_matches, resting_players))
            cycle_players = resting_players + [player for match in round_matches for pair in match for player in pair]

    return all_rounds, player_matchups, player_pairing_counts, defaultdict(int)

def display_multi_court_schedule(all_rounds):
    st.write("### Multi-Court Pickleball Tournament Schedule:")
    for round_number, (matches, resting_players) in enumerate(all_rounds, 1):
        st.write(f"\n**Round {round_number}:**")
        if resting_players:
            st.write(f"Players resting this round: {', '.join(resting_players)}")
        for match_number, match in enumerate(matches, 1):
            (player1, player2), (player3, player4) = match
            st.write(f"Court {match_number}: {player1} & {player2} vs. {player3} & {player4}")
        st.write("---")  # Add a separator between rounds

def display_leaderboard(player_scores, late_additions):
    st.write("### Leaderboard:")
    st.write("(Points include wins and score differences)")
    sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (player, score) in enumerate(sorted_players, 1):
        late_note = " (added later)" if player in late_additions else ""
        st.write(f"{rank}. {player}: {score} points{late_note}")

def insert_player_into_schedule(player_name, all_rounds, player_matchups, player_pairing_counts, rest_counts):
    for round_number, (matches, resting_players) in enumerate(all_rounds):
        if resting_players:
            # Replace a resting player with the new player
            replaced_player = random.choice(resting_players)
            resting_players.remove(replaced_player)
            resting_players.append(player_name)
        else:
            # If no resting players, we need to adjust a match
            match_to_adjust = random.choice(matches)
            matches.remove(match_to_adjust)
            players_in_match = [p for pair in match_to_adjust for p in pair]
            player_to_rest = random.choice(players_in_match)
            players_in_match.remove(player_to_rest)
            players_in_match.append(player_name)
            resting_players.append(player_to_rest)
            
            # Create new pairings for the adjusted match
            random.shuffle(players_in_match)
            new_match = [(players_in_match[0], players_in_match[1]), (players_in_match[2], players_in_match[3])]
            matches.append(new_match)

        # Initialize matchup and pairing counts for the new player
        if player_name not in player_matchups:
            player_matchups[player_name] = defaultdict(int)
            player_pairing_counts[player_name] = defaultdict(int)
        
        for existing_player in player_matchups.keys():
            if existing_player != player_name:
                player_matchups[player_name][existing_player] = 0
                player_matchups[existing_player][player_name] = 0
                player_pairing_counts[player_name][existing_player] = 0
                player_pairing_counts[existing_player][player_name] = 0
        
        if player_name not in rest_counts:
            rest_counts[player_name] = 0

    return all_rounds, player_matchups, player_pairing_counts, rest_counts

def main():
    st.set_page_config(page_title="Pickleball Tournament")

    # Initialize session state
    if 'schedule_generated' not in st.session_state:
        st.session_state.schedule_generated = False
    if 'player_scores' not in st.session_state:
        st.session_state.player_scores = defaultdict(int)
    if 'player_names' not in st.session_state:
        st.session_state.player_names = []  # Start with an empty list
    if 'num_rounds' not in st.session_state:
        st.session_state.num_rounds = 3
    if 'points_per_win' not in st.session_state:
        st.session_state.points_per_win = 1
    if 'num_courts' not in st.session_state:
        st.session_state.num_courts = 1
    if 'all_rounds' not in st.session_state:
        st.session_state.all_rounds = []
    if 'late_additions' not in st.session_state:
        st.session_state.late_additions = set()

    st.title("Pickleball Tournament")

    tab1, tab2, tab3 = st.tabs(["Info", "Schedule", "Leaderboard"])

    with tab1:
        with st.expander("Player Management", expanded=True):
            # New player addition
            st.subheader("Add New Player:")
            new_player = st.text_input("Enter new player name", key=f"new_player_input_{len(st.session_state.player_names)}")
            if st.button("Add Player"):
                add_new_player(new_player)

            # Display current players
            named_players = [player for player in st.session_state.player_names if not player.startswith("Player")]
            if named_players:
                st.subheader("Current Players:")
                for i, player in enumerate(named_players):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(player)
                    with col2:
                        if st.button("Remove", key=f"remove_{i}"):
                            st.session_state.player_names.remove(player)
                            st.rerun()

        with st.expander("Tournament Settings", expanded=True):
            st.session_state.num_rounds = st.number_input("Rounds", min_value=1, value=st.session_state.num_rounds)
            max_courts = max(1, len(st.session_state.player_names) // 4)
            st.session_state.num_courts = st.number_input("Courts", min_value=1, max_value=max_courts, value=min(st.session_state.num_courts, max_courts))
            st.session_state.points_per_win = st.number_input("Points per Win", min_value=1, value=st.session_state.points_per_win)

        # Only enable the "Generate Schedule" button when there are at least 4 players
        if len(st.session_state.player_names) >= 4:
            if st.button("Generate Schedule"):
                st.session_state.all_rounds, st.session_state.player_matchups, st.session_state.player_pairing_counts, st.session_state.rest_counts = generate_multi_court_schedule(
                    st.session_state.player_names, 
                    st.session_state.num_rounds, 
                    st.session_state.num_courts
                )
                st.session_state.schedule_generated = True
                st.rerun()
        else:
            st.warning("You need at least 4 players to generate a schedule.")

    with tab2:
        if st.session_state.schedule_generated:
            st.header("Tournament Schedule and Results")
            
            if st.button("Show/Hide Original Schedule"):
                st.session_state.show_schedule = not st.session_state.get('show_schedule', False)

            if st.session_state.get('show_schedule', False):
                with st.expander("Original Tournament Schedule", expanded=True):
                    display_multi_court_schedule(st.session_state.all_rounds)

            # Display updated schedule if there are late additions
            if st.session_state.late_additions:
                with st.expander("Updated Schedule (Including New Players)", expanded=False):
                    st.write("This schedule includes newly added players:")
                    display_multi_court_schedule(st.session_state.all_rounds)

            # Original match results
            with st.expander("Original Match Results", expanded=True):
                display_match_results_form(st.session_state.all_rounds, is_updated=False)

            # Updated match results for new players
            if st.session_state.late_additions:
                with st.expander("Updated Match Results (Including New Players)", expanded=True):
                    display_match_results_form(st.session_state.all_rounds, is_updated=True)

        else:
            st.info("Generate a schedule in the Setup tab to enter match results here.")

    with tab3:
        st.header("Leaderboard")
        if st.session_state.schedule_generated:
            display_leaderboard(st.session_state.player_scores, st.session_state.late_additions)
        else:
            st.info("Generate a schedule and enter match results to view the leaderboard.")

    if st.button("Reset Tournament"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def display_match_results_form(all_rounds, is_updated):
    with st.form(f"match_results_form_{'updated' if is_updated else 'original'}"):
        for round_number, (matches, resting_players) in enumerate(all_rounds, 1):
            st.subheader(f"Round {round_number}")
            for match_number, match in enumerate(matches, 1):
                key = f"round_{round_number}_match_{match_number}_{'updated' if is_updated else 'original'}"
                radio_key = f"radio_{key}"
                score_key = f"score_{key}"
                
                (player1, player2), (player3, player4) = match
                
                # Reset the session state for this match if the players have changed
                if key not in st.session_state or st.session_state[key] not in ["Not played", f"{player1} & {player2}", f"{player3} & {player4}"]:
                    st.session_state[key] = "Not played"
                if score_key not in st.session_state:
                    st.session_state[score_key] = {"team1": 0, "team2": 0}
                
                st.write(f"{player1} & {player2} vs {player3} & {player4}")
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    team1_score = st.number_input(f"{player1} & {player2}", min_value=0, value=st.session_state[score_key]["team1"], key=f"team1_{score_key}")
                with col2:
                    team2_score = st.number_input(f"{player3} & {player4}", min_value=0, value=st.session_state[score_key]["team2"], key=f"team2_{score_key}")
                with col3:
                    options = ["Not played", f"{player1} & {player2}", f"{player3} & {player4}"]
                    index = options.index(st.session_state[key])
                    winner = st.radio(
                        "Winner",
                        options=options,
                        key=radio_key,
                        index=index,
                        horizontal=True
                    )
                
                st.session_state[key] = winner
                st.session_state[score_key] = {"team1": team1_score, "team2": team2_score}
        
        submitted = st.form_submit_button("Update Scores")
    
    if submitted:
        update_scores(all_rounds, is_updated)
        st.success("Scores updated successfully!")

def update_scores(all_rounds, is_updated):
    for round_number, (matches, _) in enumerate(all_rounds, 1):
        for match_number, match in enumerate(matches, 1):
            key = f"round_{round_number}_match_{match_number}_{'updated' if is_updated else 'original'}"
            score_key = f"score_{key}"
            winner = st.session_state[key]
            team1_score = st.session_state[score_key]["team1"]
            team2_score = st.session_state[score_key]["team2"]
            score_diff = abs(team1_score - team2_score)
            
            (player1, player2), (player3, player4) = match
            
            # Update scores
            if winner == f"{player1} & {player2}":
                st.session_state.player_scores[player1] += (st.session_state.points_per_win + score_diff)
                st.session_state.player_scores[player2] += (st.session_state.points_per_win + score_diff)
            elif winner == f"{player3} & {player4}":
                st.session_state.player_scores[player3] += (st.session_state.points_per_win + score_diff)
                st.session_state.player_scores[player4] += (st.session_state.points_per_win + score_diff)

def add_new_player(new_player):
    if new_player and new_player not in st.session_state.player_names:
        st.session_state.player_names.append(new_player)
        if st.session_state.schedule_generated:
            st.session_state.all_rounds, st.session_state.player_matchups, st.session_state.player_pairing_counts, st.session_state.rest_counts = insert_player_into_schedule(
                new_player,
                st.session_state.all_rounds,
                st.session_state.player_matchups,
                st.session_state.player_pairing_counts,
                st.session_state.rest_counts
            )
            st.session_state.player_scores[new_player] = 0
            st.session_state.late_additions.add(new_player)
        st.rerun()

if __name__ == "__main__":
    main()
