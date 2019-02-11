module NeuralBot.Bot

open Funogram.Api
open Funogram.Bot
open Funogram.Types
open Funogram.RequestsTypes

let execute (config: BotConfig) method =
    let r =
        method 
        |> api config
        |> Async.RunSynchronously
    ()