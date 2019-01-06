module NeuralBot.Bot

open Funogram.Api
open Funogram.Bot
open Funogram.Types
open Funogram.RequestsTypes

let execute (context: UpdateContext) method =
    let r =
        method 
        |> api context.Config
        |> Async.RunSynchronously
    printfn "%s" (r.ToString())
    ()
    
    
let cast f = upcast f : IRequestBase<'a>