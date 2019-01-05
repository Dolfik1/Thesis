module Program

open System
open System.Text
open Funogram.Api
open Funogram.Bot
open Funogram.Types
open FSharp.Data
open ExtCore.Control
open Funogram.RequestsTypes

[<Literal>]
let SendMessageRequestSample = """
{
  "message": "Hi!"
}
"""

[<Literal>]
let SendMessageResponseSample = """
{
  "message": "Hi!",
  "answer": "Hello!"
}
"""

type NeuralApiRequest = JsonProvider<SendMessageRequestSample>
type NeuralApiResponse = JsonProvider<SendMessageResponseSample>

let execute context method =
    method |> api context.Config 
    |> Async.Ignore 
    |> Async.Start

let cast f = upcast f : IRequestBase<'a>

let makeApiRequestAsync apiUrl (text: string) =
    async {
        let json = NeuralApiRequest.Root(text)
        let! resp = json.JsonValue.RequestAsync(apiUrl, "POST", Seq.empty)
        printfn "%s" text
        return
            match resp.Body with 
            | HttpResponseBody.Text x -> x |> NeuralApiResponse.Parse
            | HttpResponseBody.Binary x -> x |> Encoding.UTF8.GetString 
                                             |> NeuralApiResponse.Parse
    }

let onSay apiUrl context =
    maybe {
        let! message = context.Update.Message
        let! text = message.Text
        let chatId = message.Chat.Id
        
        async {
            sendChatAction context.Update.Message.Value.Chat.Id ChatAction.Typing |> execute context        
            let! resp = makeApiRequestAsync apiUrl text
            sendMessage chatId resp.Answer |> execute context
            ()   
        } |> Async.Catch |> Async.Ignore |> Async.Start
    } |> ignore
    
let update apiUrl context = 
    onSay apiUrl context |> ignore

[<EntryPoint>]
let main argv =
    match argv.Length with
    | 0 | 1 -> printf "Please specify bot token as an first argument and api url as an second argument."
    | _ ->
        let update = update argv.[1]
        startBot {
            defaultConfig with Token = argv.[0]
        } update None
        |> Async.RunSynchronously
    0