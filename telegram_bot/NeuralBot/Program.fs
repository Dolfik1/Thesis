module Program

open Funogram.Bot

open NeuralBot
open NeuralBot.Types
    
let update botContext context = 
    Commands.onSay botContext context |> ignore
    
[<EntryPoint>]
let main argv =
    let botContext = {
        DataContext = Data.init ()
        ApiUrl = argv.[1]
    }

    match argv.Length with
    | 0 | 1 -> printf "Please specify bot token as an first argument and api url as an second argument."
    | _ ->
        let update = update botContext
        startBot {
            defaultConfig with Token = argv.[0]
        } update None
        |> Async.RunSynchronously

    botContext.DataContext |> Data.dispose
    0