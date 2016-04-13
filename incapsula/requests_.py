import random
import time

from BeautifulSoup import BeautifulSoup

from methods import *

logger = logging.getLogger('incapsula')


def _load_encapsula_resource(sess, response):
    timing = []
    start = now_in_seconds()
    timing.append('s:{}'.format(now_in_seconds() - start))

    code = get_obfuscated_code(response.content)
    parsed = parse_obfuscated_code(code)
    resource1, resource2 = get_resources(parsed, response.url)[1:]
    sess.get(resource1)

    timing.append('c:{}'.format(now_in_seconds() - start))
    time.sleep(0.02)  # simulate page refresh time
    timing.append('r:{}'.format(now_in_seconds() - start))
    sess.get(resource2 + urllib.quote('complete ({})'.format(",".join(timing))))


def crack(sess, response):
    """
    Pass a response object to this method to retry the url after the incapsula cookies have been set.

    Usage:
        >>> import incapsula
        >>> import requests
        >>> session = requests.Session()
        >>> response = incapsula.crack(session, session.get('http://www.incapsula-blocked-resource.com'))
        >>> print response.content  # response content should be incapsula free.
    :param sess: A requests.Session object.
    :param response: The response object from an incapsula blocked website.
    :return: Original response if not blocked, or new response after unblocked
    :type sess: requests.Session
    :type response: requests.Response
    :rtype: requests.Response
    """
    soup = BeautifulSoup(response.content)
    meta = soup.find('meta', {'name': 'robots'})
    if not meta:  # if the page is not blocked, then just return the original request.
        return response
    set_incap_cookie(sess, response)
    # populate first round cookies
    scheme, host = urlparse.urlsplit(response.url)[:2]
    sess.get('{scheme}://{host}/_Incapsula_Resource?SWKMTFSR=1&e={rdm}'.format(scheme=scheme, host=host, rdm=random.random))
    # populate second round cookies
    _load_encapsula_resource(sess, response)
    return sess.get(response.url)


def _get_session_cookies(sess):
    cookies_ = []
    for cookie_key, cookie_value in sess.cookies.items():
        if 'incap_ses_' in cookie_key:
            cookies_.append(cookie_value)
    return cookies_


def set_incap_cookie(sess, response):
    logger.debug('loading encapsula extensions and plugins')
    extensions = load_plugin_extensions(navigator['plugins'])
    extensions.append(load_plugin(navigator['plugins']))
    extensions.extend(load_config())
    cookies = _get_session_cookies(sess)
    digests = []
    for cookie in cookies:
        digests.append(simple_digest(",".join(extensions) + cookie))
    res = ",".join(extensions) + ",digest=" + ",".join(str(digests))
    cookie = create_cookie("___utmvc", res, 20, response.url)
    sess.cookies.set(**cookie)
