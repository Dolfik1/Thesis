module NeuralBot.Data

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

let insertScore (score: UserScore) context =
    let collection = context.Db.GetCollection<UserScore>("scores")
    collection.Insert score |> ignore
    score

let updateScoreValue (id: string) (value: int) context =
    let collection = context.Db.GetCollection<UserScore>("scores")
    let oid = ObjectId(id)
    let score = collection.FindOne(fun x -> x.Id = oid)
    let value = LanguagePrimitives.EnumOfValue value
    let score = { score with Score = Some value }
    collection.Update score |> ignore
    score

