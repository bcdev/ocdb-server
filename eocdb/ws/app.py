# The MIT License (MIT)
# Copyright (c) 2018 by EUMETSAT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import argparse
import os
import sys

from tornado.web import Application, StaticFileHandler

# noinspection PyPep8Naming
from eocdb.ws import __version__ as VERSION
# noinspection PyPep8Naming
from eocdb.ws import __description__ as DESCRIPTION
from eocdb.ws.handlers import InfoHandler, MeasurementsQueryHandler
from eocdb.ws.webservice import url_pattern, WebService
from eocdb.ws.defaults import DEFAULT_PORT, DEFAULT_ADDRESS, DEFAULT_UPDATE_PERIOD, DEFAULT_CONFIG_FILE


def new_application():
    application = Application([
        ('/res/(.*)', StaticFileHandler, {'path': os.path.join(os.path.dirname(__file__), 'res')}),
        (url_pattern('/'), InfoHandler),
        (url_pattern('/eocdb/api/measurements'), MeasurementsQueryHandler),
        # (url_pattern('/xcube/tile/{{ds_name}}/{{var_name}}/{{z}}/{{x}}/{{y}}.png'), GetTileDatasetHandler),
        # (url_pattern('/xcube/tile/ne2/{{z}}/{{x}}/{{y}}.jpg'), GetTileNE2Handler),
        # (url_pattern('/xcube/tilegrid/{{ds_name}}/{{var_name}}/{{format_name}}'), GetTileGridDatasetHandler),
        # (url_pattern('/xcube/tilegrid/ne2/{{format_name}}'), GetTileGridNE2Handler),
        # (url_pattern('/xcube/datasets.json'), GetDatasetsJsonHandler),
        # (url_pattern('/xcube/variables/{{ds_name}}.json'), GetVariablesJsonHandler),
        # (url_pattern('/xcube/coords/{{ds_name}}/{{dim_name}}.json'), GetCoordinatesJsonHandler),
        # (url_pattern('/xcube/colorbars.json'), GetColorBarsHandler, dict(format_name='text/json')),
        # (url_pattern('/xcube/colorbars.html'), GetColorBarsHandler, dict(format_name='text/html')),
    ])
    return application


def new_web_service(args=None) -> WebService:
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--version', '-V', action='version', version=VERSION)
    parser.add_argument('--address', '-a', dest='address', metavar='ADDRESS',
                        help='Server address. '
                             f'Defaults to {DEFAULT_ADDRESS!r}.',
                        default=DEFAULT_ADDRESS)
    parser.add_argument('--port', '-p', dest='port', metavar='PORT', type=int,
                        default=DEFAULT_PORT,
                        help='Port number where the web service will listen on. '
                             f'Defaults to {DEFAULT_PORT}.')
    parser.add_argument('--update', '-u', dest='update_period', metavar='UPDATE_PERIOD', type=float,
                        default=DEFAULT_UPDATE_PERIOD,
                        help='Check for configuration updates after given period in seconds. '
                             'Zero or a negative value will disable configuration update checks. '
                             f'Defaults to {DEFAULT_UPDATE_PERIOD!r}.')
    parser.add_argument('--config', '-c', dest='config_file', metavar='CONFIG_FILE', default=None,
                        help='Configuration file. '
                             f'Defaults to {DEFAULT_CONFIG_FILE!r}.')
    parser.add_argument('--verbose', '-v', dest='verbose', action='store_true',
                        help="if given, logging will be delegated to the console (stderr)")

    args_obj = parser.parse_args(args)

    return WebService(new_application(),
                      log_to_stderr=args_obj.verbose,
                      port=args_obj.port,
                      address=args_obj.address,
                      config_file=args_obj.config_file,
                      update_period=args_obj.update_period)


def main(args=None) -> int:
    try:
        print(f'{DESCRIPTION}, version {VERSION}')
        service = new_web_service(args)
        service.start()
        return 0
    except Exception as e:
        print('error: %s' % e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
