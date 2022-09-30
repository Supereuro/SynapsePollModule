import json
from twisted.web.resource import Resource
from twisted.web.server import Request
from twisted.internet import reactor
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.web.server import NOT_DONE_YET
from .database import *
import psycopg2


def checkAuth(request, connection, callback):
    agent = Agent(reactor)
    user = None
    authHeader = None
    try:
        user = request.args.get(b"user")[0].decode()
        authHeader = request.getHeader("Authorization")
    except Exception as error:
        None

    if authHeader is None or user is None:
        request.setResponseCode(401)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"errcode": "M_MISSING_TOKEN", "error": "Missing access token"}).encode())
        request.finish()
        return

    print("User Argument: .......... " + user)
    url = "http://localhost:8008/_matrix/client/v3/presence/{0}/status".format(user).encode("utf-8")
    d = agent.request(b"GET",
                      url,
                      Headers({"Content-Type": ["application/json"], "Authorization": [authHeader]}),
                      # request.requestHeaders,
                      None,
                      )

    def handle_response(response):
        if response.code != 200:
            request.setResponseCode(401)
            request.setHeader(b"Content-Type", b"application/json")
            request.write(json.dumps({"errcode": "M_MISSING_TOKEN", "error": "Missing access token"}).encode())
            request.finish()
        else:
            callback(request, connection)
        # b = readBody(response)
        # b.addCallback(cbBody)
        # request.setHeader(b"Content-Type", b"application/json")
        # request.write(json.dumps(response).encode())
        # finished = Deferred()
        # finished.addCallback(handle_result)
        # response.deliverBody(BeginningPrinter(finished, request))
        # return finished
        # request.write(result)
        # request.finish()
        # d = defer.succeed('{"das": "ist super"}')

        # return d

    d.addCallback(handle_response)


def postRequest(request, connection):
    newdata = request.content.getvalue()
    if newdata is None:
        request.setResponseCode(400)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
        request.finish()
    else:
        pollData = json.loads(newdata)
        result = database.create_poll(connection, pollData["poll"]["title"], pollData["poll"]["description"],
                                      pollData["poll"]["owner_user"],
                                      pollData["poll"]["room_id"], pollData["poll"]["options"])
        if result is not None:
            request.setResponseCode(500)
            request.write(json.dumps({"errcode": "M_UNKNOWN  ", "error": "Unknown Server error"}).encode())

        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"success": "ok "}).encode())
        request.finish()


def postVoteRequest(request, connection):
    newdata = request.content.getvalue()
    if newdata is None:
        request.setResponseCode(400)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
        request.finish()
    else:
        pollid = request.args.get(b"pollid")[0].decode()
        voteData = json.loads(newdata)
        result = database.add_poll_vote(connection, voteData["user_name"], voteData["option_id"], voteData["userchoice"], pollid)
        if result is not None:
            request.setResponseCode(500)
            request.write(json.dumps({"errcode": "M_UNKNOWN  ", "error": "Unknown Server error"}).encode())

        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"success": "ok "}).encode())
        request.finish()


def pollRequest(request, connection):
    result = database.get_polls(connection)
    jsonResult = '{ "polls": ' + json.dumps(result) + '}'
    request.write(jsonResult.encode())
    request.finish()


def singlePollRequest(request, connection):
    pollid = None
    try:
        pollid = request.args.get(b"pollid")[0].decode()

    except Exception as error:
        None

    if pollid is None:
        request.setResponseCode(400)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
        request.finish()
    else:
        result = database.get_poll(connection, pollid)
        jsonResult = json.dumps(result[0])
        request.write(jsonResult.encode())
        request.finish()


