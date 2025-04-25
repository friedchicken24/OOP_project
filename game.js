document.addEventListener('DOMContentLoaded', function() {
    // Game elements
    const gameSetup = document.getElementById('game-setup');
    const gameContainer = document.getElementById('game-container');
    const gameBoard = document.getElementById('game-board');
    const playerDisplay = document.getElementById('player-display');
    const difficultyDisplay = document.getElementById('difficulty-display');
    const timeDisplay = document.getElementById('time-display');
    const attemptsDisplay = document.getElementById('attempts-display');
    const matchesDisplay = document.getElementById('matches-display');
    const totalPairsDisplay = document.getElementById('total-pairs');
    const newGameButton = document.getElementById('new-game-button');
    
    // Modal elements
    const gameCompletedModal = new bootstrap.Modal(document.getElementById('gameCompletedModal'));
    const finalTimeDisplay = document.getElementById('final-time');
    const finalAttemptsDisplay = document.getElementById('final-attempts');
    const finalScoreDisplay = document.getElementById('final-score');
    const saveScoreButton = document.getElementById('save-score-button');
    const viewHighscoresButton = document.getElementById('view-highscores-button');
    const playAgainButton = document.getElementById('play-again-button');
    
    // Game state
    let gameState = null;
    let timerInterval = null;
    let canFlip = true;
    
    // Check if a game is in progress
    function checkGameState() {
        fetch('/get_game_state')
            .then(response => response.json())
            .then(data => {
                gameState = data;
                if (gameState.player_name) {
                    // Show game board if a game exists
                    gameSetup.classList.add('d-none');
                    gameContainer.classList.remove('d-none');
                    updateGameDisplay();
                    renderGameBoard();
                    startTimer();
                }
            })
            .catch(error => console.error('Error checking game state:', error));
    }
    
    // Update game display with current state
    function updateGameDisplay() {
        playerDisplay.textContent = gameState.player_name;
        difficultyDisplay.textContent = capitalizeFirstLetter(gameState.difficulty);
        timeDisplay.textContent = gameState.time;
        attemptsDisplay.textContent = gameState.attempts;
        matchesDisplay.textContent = gameState.matched_pairs;
        totalPairsDisplay.textContent = gameState.total_pairs;
    }
    
    // Render the game board with cards
    function renderGameBoard() {
        gameBoard.innerHTML = '';
        
        // Determine number of columns based on difficulty
        let colClass;
        if (gameState.difficulty === 'easy') {
            colClass = 'col-md-3'; // 4 cards per row
        } else if (gameState.difficulty === 'normal') {
            colClass = 'col-md-3'; // 4 cards per row
        } else {
            colClass = 'col-md-2'; // 6 cards per row
        }
        
        // Create card elements
        gameState.cards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = colClass;
            
            const cardInner = document.createElement('div');
            cardInner.className = 'card-inner';
            if (card.is_flipped) {
                cardInner.classList.add('flipped');
            }
            if (card.is_matched) {
                cardInner.classList.add('matched');
            }
            
            // Front of card (hidden)
            const cardFront = document.createElement('div');
            cardFront.className = 'card-front';
            cardFront.innerHTML = '<i class="fas fa-question"></i>';
            
            // Back of card (value)
            const cardBack = document.createElement('div');
            cardBack.className = 'card-back';
            cardBack.innerHTML = `<span class="card-value">${card.value}</span>`;
            
            cardInner.appendChild(cardFront);
            cardInner.appendChild(cardBack);
            cardDiv.appendChild(cardInner);
            
            // Add click event
            cardDiv.dataset.id = card.id;
            cardDiv.addEventListener('click', handleCardClick);
            
            gameBoard.appendChild(cardDiv);
        });
    }
    
    // Handle card click
    function handleCardClick(event) {
        if (!canFlip) return;
        
        // Find the clicked card
        const cardElement = event.currentTarget;
        const cardId = parseInt(cardElement.dataset.id);
        const cardInner = cardElement.querySelector('.card-inner');
        
        // Check if card is already flipped or matched
        if (cardInner.classList.contains('flipped') || cardInner.classList.contains('matched')) {
            return;
        }
        
        // Flip the card
        flipCard(cardId);
    }
    
    // Flip a card via API
    function flipCard(cardId) {
        fetch('/flip_card', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ card_id: cardId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update game state
                gameState.attempts = data.attempts;
                gameState.matched_pairs = data.matched_pairs;
                gameState.time = data.time;
                
                // Update display
                updateGameDisplay();
                
                // Refresh the game board
                checkGameState();
                
                // Check if two cards are flipped
                const flippedCards = document.querySelectorAll('.card-inner.flipped:not(.matched)');
                if (flippedCards.length === 2) {
                    canFlip = false;
                    
                    if (data.is_match) {
                        // Match found
                        setTimeout(() => {
                            flippedCards.forEach(card => {
                                card.classList.add('matched');
                            });
                            canFlip = true;
                            
                            // Check if game is completed
                            if (data.is_completed) {
                                gameCompleted(data.score);
                            }
                        }, 500);
                    } else {
                        // No match
                        setTimeout(() => {
                            // Reset the unmatched cards
                            resetUnmatched();
                        }, 1000);
                    }
                }
            }
        })
        .catch(error => console.error('Error flipping card:', error));
    }
    
    // Reset unmatched cards via API
    function resetUnmatched() {
        fetch('/reset_unmatched', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Refresh the game board
                checkGameState();
                canFlip = true;
            }
        })
        .catch(error => console.error('Error resetting unmatched cards:', error));
    }
    
    // Start timer to update time display
    function startTimer() {
        // Clear any existing timer
        if (timerInterval) {
            clearInterval(timerInterval);
        }
        
        // Update time every second
        timerInterval = setInterval(() => {
            fetch('/get_game_state')
                .then(response => response.json())
                .then(data => {
                    timeDisplay.textContent = data.time;
                    
                    // Check if game is completed
                    if (data.is_completed && !gameState.is_completed) {
                        gameState = data;
                        gameCompleted(data.score);
                    }
                })
                .catch(error => console.error('Error updating time:', error));
        }, 1000);
    }
    
    // Game completed handler
    function gameCompleted(score) {
        // Stop the timer
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        
        // Update modal with final stats
        finalTimeDisplay.textContent = timeDisplay.textContent;
        finalAttemptsDisplay.textContent = attemptsDisplay.textContent;
        finalScoreDisplay.textContent = score;
        
        // Show completion modal
        gameCompletedModal.show();
    }
    
    // Save score handler
    saveScoreButton.addEventListener('click', function() {
        fetch('/save_score', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Disable the save button to prevent multiple saves
                saveScoreButton.disabled = true;
                saveScoreButton.textContent = 'Score Saved!';
            }
        })
        .catch(error => console.error('Error saving score:', error));
    });
    
    // View high scores button handler
    viewHighscoresButton.addEventListener('click', function() {
        window.location.href = '/highscores';
    });
    
    // Play again button handler
    playAgainButton.addEventListener('click', function() {
        // Close the modal
        gameCompletedModal.hide();
        
        // Show the setup form
        gameContainer.classList.add('d-none');
        gameSetup.classList.remove('d-none');
    });
    
    // New game button handler
    newGameButton.addEventListener('click', function() {
        // Show the setup form
        gameContainer.classList.add('d-none');
        gameSetup.classList.remove('d-none');
        
        // Stop the timer
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    });
    
    // Utility function to capitalize first letter
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    // Initialize
    checkGameState();
});
