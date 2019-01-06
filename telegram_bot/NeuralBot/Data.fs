module NeuralBot.Data

open ExtCore
open LiteDB
open NeuralBot.Types

let createScore userId username firstName lastName userMessage botMessage score =
    {
      Id = ObjectId.NewObjectId()
      UserId = userId
      Username = username
      FirstName = firstName
      LastName = lastName
      UserMessage = userMessage
      BotMessage = botMessage
      Score = score 
    }

let init () =
    {
      Db = new LiteDatabase("lite.db")
    }

let dispose context =
    context.Db.Dispose()

let insertScore context (score: UserScore) =
    async {
        let collection = context.Db.GetCollection<UserScore>("scores")
        collection.Insert score |> ignore
    }