def deletePollRequest(request, connection):
    pollid = None
    try:
        pollid = request.args.get(b"pollid")[0].decode()

    except Exception as error:
        None

    if pollid is None:
        request.setResponseCode(400)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
        request.finish()
    else:
        try:
            result = database.delete_poll(connection, pollid)
            if result is not None:
                request.setResponseCode(500)
                request.write(json.dumps({"errcode": "M_UNKNOWN  ", "error": "Unknown Server error"}).encode())
            else:
                request.write(json.dumps({"success": "ok "}).encode())

            request.setHeader(b"Content-Type", b"application/json")
            request.finish()
        except Exception as error:
            request.setResponseCode(500)
            request.setHeader(b"Content-Type", b"application/json")
            request.write(json.dumps({"errcode": "M_UNKNOWN", "error": "Unknown Server error"}).encode())
            request.finish()


def optionsRequest(request, connection):
    pollid = None
    try:
        pollid = request.args.get(b"pollid")[0].decode()

    except Exception as error:
        None

    if pollid is None:
        request.setResponseCode(400)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
        request.finish()
    else:
        result = database.get_options(connection, pollid)
        jsonResult = '{ "options": ' + json.dumps(result) + '}'
        request.write(jsonResult.encode())
        request.finish()


def votesRequest(request, connection):
    pollid = None
    try:
        pollid = request.args.get(b"pollid")[0].decode()

    except Exception as error:
        None

    if pollid is None:
        request.setResponseCode(400)
        request.setHeader(b"Content-Type", b"application/json")
        request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
        request.finish()
    else:
        result = database.get_votes(connection, pollid)
        jsonResult = '{ "votes": ' + json.dumps(result) + '}'
        request.write(jsonResult.encode())
        request.finish()


def voteRequest(request, connection):
    request.setResponseCode(400)
    request.setHeader(b"Content-Type", b"application/json")
    request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
    request.finish()


class PollResource(Resource):

    def __init__(self, config):
        self.connection = psycopg2.connect(**config)
        super(PollResource, self).__init__()

    def render_GET(self, request: Request):
        path_resource = request.prepath[-1].decode('utf-8')
        if path_resource is not None:
            if path_resource == 'poll':
                request.setResponseCode(200)
                request.setHeader(b"Content-Type", b"application/json")
                request.write(json.dumps({"success": "Module installed"}).encode())
                request.finish()
            elif path_resource == 'getall':
                checkAuth(request, self.connection, pollRequest)
            elif path_resource == 'getpoll':
                checkAuth(request, self.connection, singlePollRequest)
            elif path_resource == 'getoptions':
                checkAuth(request, self.connection, optionsRequest)
            elif path_resource == 'getvotes':
                checkAuth(request, self.connection, votesRequest)
            elif path_resource == 'getvote':
                checkAuth(request, self.connection, voteRequest)
            else:
                request.setResponseCode(400)
                request.setHeader(b"Content-Type", b"application/json")
                request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
                request.finish()
        return NOT_DONE_YET

    def render_POST(self, request: Request):
        path_resource = request.prepath[-1].decode('utf-8')
        if path_resource is not None:
            if path_resource == 'createpoll':
                checkAuth(request, self.connection, postRequest)
            elif path_resource == 'createvote':
                checkAuth(request, self.connection, postVoteRequest)
            elif path_resource == 'deletepoll':
                checkAuth(request, self.connection, deletePollRequest)
            else:
                request.setResponseCode(400)
                request.setHeader(b"Content-Type", b"application/json")
                request.write(json.dumps({"errcode": "M_BAD_JSON ", "error": "Malformed JSON Data"}).encode())
                request.finish()

        return NOT_DONE_YET


class Poll:
    def __init__(self, config, api):
        self._api = api
        self._config = config
        self.connection = psycopg2.connect(**config)
        database.create_tables(self.connection)

        self._api.register_web_resource(
            path="/_synapse/client/poll",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/getall",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/getpoll",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/getoptions",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/getvotes",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/getvote",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/createpoll",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/deletepoll",
            resource=PollResource(config),
        )

        self._api.register_web_resource(
            path="/_synapse/client/poll/createvote",
            resource=PollResource(config),
        )

    @staticmethod
    def parse_config(config):
        return config
