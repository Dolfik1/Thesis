module NeuralBot.Actors

open System.Collections.Generic
open Akkling
open Akkling.Persistence
open Funogram
open Funogram.Bot
open Funogram.RequestsTypes
open Funogram.Types
open Misc
open NeuralBot

type ChatActorMessage = ProcessTextMessage of Message | Start | ToggleRating | ToggleDisabled
type ChatsActorMessage = Chat * ChatActorMessage

type ChatActorState = { Chat: Chat; RatingEnabled: bool; Disabled: bool }
let defaultChatActorState chat = { Chat = chat; RatingEnabled = false; Disabled = false }

let createOutputGate botConfig = props(fun mailbox ->
    let rec loop () =
        actor {
           let! message = mailbox.Receive()
           message |> Bot.execute botConfig
           return! loop () 
        }
    loop ())

let createChatActor outputGate initialState = propsPersist(fun mailbox ->
    let rec loop (state: ChatActorState) =
        actor {
            let! action = mailbox.Receive()
            let state =
                match action with
                | ChatActorMessage.ProcessTextMessage m ->
                    match m.Text with
                    | Some text ->
                        if not state.Disabled then
                            outputGate <! (Api.sendChatAction m.Chat.Id ChatAction.Typing |> castRequest)
                            async {
                                // let! resp = NeuralBot.Api.makeApiRequestAsync "" text
                                // sendMessage chatId resp.Answer |> Bot.execute context
                                // makeInlineRequest (m.Chat.Id) resp.Answer "1234"
                                let text = "Hello, world"
                                return
                                    if state.RatingEnabled then
                                        makeInlineRequest m.Chat.Id text (m.MessageId |> string)
                                    else
                                        makeTextRequest m.Chat.Id text
                            } |!> outputGate
                        else ()
                    | None -> ()
                    { state with Chat = m.Chat }
                | Start ->
                    outputGate <! makeTextRequest state.Chat.Id "Привет! Я Тритт, отправь мне сообщение и я на него отвечу!"
                    state
                | ToggleRating ->
                    let text = if state.RatingEnabled then "Режим оценки отключён" else "Режим оценки включён"
                    outputGate <! makeTextRequest state.Chat.Id text
                    { state with RatingEnabled = not state.RatingEnabled }
                | ToggleDisabled ->
                    let text = if not state.Disabled then "Бот отключён" else "Бот включён"
                    outputGate <! makeTextRequest state.Chat.Id text
                    { state with Disabled = not state.Disabled }
                    
            return! loop state
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
            let! updateContext = mailbox.Receive()
            let update = updateContext.Update
            match update with
            | UpdateType.Message x ->
                let action a = (x.Chat, a)
                let r = processCommands updateContext [
                    cmd "/start" (fun _ -> chatsActorRef <! action Start)
                    cmd "/toggle_rating" (fun _ -> chatsActorRef <! action ToggleRating)
                    cmd "/toggle_bot" (fun _ -> chatsActorRef <! action ToggleDisabled)
                ]
                match r with
                | true -> chatsActorRef <! action (ProcessTextMessage x)
                | false -> ()
            | _ -> ()
            return! loop ()
        }
    loop ())