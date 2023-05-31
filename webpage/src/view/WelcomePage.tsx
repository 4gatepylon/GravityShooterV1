import React, { useContext, useState, useEffect } from "react"

import { Context } from "../model/State"

// Shared janky style just to make it a little less far to the side
const PADDING_STYLE = {
    paddingLeft: "40px",
    paddingRight: "40px"
}

export function WelcomeForm () {
    const { getName } = useContext(Context)

    const [value, setValue] = useState("")
    function handleSubmit(event: any) {
        if (DEBUG) {
            console.log("Submitted a name")
        }
        event.preventDefault()

        // This will send a request to the server which is handled by the response handler in the context/state
        getName(event.target.name.value)
        
    }
    const DEBUG = true
    function handleChange(event: any) {
        setValue(event.target.value)
    }

    return (
        <div style={PADDING_STYLE}>
            <h1>
                Welcome to 1v1 Wordle!
            </h1>
            <p>
                Please enter your name.
                This is very similar to regular wordle, but in 1v1 mode you will see the wordle tables
                of both you and your opponent. However, you will have two different words. You will
                be racing at the same time (in real time; no turns) to try and guess your word.
                Have fun!
            </p>
            <form onSubmit={(e) => handleSubmit(e)}>
                <label>
                    Name:
                    <input type="text" value={value} onChange={(e) => handleChange(e)} name="name"/>
                </label>
            <input type="submit" value="Submit" />
            </form>
        </div>
    );
  }

export function WelcomeLoading() {
    const { getMatch, gotName, thisPlayerId } = useContext(Context)

    // On hitting the loading screen, try to get another opponent
    const DEBUG = true
    useEffect(() => {
        // The second clause is slightly redundant but necessary to fix a bug
        // NOTE in the future we may want to clean that up
        if (gotName && thisPlayerId != "") {
            if (DEBUG) {
                console.log(`Player id ${thisPlayerId} getting match`)
            }
            getMatch()
        }
    }, [gotName, thisPlayerId])

    return (
        <div style={PADDING_STYLE}>
            <h1>Please wait while we find an opponent!</h1>
        </div>
    )
}