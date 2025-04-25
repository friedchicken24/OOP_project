import json
from flask import render_template, request, jsonify, session, redirect, url_for

from app import app
from game import Game, HighScoreManager

# Initialize the high score manager
high_score_manager = HighScoreManager()

@app.route('/')
def index():
    """Render the main game page"""
    return render_template('index.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    """Start a new game"""
    player_name = request.form.get('player_name', 'Player')
    difficulty = request.form.get('difficulty', 'normal')
    
    # Create a new game
    game = Game(difficulty=difficulty, player_name=player_name)
    
    # Store game in session
    session['game'] = game.serialize()
    
    return redirect(url_for('index'))

@app.route('/get_game_state')
def get_game_state():
    """Get the current game state as JSON"""
    if 'game' not in session:
        # Start a new game if none exists
        game = Game()
        session['game'] = game.serialize()
    
    # Deserialize the game from session
    game_data = session['game']
    game = Game.deserialize(game_data)
    
    # Return the game state
    return jsonify({
        'player_name': game.player_name,
        'difficulty': game.difficulty,
        'time': game.get_formatted_time(),
        'attempts': game.attempts,
        'matched_pairs': game.matched_pairs,
        'total_pairs': len(game.cards) // 2,
        'is_completed': game.is_completed,
        'score': game.get_score(),
        'cards': [card.serialize() for card in game.cards]
    })

@app.route('/flip_card', methods=['POST'])
def flip_card():
    """Flip a card"""
    if 'game' not in session:
        return jsonify({'error': 'No active game'}), 400
    
    # Get card ID from request
    data = request.get_json()
    card_id = data.get('card_id')
    
    if card_id is None:
        return jsonify({'error': 'No card ID provided'}), 400
    
    # Deserialize the game from session
    game_data = session['game']
    game = Game.deserialize(game_data)
    
    # Flip the card
    success = game.flip_card(card_id)
    
    if not success:
        return jsonify({'error': 'Invalid card ID or card already matched'}), 400
    
    # Check for a match
    is_match = game.check_match()
    
    # Update the game in session
    session['game'] = game.serialize()
    
    return jsonify({
        'success': True,
        'is_match': is_match,
        'is_completed': game.is_completed,
        'matched_pairs': game.matched_pairs,
        'attempts': game.attempts,
        'score': game.get_score(),
        'time': game.get_formatted_time()
    })

@app.route('/reset_unmatched', methods=['POST'])
def reset_unmatched():
    """Reset unmatched cards"""
    if 'game' not in session:
        return jsonify({'error': 'No active game'}), 400
    
    # Deserialize the game from session
    game_data = session['game']
    game = Game.deserialize(game_data)
    
    # Reset unmatched cards
    game.reset_unmatched()
    
    # Update the game in session
    session['game'] = game.serialize()
    
    return jsonify({'success': True})

@app.route('/save_score', methods=['POST'])
def save_score():
    """Save the player's score"""
    if 'game' not in session:
        return jsonify({'error': 'No active game'}), 400
    
    # Deserialize the game from session
    game_data = session['game']
    game = Game.deserialize(game_data)
    
    if not game.is_completed:
        return jsonify({'error': 'Game not completed yet'}), 400
    
    # Save the score
    high_score_manager.add_score(game)
    
    return jsonify({
        'success': True,
        'score': game.get_score(),
        'player_name': game.player_name
    })

@app.route('/highscores')
def highscores():
    """Show high scores page"""
    difficulty = request.args.get('difficulty', 'normal')
    high_scores = high_score_manager.get_high_scores(difficulty)
    
    return render_template(
        'highscores.html', 
        high_scores=high_scores, 
        difficulty=difficulty
    )

@app.route('/get_highscores')
def get_highscores():
    """Get high scores as JSON"""
    difficulty = request.args.get('difficulty', 'normal')
    high_scores = high_score_manager.get_high_scores(difficulty)
    
    return jsonify({
        'difficulty': difficulty,
        'high_scores': high_scores
    })
