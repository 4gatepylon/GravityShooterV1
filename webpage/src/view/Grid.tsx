import React, { ReactNode, useState, useContext } from 'react';
import { Context } from '../model/State'
import '../styles/App.css';

// https://www.color-meanings.com/shades-of-yellow-color-names-html-hex-rgb-codes/
// typescript apparently a little retarded somtimes so couldnt' import
export const BLACK: string = "#000000"; // generic, might be useful
// Guessed, right letter and position
export const GREEN = "#3CB043";
export const HELLGREEN = "#5DBB63";
// Guessed, right letter but not position
export const YELLOW = "#F9E076";
export const HELLYELLOW = "#FDEFB2";
// Guessed, wrong letter
export const RED = "#D0312D";
export const HELLRED = "#BC5443";
// Not yet guessed
export const WHITE = "#FFFFFF";
export const HELLGREY = "#F9F9F9";

// A box renders a small box with a letter inside of it
interface BoxI {
    row: number
    col: number
    player: string
}
function Box(props: BoxI) {
    const { 
        guess,
        pastGuesses,
        secretWord
    } = useContext(Context)

    const player = props.player
    const _guess = guess(player)
    const _pastGuesses = pastGuesses(player)
    const _secretWord = secretWord(player)

    // A hover effect makes the box feel more interactive and pretty
    const [isHover, setIsHover] = useState(false);
    const handleMouseEnter = () => {
        setIsHover(true);
    };
    const handleMouseLeave = () => {
        setIsHover(false);
    };

    const row = props.row
    const col = props.col
    const letter = row < _pastGuesses.length && col < _pastGuesses[row].length ? (
        _pastGuesses[row][col]
    ) : (
        row == _pastGuesses.length && col < _guess.length ? (
            _guess[col]
        ) : (
            ""
        )
    );
    const letterAlreadyGuessed = row < _pastGuesses.length
    const indexValid = letterAlreadyGuessed && col < _secretWord.length
    const rightLetterAndSpace = indexValid && letter == _secretWord[col]
    const rightLetter = rightLetterAndSpace || indexValid && _secretWord.includes(letter)

    const backgroundColor = letterAlreadyGuessed ? (
       rightLetterAndSpace ? (
            !isHover ? GREEN : HELLGREEN
        ) : (
            // NOTE we ignore count here
            rightLetter ? (
                !isHover ? YELLOW: HELLYELLOW
            ) : (
                !isHover ? RED : HELLRED
            )
        )
    ) : (
        !isHover ? WHITE : HELLGREY
    );

    const style = {
        backgroundColor: backgroundColor,
        padding: "40px",
        margin: "10px",
        outline: "1px solid black",
    };

    const letterStyle = {
        bottom: "32px",
        right: "32px",
        fontSize: "32px"
    }

    return (
        // Have to use className for position because position
        // type is not seemingly supported by React.
        <div
            style={style}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            className="position_rel"
        >
            <text className="position_abs" style={letterStyle}>
                {letter}
            </text>
        </div>
    );
}

// Grid width and height
const WIDTH = 5;
const HEIGHT = 6;
// Grid expects to take in a player 
interface GridI { player: string };
export default function Grid(props: GridI) {
    // NOTE in the future it would be nice to find a functional way to write this instead
    // because this sort of code sucks
    let rows = new Array<Array<ReactNode>>();
    for (let i = 0; i < HEIGHT; i++) {
        rows.push(new Array<ReactNode>());
        for (let j = 0; j < WIDTH; j++) {
            rows[rows.length - 1].push(
                <Box 
                    row={i}
                    col={j}
                    player={props.player} 
                />
            );
        }
    }

    // Map the grid of boxes to divs that have the right orientation on the screen
    let drawableRows = rows.map(
        (row: Array<ReactNode>, i: number) => (
            // Forced to inline to avoid typing issues
            <div
                style={{ 
                    display: 'flex',
                    flexDirection: 'row'
                }}
                key={i}
            >  
                {row}
            </div>
        )
    );
    
    // Display the array
    return (
        // Forced to inline to avoid type errors
        <div style={{
            display: 'flex',
            flexDirection: 'column'
        }}>
            {drawableRows}
        </div>
    );
}