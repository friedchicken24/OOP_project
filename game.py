import json
import os
import random
import time
from datetime import datetime

class Card:

    def __init__(self, id, value):
        self.id = id
        self.value = value
        self.is_flipped = False
        self.is_matched = False
    
    def flip(self):
        """Flip the card"""
        self.is_flipped = not self.is_flipped
        
    def match(self):
        """Mark card as matched"""
        self.is_matched = True
        
    def serialize(self):
        """Convert card object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'value': self.value,
            'is_flipped': self.is_flipped,
            'is_matched': self.is_matched
        }
        
    @classmethod
    def deserialize(cls, data):
        """Create a card object from dictionary data"""
        card = cls(data['id'], data['value'])
        card.is_flipped = data['is_flipped']
        card.is_matched = data['is_matched']
        return card

class Game:
    """
    Represents the memory match game
    """
    def __init__(self, difficulty='normal', player_name="Player"):
        self.player_name = player_name
        self.start_time = time.time()
        self.end_time = None
        self.attempts = 0
        self.matched_pairs = 0
        self.is_completed = False
        self.difficulty = difficulty
        self.cards = self._create_deck()
        
    def _create_deck(self):
        """Create a deck of cards based on difficulty level"""
        # Card values - using emojis for easy visualization
        card_values = ['🍎', '🍌', '🍓', '🍕', '🍦', '🍩', '🍔', '🌮', 
                       '🚀', '🚗', '🎮', '🎸', '🎯', '⚽', '🎨', '🎭']
        
        # Number of pairs based on difficulty
        if self.difficulty == 'easy':
            num_pairs = 6
        elif self.difficulty == 'normal':
            num_pairs = 8
        else:  # hard
            num_pairs = 12
            
        # Select card values for this game
        selected_values = card_values[:num_pairs]
        
        # Create pairs of cards
        cards = []
        for i, value in enumerate(selected_values):
            # Add two cards with the same value (a pair)
            cards.append(Card(i * 2, value))
            cards.append(Card(i * 2 + 1, value))
            
        # Shuffle the cards
        random.shuffle(cards)
        return cards
    
    def flip_card(self, card_id):
        """Flip a card by its ID"""
        # Find the card by ID
        card = next((c for c in self.cards if c.id == card_id), None)
        
        if card and not card.is_matched:
            card.flip()
            return True
        return False
    
    def check_match(self):
        """Check if the currently flipped cards match"""
        flipped_cards = [card for card in self.cards if card.is_flipped and not card.is_matched]
        
        # If two cards are flipped, check for a match
        if len(flipped_cards) == 2:
            self.attempts += 1
            
            if flipped_cards[0].value == flipped_cards[1].value:
                # Match found
                flipped_cards[0].match()
                flipped_cards[1].match()
                self.matched_pairs += 1
                
                # Check if all pairs are matched
                total_pairs = len(self.cards) // 2
                if self.matched_pairs == total_pairs:
                    self.end_time = time.time()
                    self.is_completed = True
                
                return True
            return False
        return None  # Not enough cards flipped to check
    
    def reset_unmatched(self):
        """Reset any unmatched flipped cards"""
        for card in self.cards:
            if card.is_flipped and not card.is_matched:
                card.flip()
    
    def get_game_duration(self):
        """Get the duration of the game in seconds"""
        if self.end_time:
            return int(self.end_time - self.start_time)
        return int(time.time() - self.start_time)
    
    def get_formatted_time(self):
        """Get the formatted time (MM:SS)"""
        seconds = self.get_game_duration()
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_score(self):
        """Calculate the player's score"""
        if not self.is_completed:
            return 0
            
        duration = self.get_game_duration()
        # Score calculation: base score depends on difficulty, 
        # then adjusted for time and attempts
        if self.difficulty == 'easy':
            base_score = 1000
        elif self.difficulty == 'normal':
            base_score = 2000
        else:  # hard
            base_score = 3000
            
        time_factor = 1.0 - min(0.7, duration / 300)  # Lose up to 70% for time (cap at 5 minutes)
        attempt_factor = 1.0 - min(0.5, (self.attempts - self.matched_pairs) / 30)  # Lose up to 50% for extra attempts
        
        score = int(base_score * time_factor * attempt_factor)
        return max(score, 1)  # Minimum score is 1
    
    def serialize(self):
        """Convert game object to dictionary for JSON serialization"""
        return {
            'player_name': self.player_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'attempts': self.attempts,
            'matched_pairs': self.matched_pairs,
            'is_completed': self.is_completed,
            'difficulty': self.difficulty,
            'cards': [card.serialize() for card in self.cards]
        }
        
    @classmethod
    def deserialize(cls, data):
        """Create a game object from dictionary data"""
        game = cls(data['difficulty'], data['player_name'])
        game.start_time = data['start_time']
        game.end_time = data['end_time']
        game.attempts = data['attempts']
        game.matched_pairs = data['matched_pairs']
        game.is_completed = data['is_completed']
        game.cards = [Card.deserialize(card_data) for card_data in data['cards']]
        return game

class HighScoreManager:
    """
    Manages the high scores for the memory match game
    """
    def __init__(self, file_path='data/highscores.json'):
        self.file_path = file_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.high_scores = self._load_high_scores()
    
    def _load_high_scores(self):
        """Load high scores from JSON file"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize with empty high scores for each difficulty
            return {
                'easy': [],
                'normal': [],
                'hard': []
            }
    
    def _save_high_scores(self):
        """Save high scores to JSON file"""
        with open(self.file_path, 'w') as f:
            json.dump(self.high_scores, f, indent=2)
    
    def add_score(self, game):
        """Add a new high score"""
        if not game.is_completed:
            return False
            
        score_data = {
            'player_name': game.player_name,
            'score': game.get_score(),
            'time': game.get_game_duration(),
            'attempts': game.attempts,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        difficulty = game.difficulty
        self.high_scores[difficulty].append(score_data)
        
        # Sort by score (descending)
        self.high_scores[difficulty].sort(key=lambda x: x['score'], reverse=True)
        
        # Keep only top 10 scores
        self.high_scores[difficulty] = self.high_scores[difficulty][:10]
        
        # Save to file
        self._save_high_scores()
        return True
    
    def get_high_scores(self, difficulty='normal'):
        """Get high scores for a specific difficulty"""
        return self.high_scores.get(difficulty, [])
    
    def get_all_high_scores(self):
        """Get all high scores"""
        return self.high_scores
