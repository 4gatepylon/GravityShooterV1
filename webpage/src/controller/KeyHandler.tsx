import React, { ReactNode, useState, useContext, useEffect } from 'react';
import { Context } from "../model/State"

// Special keycodes
let BACKSPACE = "backspace"
let ENTER = "enter"

// Window key events
interface KeyIF {
    key: string
}
// KeyHandler simple handles keys by calling the corresponding state update request functions in
// with hooks in the Context function.
interface KeyHandlerIF { children: ReactNode }
export default function KeyHandler(props: KeyHandlerIF) {
    let {
        // We use these to decide when to let input through and when not to
        guess,
        guessLetter,
        pastGuesses,
        guessWord,
        backspaceLetter,
        thisPlayerId,
        // We use these below to decide basically what preset of inputs are allowed
        // (i.e. you are allowed to type names in general welcome and then simply word letters
        // during the game)
        isGameOver,
        gotName,
        gotMatch,
      } = useContext(Context)
    
      
    
      const DEBUG = true
      function handleKeyPress(keyEvent: KeyIF) {
        if (DEBUG) {
            console.log(`You just typed ${keyEvent.key}`);
        }

        if (!gotName) {
            // In this case, do nothing; we are using a regular form way under the window
            // in the DOM to fetch the name in one fell swoop
        } else if (!gotMatch) {
            // Do nothing because this is a blank loading screen
        } else {
            // In the game case, just try to let them type the letter (or guess the word or backspace
            // the letter, or whatever)

            const MAX_NUM_GUESSES = 6
            const MAX_GUESS_LENGTH = 5
            const MIN_GUESS_LEN = 1
            const KEY_LENGTH = 1;
            const _pastGuesses = pastGuesses(thisPlayerId)
            const _guess = guess(thisPlayerId)
            const _readyToGuess = guess(thisPlayerId).length == MAX_GUESS_LENGTH

            const keycode = keyEvent.key.toLowerCase()
            if (keycode == BACKSPACE && _guess.length >= MIN_GUESS_LEN) {
                backspaceLetter()
            } else if (_readyToGuess && keycode == ENTER) {
                guessWord()
            } else if (!_readyToGuess && keycode.length == KEY_LENGTH && 'a' <= keycode && keycode <= 'z') {
                guessLetter(keycode)
            }
        }
      }
    
      // Set a global focusless keydown handler as in https://github.com/facebook/react/issues/15815
      // Apparently you need to refresh this every time, but it's not clear why
      // For simplicity, we only handle keydown, which means that if you keep holding it will keep
      //   typing. In practice this is fine, but to make a more polished game you might want to
      //   handle keyup (the reason we can't just handle keypress is because the window element
      //   apparently doesn't have it).
      useEffect(() => {
        window.addEventListener('keydown', handleKeyPress)
        return () => {
          window.removeEventListener('keydown', handleKeyPress)
        }
      })
    
    // Doesn't return anything, just wrap your functionality in KeyHandler so that
    // everything under it will handle keys (actually, this might even affect things
    // above it since it sets listeners on window)
    return <div>{props.children}</div>
}