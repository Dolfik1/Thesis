module NeuralBot.Actors

open System.Collections.Generic
open Akkling
open Akkling.Persistence
open Funogram
open Funogram.RequestsTypes
open Funogram.Types
open Misc
open NeuralBot

type ChatActorMessage = ProcessMessage of Message
type ChatsActorMessage = Chat * ChatActorMessage

type ChatActorState = { Chat: Chat }
let defaultChatActorState chat = { Chat = chat }

let createOutputGate botConfig = props(fun mailbox ->
    let rec loop () =
        actor {
           let! message = mailbox.Receive()
           message |> Bot.execute botConfig
           return! loop () 
        }
    loop ())

let createChatActor outputGate initialState = propsPersist(fun mailbox ->
    let rec loop state =
        actor {
            let! action = mailbox.Receive()
            let stateChat =
                match action with
                | ChatActorMessage.ProcessMessage m ->
                    match m.Text with
                    | Some text ->
                        outputGate <! (Api.sendChatAction m.Chat.Id ChatAction.Typing |> castRequest)
                        async {
                            // let! resp = NeuralBot.Api.makeApiRequestAsync "" text
                            // sendMessage chatId resp.Answer |> Bot.execute context
                            // makeInlineRequest (m.Chat.Id) resp.Answer "1234"
                            return makeTextRequest m.Chat.Id "Hello, world"
                        } |!> outputGate
                    | None -> ()
                    m.Chat
            return! loop { state with ChatActorState.Chat = stateChat }
        }
    loop initialState)

let createChatsActor (outputGate: IActorRef<IBotRequest>) = propsPersist(fun mailbox ->
    let rec loop (state: Dictionary<int64, IActorRef<ChatActorMessage>>) =
        actor {
            let! (r: ChatsActorMessage) = mailbox.Receive()
            let chat, message = r
            
            let actorRef =
                let r, actorRef = state.TryGetValue chat.Id
                match r with
                | true -> actorRef
                | false ->
                    let id = chat.Id |> string
                    let actorRef = (defaultChatActorState chat |> createChatActor outputGate)
                                   |> spawnChildren mailbox (ActorsNames.chat id)
                    state.Add(chat.Id, actorRef)
                    actorRef
            actorRef <! message
            return! loop state
        }
    loop (new Dictionary<int64, IActorRef<ChatActorMessage>>()))

let createUpdatesActor (chatsActorRef: IActorRef<ChatsActorMessage>) = props(fun mailbox ->
    let rec loop () =
        actor {
            let! (update: Update) = mailbox.Receive()
            match update with
            | UpdateType.Message x ->
                chatsActorRef <! (x.Chat, ProcessMessage x)
            | _ -> ()
            return! loop ()
        }
    loop ())