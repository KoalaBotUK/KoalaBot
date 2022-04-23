from koala.decorators import make_registering_decorator


def rest_get(func):
    return func


def rest_post(func):
    return func


rest_get = make_registering_decorator(rest_get)
rest_post = make_registering_decorator(rest_post)
