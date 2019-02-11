module NeuralBot.Types

open LiteDB

type DataContext = {
    Db: LiteDatabase
}

type ReplyScore = VeryBad = 0 | Bad = 1 | Average = 2 | Good = 3 | VeryGood = 4

[<CLIMutable>]
type UserScore = {
    Id: ObjectId
    UserId: int64
    Username: string option
    FirstName: string
    LastName: string option
    UserMessage: string
    BotMessage: string
    Score: ReplyScore option
}

type BotContext = {
  DataContext: DataContext
  ApiUrl: string
}