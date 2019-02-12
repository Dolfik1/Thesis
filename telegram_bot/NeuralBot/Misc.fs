module NeuralBot.Misc

open System
open Akka.Actor
open Akkling
open Funogram
open Funogram.Types

    
let castRequest f = upcast f : RequestsTypes.IBotRequest

let spawnChildren parent name props =
    let strategy =
        fun (exc: Exception) ->
            Directive.Resume
        |> Strategy.OneForOne
        |> Some
    // TODO STRATEGY
    spawn parent name props

let pipeTo receipient computation =
    Async.StartAsTask(computation).PipeTo(receipient)

let private createInlineButton text data =
    {
      Text = text
      CallbackData = Some(data)
      Url = None
      CallbackGame = None
      SwitchInlineQuery = None
      SwitchInlineQueryCurrentChat = None
    }
    
let private createInlineKeyboard pairId =
    let data = sprintf "%s_%i" pairId
    let buttons = [[
         data 0 |> createInlineButton "🤯Very Bad"
         data 1 |> createInlineButton "😑Bad"
       ] |> List.toSeq;
       [
         data 2 |> createInlineButton "😐Average"
       ] |> List.toSeq;
       [
         data 3 |> createInlineButton "🙂Good"
         data 4 |> createInlineButton "😀Very Good"
       ] |> List.toSeq ] |> List.toSeq
    { InlineKeyboard = buttons }

let makeTextRequest chatId text = 
    Api.sendMessage chatId text |> castRequest

let makeTextRequestReply chatId text replyMessageId = 
    Api.sendMessageReply chatId text replyMessageId |> castRequest
    
let makeInlineRequestReply chatId text replyMessageId pairId =
    let markup = createInlineKeyboard pairId |> Markup.InlineKeyboardMarkup
    Api.sendMessageBase chatId text None None None replyMessageId (Some markup) |> castRequest
    