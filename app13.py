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
    matches = []
    remaining_pairings = pairings.copy()

    while len(remaining_pairings) > 1:
        pair1 = remaining_pairings.pop(0)
        best_match = None
        best_score = float('-inf')

        for i, pair2 in enumerate(remaining_pairings):
            if set(pair1).isdisjoint(set(pair2)):  # Ensure no player is playing against themselves
                score = calculate_match_score(pair1, pair2, previous_match_history, player_matchups)
                if score > best_score:
                    best_score = score
                    best_match = (i, pair2)

        if best_match:
            i, pair2 = best_match
            matches.append((pair1, pair2))
            update_match_history(pair1, pair2, previous_match_history, player_matchups)
            remaining_pairings.pop(i)
        else:
            # If no valid match found, put the pair back and try again later
            remaining_pairings.append(pair1)

    return matches

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

def generate_tournament_schedule(players, num_rounds):
    player_pairing_counts = defaultdict(lambda: defaultdict(int))
    rest_counts = {player: 0 for player in players}  # Initialize rest counts for all players
    previous_match_history = defaultdict(set)
    player_matchups = defaultdict(lambda: defaultdict(int))
    all_rounds = []

    for _ in range(num_rounds):
        pairings, resting_player = create_optimized_pairings(players, player_pairing_counts, rest_counts)
        matches = create_matches(pairings, previous_match_history, player_matchups)
        all_rounds.append((matches, resting_player))

        # Update rest counts after each round
        if resting_player:
            rest_counts[resting_player] += 1

    return all_rounds, player_matchups, player_pairing_counts, rest_counts

def display_tournament_schedule(all_rounds):
    st.write("### Pickleball Tournament Schedule:")
    for round_number, (matches, resting_player) in enumerate(all_rounds, 1):
        st.write(f"\n**Round {round_number}:**")
        if resting_player:
            st.write(f"Player resting this round: {resting_player}")
        for match_number, (pair1, pair2) in enumerate(matches, 1):
            st.write(f"Match {match_number}: {pair1[0]} & {pair1[1]} vs. {pair2[0]} & {pair2[1]}")
        st.write("---")  # Add a separator between rounds

def display_player_matchup_counts(player_matchups):
    st.write("\n### Player Matchup Counts (Times Faced Each Other):")
    for player1, opponents in player_matchups.items():
        for player2, count in opponents.items():
            if player1 < player2:
                st.write(f"{player1} vs. {player2}: {count} times")

def display_partnership_stats(player_pairing_counts):
    st.write("\n### Partnership Statistics (Times Paired Together):")
    for player1 in player_pairing_counts:
        for player2, count in player_pairing_counts[player1].items():
            if player1 < player2:  # To avoid duplicate pairs
                st.write(f"{player1} and {player2} partnered {count} times")

def display_rest_stats(rest_counts):
    st.write("\n### Rest Statistics (Times Rested):")
    for player, count in rest_counts.items():
        st.write(f"{player} rested {count} times")

def generate_printable_schedule(all_rounds):
    schedule = "Pickleball Doubles Tournament - Match Results\n\n"
    for round_number, (matches, resting_player) in enumerate(all_rounds, 1):
        schedule += f"Round {round_number}:\n"
        if resting_player:
            schedule += f"Player resting this round: {resting_player}\n"
        for match_number, (pair1, pair2) in enumerate(matches, 1):
            schedule += f"Match {match_number}: {pair1[0]} & {pair1[1]} vs. {pair2[0]} & {pair2[1]}\n"
            schedule += "Winner: [ ] Team 1  [ ] Team 2\n"
            schedule += "---\n"  # Add a separator between matches
        schedule += "\n"  # Add an extra line between rounds
    return schedule

def display_schedule_history(schedule_history):
    st.write("### Last 3 Generated Schedules:")
    if not schedule_history:
        st.write("No History")
    else:
        for i, (players, num_rounds, all_rounds) in enumerate(reversed(schedule_history[-3:]), 1):
            st.write(f"\n**Schedule {i}:**")
            st.write(f"Players: {', '.join(players)}")
            st.write(f"Number of rounds: {num_rounds}")
            display_tournament_schedule(all_rounds)

def main():
    st.title("Pickleball Doubles Tournament Scheduler")

    # Initialize session state
    if 'schedule_generated' not in st.session_state:
        st.session_state.schedule_generated = False
    if 'schedule_history' not in st.session_state:
        st.session_state.schedule_history = []
    if 'num_players' not in st.session_state:
        st.session_state.num_players = 4
    if 'player_names' not in st.session_state:
        st.session_state.player_names = [f"Player {i+1}" for i in range(4)]
    if 'num_rounds' not in st.session_state:
        st.session_state.num_rounds = 3

    # Add a reset button
    if st.button("Reset All Inputs"):
        # Reset all inputs and clear the generated schedule
        st.session_state.num_players = 4
        st.session_state.player_names = [f"Player {i+1}" for i in range(4)]
        st.session_state.num_rounds = 3
        st.session_state.schedule_generated = False
        st.rerun()  # Corrected line

    num_players = st.number_input("Enter the number of players:", min_value=2, step=1, value=st.session_state.num_players, key="num_players_input")

    # Update player names if number of players changed
    if num_players != len(st.session_state.player_names):
        st.session_state.player_names = st.session_state.player_names[:num_players] + [f"Player {i+1}" for i in range(len(st.session_state.player_names), num_players)]

    players = [st.text_input(f"Name for Player {i + 1}", value=st.session_state.player_names[i], key=f"player_{i}") for i in range(num_players)]

    num_rounds = st.number_input("Enter the number of rounds in the tournament:", min_value=1, step=1, value=st.session_state.num_rounds, key="num_rounds_input")

    # Update session state
    st.session_state.num_players = num_players
    st.session_state.player_names = players
    st.session_state.num_rounds = num_rounds

    if st.button("Generate Tournament Schedule"):
        st.session_state.all_rounds, st.session_state.player_matchups, st.session_state.player_pairing_counts, st.session_state.rest_counts = generate_tournament_schedule(players, num_rounds)
        st.session_state.schedule_generated = True
        st.session_state.schedule_history.append((players, num_rounds, st.session_state.all_rounds))
        display_tournament_schedule(st.session_state.all_rounds)

    if st.session_state.schedule_generated:
        # Add buttons to show statistics
        if st.button("Show Times Players Faced Each Other"):
            display_player_matchup_counts(st.session_state.player_matchups)

        if st.button("Show Times Players Paired Together"):
            display_partnership_stats(st.session_state.player_pairing_counts)

        if st.button("Show Rest Statistics"):
            display_rest_stats(st.session_state.rest_counts)

        printable_schedule = generate_printable_schedule(st.session_state.all_rounds)
        st.download_button(
            label="Download Printable Tournament Schedule",
            data=printable_schedule,
            file_name="pickleball_tournament_schedule.txt",
            mime="text/plain"
        )

    if st.button("Show Schedule History"):
        display_schedule_history(st.session_state.schedule_history)

if __name__ == "__main__":
    main()
