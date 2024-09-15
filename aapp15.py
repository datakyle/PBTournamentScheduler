# Write your code here :-)
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

def display_leaderboard(player_scores):
    st.write("### Leaderboard:")
    sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (player, score) in enumerate(sorted_players, 1):
        st.write(f"{rank}. {player}: {score} points")

def main():
    st.title("Americano Style Pickleball Tournament")

    # Initialize session state
    if 'schedule_generated' not in st.session_state:
        st.session_state.schedule_generated = False
    if 'player_scores' not in st.session_state:
        st.session_state.player_scores = defaultdict(int)
    if 'num_players' not in st.session_state:
        st.session_state.num_players = 4
    if 'player_names' not in st.session_state:
        st.session_state.player_names = [f"Player {i+1}" for i in range(4)]
    if 'num_rounds' not in st.session_state:
        st.session_state.num_rounds = 3
    if 'points_per_win' not in st.session_state:
        st.session_state.points_per_win = 1

    # Add a reset button
    if st.button("Reset All Inputs"):
        st.session_state.num_players = 4
        st.session_state.player_names = [f"Player {i+1}" for i in range(4)]
        st.session_state.num_rounds = 3
        st.session_state.schedule_generated = False
        st.session_state.player_scores = defaultdict(int)
        st.session_state.points_per_win = 1
        st.rerun()

    num_players = st.number_input("Enter the number of players:", min_value=2, step=1, value=st.session_state.num_players, key="num_players_input")

    # Update player names if number of players changed
    if num_players != len(st.session_state.player_names):
        st.session_state.player_names = st.session_state.player_names[:num_players] + [f"Player {i+1}" for i in range(len(st.session_state.player_names), num_players)]

    players = [st.text_input(f"Name for Player {i + 1}", value=st.session_state.player_names[i], key=f"player_{i}") for i in range(num_players)]

    num_rounds = st.number_input("Enter the number of rounds in the tournament:", min_value=1, step=1, value=st.session_state.num_rounds, key="num_rounds_input")

    points_per_win = st.number_input("Points awarded per win:", min_value=1, step=1, value=st.session_state.points_per_win, key="points_per_win_input")

    # Update session state
    st.session_state.num_players = num_players
    st.session_state.player_names = players
    st.session_state.num_rounds = num_rounds
    st.session_state.points_per_win = points_per_win

    if st.button("Generate Tournament Schedule"):
        st.session_state.all_rounds, st.session_state.player_matchups, st.session_state.player_pairing_counts, st.session_state.rest_counts = generate_tournament_schedule(players, num_rounds)
        st.session_state.schedule_generated = True
        display_tournament_schedule(st.session_state.all_rounds)

    if st.session_state.schedule_generated:
        st.write("### Enter Match Results:")
        for round_number, (matches, resting_player) in enumerate(st.session_state.all_rounds, 1):
            st.write(f"\n**Round {round_number}:**")
            for match_number, (pair1, pair2) in enumerate(matches, 1):
                winner = st.radio(
                    f"Match {match_number}: {pair1[0]} & {pair1[1]} vs. {pair2[0]} & {pair2[1]}",
                    options=["Not played", "Team 1 wins", "Team 2 wins"],
                    key=f"round_{round_number}_match_{match_number}"
                )
                if winner == "Team 1 wins":
                    st.session_state.player_scores[pair1[0]] += points_per_win
                    st.session_state.player_scores[pair1[1]] += points_per_win
                elif winner == "Team 2 wins":
                    st.session_state.player_scores[pair2[0]] += points_per_win
                    st.session_state.player_scores[pair2[1]] += points_per_win

        display_leaderboard(st.session_state.player_scores)

if __name__ == "__main__":
    main()
