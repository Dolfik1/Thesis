module NeuralBot.Types

open LiteDB

type DataContext = {
    Db: LiteDatabase
}

type ReplyScore = VeryBad = 0 | Bad = 1 | Average = 2 | Good = 3 | VeryGood = 4

type UserScore = {
    Id: ObjectId
    UserId: int64
    Username: string
    FirstName: string
    LastName: string
    UserMessage: string
    BotMessage: string
    Score: ReplyScore
}

type BotContext = {
  DataContext: DataContext
  ApiUrl: string
}