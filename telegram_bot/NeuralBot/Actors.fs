module NeuralBot.Actors

open System.Collections.Generic
open Akkling
open Akkling.Persistence
open Funogram
open Funogram.Bot
open Funogram.Types
open Misc
open NeuralBot
open NeuralBot.Types

type ChatActorMessage = ProcessTextMessage of Message | Start | ToggleRating | ToggleDisabled
type ChatsActorMessage = Chat * ChatActorMessage
type StorageActorMessage<'a> = Execute of (Types.DataContext -> Async<'a>)

type ChatActorState = { Chat: Chat; RatingEnabled: bool; Disabled: bool }
let defaultChatActorState chat = { Chat = chat; RatingEnabled = false; Disabled = false }

let createStorageActor context = props(fun mailbox ->
    let rec loop () =
        actor {
            let! (action: StorageActorMessage<'a>) = mailbox.Receive()
            match action with
            | Execute fn -> fn context |> Async.StartAsTask |> ignore
            return! loop ()
        }
    loop ())

let createOutputGateActor botConfig = props(fun mailbox ->
    let rec loop () =
        actor {
           let! message = mailbox.Receive()
           async {
             let! result = message |> Api.apiUntyped botConfig
             match result with
             | Result.Ok x -> ()
             | Result.Error e -> printfn "Error: %s" e.Description
           } |> Async.Start
           return! loop () 
        }
    loop ())

let createChatActor outputGate storage initialState = propsPersist(fun mailbox ->
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
                                let from = m.From.Value
                                let response = "Hello, world"
                                let score = Data.createScore from.Id from.Username
                                                from.FirstName from.LastName text response None

                                storage <! Execute (Data.insertScore score)
                                // let! resp = NeuralBot.Api.makeApiRequestAsync "" text
                                // sendMessage chatId resp.Answer |> Bot.execute context
                                
                                let replyMessageId =
                                    if state.Chat.Type = "group" || state.Chat.Type = "supergroup"
                                    then Some m.MessageId else None 
                                
                                return
                                    if state.RatingEnabled then
                                        makeInlineRequestReply (ChatId.Int m.Chat.Id) response replyMessageId (score.Id |> string)
                                    else
                                        makeTextRequestReply m.Chat.Id response replyMessageId
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

let createChatsActor outputGate storage = propsPersist(fun mailbox ->
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
                    let actorRef = (defaultChatActorState chat |> createChatActor outputGate storage)
                                   |> spawnChildren mailbox (ActorsNames.chat id)
                    state.Add(chat.Id, actorRef)
                    actorRef
            actorRef <! message
            return! loop state
        }
    loop (new Dictionary<int64, IActorRef<ChatActorMessage>>()))

let createUpdatesActor (chatsActorRef: IActorRef<ChatsActorMessage>) outputGate storage = props(fun mailbox ->
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
            | UpdateType.CallbackQuery q ->
                let data = q.Data |> Option.defaultValue ""
                let blocks = data.Split("_")
                match blocks.Length with
                | 2 ->
                    let id = blocks.[0]
                    let score = blocks.[1] |> int
                    storage <! Execute (Data.updateScoreValue id score)
                    outputGate <! (Api.answerCallbackQueryBase (Some q.Id) (Some "Запомнил!") (Some false) None None |> castRequest)
                | _ -> ()
            | _ -> ()
            return! loop ()
        }
    loop ())