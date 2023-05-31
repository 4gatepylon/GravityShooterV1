import React, { useState, useContext, useEffect } from 'react';
import logo from './assets/logo.svg';
import Grid from './view/Grid'
import './styles/App.css';
import { Context, GameStateIF } from './model/State'
import { WelcomeForm, WelcomeLoading } from "./view/WelcomePage"


// A section basically renders a grid for a player, so you can see what that player has guessed so far (etc)
interface SectionIF { 
  paddingRight: string,
  isGameOver: boolean,
  playerId: string,
  playerName: string,
  winner: string
}
function Section(props: SectionIF) {

  return (
    // We are forced to inline to avoid type errors
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      paddingLeft: "10px",
      paddingRight: props.paddingRight
    }}>
      <h1>
        {props.playerName} {props.isGameOver ? (props.winner == props.playerId ? "[WINNER]" : "[LOSER]") : ""}
      </h1>
      <Grid player={props.playerId} />
    </div>
  )
}

// This renders just a black wall that seperates the two grids for ease of understanding the UI
// (it's pretty jank)
function Wall() {
  return (
    <div style= {{
      marginTop: "5%",
      paddingTop: "20%",
      paddingBottom: "20%",
      paddingLeft: "5px",
      paddingRight: "5px",
      backgroundColor: "black"
    }} />
  )
}

// This renders a message that tells you who won on the right side
// (also pretty jank)
interface GameOverMessageIF { winner: string }
function GameOverMessage(props: GameOverMessageIF) {
  const winnerMessage = props.winner == "" ? "No winner!" : `${props.winner} wins!`

  return (
    // We are forced to inline to avoid type errors
    <div style={{
      paddingTop: "40px",
      paddingLeft: "20px",
      fontSize: "60px"
    }}>
        {[
          "Game", 
          "Over!", 
          winnerMessage
        ].map(
          (w: string) => <h1>{w}</h1>
        )}
    </div>
  )
}

function Game() {
  let {
    // Be able to display both the name titles
    thisPlayerName,
    thisPlayerId,
    otherPlayerName,
    otherPlayerId,
    // Display a message when it is over
    isGameOver,
    winner,
  } = useContext(Context)

  return (
    // We are forced to inline to avoid type errors
    <div style={{
        // NOTE we will want a better way to center shit going forward
        display: 'flex',
        flexDirection: 'row'
      }
    }>
      <Section 
        isGameOver={isGameOver}
        playerId={thisPlayerId}
        playerName={thisPlayerName}
        paddingRight="10px"
        winner={winner}
      />
      <Wall />
      <Section 
        isGameOver={isGameOver}
        playerId={otherPlayerId}
        playerName={otherPlayerName}
        paddingRight="0px"
        winner={winner}
      />
      {isGameOver && <GameOverMessage winner={winner} />}
    </div>
  )
}

export default function App() {
  let { 
    gotName,
    gotMatch
  } = useContext(Context)
  
  // there's a lot of improvements that can be made with styling
  return (
    !gotName ? (
      <WelcomeForm />
    ) :
    !gotMatch ? (
      <WelcomeLoading />
    ) : (
      <Game />
    )
  );
}
