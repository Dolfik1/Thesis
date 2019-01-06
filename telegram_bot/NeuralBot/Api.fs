module NeuralBot.Api

open System.Text
open FSharp.Data

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