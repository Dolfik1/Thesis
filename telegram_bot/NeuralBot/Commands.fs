module NeuralBot.Commands

open ExtCore.Control
open Funogram.Api
open Funogram.Bot
open Funogram.Types
open Funogram.RequestsTypes
open NeuralBot
open NeuralBot.Api
open NeuralBot.Types
    
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


let private makeTextRequest chatId text = 
    sendMessage chatId text |> Bot.cast
    
let private makeInlineRequest chatId text pairId =
    let markup = createInlineKeyboard pairId |> Markup.InlineKeyboardMarkup
    sendMessageMarkup chatId text markup
    
let onSay botContext (context: UpdateContext) =
    maybe {
        let! message = context.Update.Message
        let! text = message.Text
        let chatId = message.Chat.Id

        async {
            sendChatAction chatId ChatAction.Typing |> Bot.execute context
            // let! resp = makeApiRequestAsync botContext.ApiUrl text
            // sendMessage chatId resp.Answer |> Bot.execute context
            makeInlineRequest chatId "test" "1234" |> Bot.execute context
            ()
        } |> Async.Catch |> Async.Ignore |> Async.Start
    } |> ignore