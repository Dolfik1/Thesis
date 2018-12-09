import falcon
import argparse
import json
from wsgiref import simple_server
from chatbot import Chatbot, add_args


class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')


class JSONTranslator(object):
    # NOTE: Starting with Falcon 1.3, you can simply
    # use req.media and resp.media for this instead.

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        if 'result' not in resp.context:
            return

        resp.body = json.dumps(resp.context['result'])


def max_body(limit):
    def hook(req, resp, resource, params):
        length = req.content_length
        if length is not None and length > limit:
            msg = ('The size of the request is too large. The body must not '
                   'exceed ' + str(limit) + ' bytes in length.')

            raise falcon.HTTPRequestEntityTooLarge(
                'Request body is too large', msg)

    return hook


class SendMessageResource(object):
    def __init__(self, chatbot):
        self.chatbot = chatbot

    @falcon.before(max_body(1024))
    def on_post(self, req, resp):
        try:
            message = req.context['doc']['message']
        except KeyError:
            raise falcon.HTTPBadRequest(
                'Missing key',
                '"message" must be submitted in the request body.')

        answer = self.chatbot.say(message)
        resp.status = falcon.HTTP_200

        resp.context['result'] = {
            "message": message,
            "answer": answer
        }


def main():
    parser = argparse.ArgumentParser()
    add_args(parser)
    args = parser.parse_args()
    chatbot = Chatbot(save_dir=args.save_dir, n=args.n, prime=args.prime,
                      beam_width=args.beam_width,
                      temperature=args.temperature, topn=args.topn,
                      relevance=args.relevance)
    chatbot.start()
    app = falcon.API(
        middleware=[
            RequireJSON(),
            JSONTranslator()
        ])
    app.add_route('/send/message', SendMessageResource(chatbot))
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()
    chatbot.stop()


if __name__ == '__main__':
    main()
