module Program

open Funogram.Bot

open NeuralBot
open NeuralBot.Types
open Akkling
    
[<EntryPoint>]
let main argv =
    let botContext = {
        DataContext = Data.init ()
        ApiUrl = argv.[1]
    }

    let system = System.create "neuralbot" (Configuration.load())
    match argv.Length with
    | 0 | 1 -> printf "Please specify bot token as an first argument and api url as an second argument."
    | _ ->
        let config = { defaultConfig with Token = argv.[0] }
    
        let storageActorRef = Actors.createStorageActor botContext.DataContext |> spawn system ActorsNames.storage 
        let outputGateActorRef = Actors.createOutputGateActor config |> spawn system ActorsNames.outputGate
        let chatsActorRef = Actors.createChatsActor outputGateActorRef storageActorRef |> spawn system ActorsNames.chats
        let updatesActor =
            Actors.createUpdatesActor chatsActorRef outputGateActorRef storageActorRef
            |> spawn system ActorsNames.updates

        let update context =
            updatesActor <! context
        
        startBot config update None
        |> Async.RunSynchronously

    botContext.DataContext |> Data.dispose
    system.Dispose()
    0