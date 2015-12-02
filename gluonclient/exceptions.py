# Copyright 2011 VMware, Inc
# Copyright 2015 Cisco Systems, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Based on a file from neutronclient.

# TODO not got here yet, so:
#from gluonclient.i18n import _
def _(x): return x

"""
Gluon base exception handling.

Exceptions are classified into three categories:
* Exceptions corresponding to exceptions from gluon server:
  This type of exceptions should inherit one of exceptions
  in HTTP_EXCEPTION_MAP.
* Exceptions from client library:
  This type of exceptions should inherit GluonClientException.
* Exceptions from CLI code:
  This type of exceptions should inherit GluonCLIError.
"""


class GluonException(Exception):
    """Base Gluon Exception.

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = _("An unknown exception occurred.")

    def __init__(self, message=None, **kwargs):
        if message:
            self.message = message
        try:
            self._error_string = self.message % kwargs
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message

    def __str__(self):
        return self._error_string


class GluonClientException(GluonException):
    """Base exception which exceptions from Gluon are mapped into.

    NOTE: on the client side, we use different exception types in order
    to allow client library users to handle server exceptions in try...except
    blocks. The actual error message is the one generated on the server side.
    """

    status_code = 0

    def __init__(self, message=None, **kwargs):
        if 'status_code' in kwargs:
            self.status_code = kwargs['status_code']
        super(GluonClientException, self).__init__(message, **kwargs)


# Base exceptions from Gluon

class BadRequest(GluonClientException):
    status_code = 400


class Unauthorized(GluonClientException):
    status_code = 401
    message = _("Unauthorized: bad credentials.")


class Forbidden(GluonClientException):
    status_code = 403
    message = _("Forbidden: your credentials don't give you access to this "
                "resource.")


class NotFound(GluonClientException):
    status_code = 404


class Conflict(GluonClientException):
    status_code = 409


class InternalServerError(GluonClientException):
    status_code = 500


class ServiceUnavailable(GluonClientException):
    status_code = 503


HTTP_EXCEPTION_MAP = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    409: Conflict,
    500: InternalServerError,
    503: ServiceUnavailable,
}


# Exceptions mapped to Gluon server exceptions
# These are defined if a user of client library needs specific exception.
# Exception name should be <Gluon Exception Name> + 'Client'
# e.g., NetworkNotFound -> NetworkNotFoundClient

class PortNotFoundClient(NotFound):
    pass


class StateInvalidClient(BadRequest):
    pass


class PortInUseClient(Conflict):
    pass

# Exceptions from client library

class NoAuthURLProvided(Unauthorized):
    message = _("auth_url was not provided to the Gluon client")


class EndpointNotFound(GluonClientException):
    message = _("Could not find Service or Region in Service Catalog.")


class EndpointTypeNotFound(GluonClientException):
    message = _("Could not find endpoint type %(type_)s in Service Catalog.")


class AmbiguousEndpoints(GluonClientException):
    message = _("Found more than one matching endpoint in Service Catalog: "
                "%(matching_endpoints)")


class RequestURITooLong(GluonClientException):
    """Raised when a request fails with HTTP error 414."""

    def __init__(self, **kwargs):
        self.excess = kwargs.get('excess', 0)
        super(RequestURITooLong, self).__init__(**kwargs)


class ConnectionFailed(GluonClientException):
    message = _("Connection to gluon failed: %(reason)s")


class SslCertificateValidationError(GluonClientException):
    message = _("SSL certificate validation has failed: %(reason)s")


class MalformedResponseBody(GluonClientException):
    message = _("Malformed response body: %(reason)s")


class InvalidContentType(GluonClientException):
    message = _("Invalid content type %(content_type)s.")


# Command line exceptions

class GluonCLIError(GluonException):
    """Exception raised when command line parsing fails."""
    pass


class CommandError(GluonCLIError):
    pass


class UnsupportedVersion(GluonCLIError):
    """Indicates that the user is trying to use an unsupported version of
    the API.
    """
    pass
